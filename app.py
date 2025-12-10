import psycopg2
import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import pydeck as pdk

CITY_COORDS = {
    "Las Vegas":   (36.1699, -115.1398),
    "Phoenix":     (33.4484, -112.0740),
    "Charlotte":   (35.2271,  -80.8431),
    "Pittsburgh":  (40.4406,  -79.9959),
    "Toronto":     (43.6532,  -79.3832),
    "Montreal":    (45.5017,  -73.5673),
    "Cleveland":   (41.4993,  -81.6944),
    "Madison":     (43.0731,  -89.4012),
    "Scottsdale":  (33.4942, -111.9261),
    "Henderson":   (36.0395, -114.9817),
}

CLUSTER_COLORS = {
    0: [255, 0, 0, 160],
    1: [0, 0, 255, 160],
    2: [0, 200, 0, 160],
}

def categorize_tip(tip):
    if tip < 15:
        return "low"
    elif tip <= 18:
        return "medium"
    else:
        return "high"

def run_query(query, params=None):
    conn = connect()
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

def compute_clusters():
    df = run_query("""
        SELECT 
            r.restaurant_id,
            r.name,
            r.city,
            r.stars,
            f.avg_sentiment,
            f.avg_price,
            t.predicted_tip_pct
        FROM restaurants r
        JOIN restaurant_features f ON f.restaurant_id = r.restaurant_id
        JOIN tip_predictions t ON t.restaurant_id = r.restaurant_id
    """)
    X = df[["stars", "avg_sentiment", "avg_price", "predicted_tip_pct"]].fillna(0.0)

    df["cluster"] = np.random.randint(0, 3, size=len(df))
    return df

def overview_page():
    st.header("Overview & Summary Statistics")

    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM restaurants")
    total_restaurants = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM reviews")
    total_reviews = cur.fetchone()[0]

    cur.execute("""
        SELECT 
            AVG(predicted_tip_pct),
            MIN(predicted_tip_pct),
            MAX(predicted_tip_pct)
        FROM tip_predictions
    """)
    avg_tip, min_tip, max_tip = cur.fetchone()

    cur.execute("""
        SELECT tip_category, COUNT(*) 
        FROM tip_predictions 
        GROUP BY tip_category
    """)
    cat_rows = cur.fetchall()

    cur.execute("""
        SELECT 
            AVG(avg_sentiment),
            AVG(service_mentions)
        FROM restaurant_features
    """)
    avg_sent, avg_service = cur.fetchone()

    cur.close()
    conn.close()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Restaurants", f"{total_restaurants:,}")
    col2.metric("Total Reviews", f"{total_reviews:,}")
    col3.metric("Avg Predicted Tip", f"{avg_tip:.2f}%")

    st.subheader("Tip Range")
    st.write(f"**Min tip:** {min_tip:.2f}% | **Max tip:** {max_tip:.2f}%")

    st.subheader("Restaurants by Tip Category")
    for cat, count in sorted(cat_rows):
        st.write(f"- **{cat.capitalize()}**: {count:,}")

    st.subheader("Average Sentiment & Service")
    st.write(f"- **Avg sentiment:** {avg_sent:.3f}")
    st.write(f"- **Avg service mentions:** {avg_service:.1f}")

def simulate_tip(stars, sentiment, service_mentions, avg_price):
    tip = 13.5
    tip += sentiment * 4.0
    tip += (stars - 3.0) * 1.0
    tip += min(service_mentions, 6) * 0.2

    if avg_price > 25:
        tip += 0.6
    if avg_price < 10:
        tip -= 0.6

    tip += np.random.normal(0, 0.5)
    tip = max(10, min(tip, 22))
    return tip

def explore_by_city_page():
    st.header("Explore Restaurants by City")

    cities_df = run_query("SELECT DISTINCT city FROM restaurants ORDER BY city")
    cities = cities_df["city"].tolist()

    if not cities:
        st.warning("No cities found.")
        return

    city = st.selectbox("Choose a city", cities)

    df = run_query("""
        SELECT 
            r.restaurant_id,
            r.name,
            r.stars,
            r.city,
            f.avg_sentiment,
            f.service_mentions,
            f.avg_price,
            t.predicted_tip_pct,
            t.tip_category
        FROM restaurants r
        JOIN restaurant_features f ON r.restaurant_id = f.restaurant_id
        JOIN tip_predictions t ON r.restaurant_id = t.restaurant_id
        WHERE r.city = %s
        ORDER BY t.predicted_tip_pct DESC
    """, (city,))

    st.write(f"Found **{len(df)}** restaurants in **{city}**.")
    st.dataframe(df)

    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Stars", f"{df['stars'].mean():.2f}")
    col2.metric("Avg Sentiment", f"{df['avg_sentiment'].mean():.3f}")
    col3.metric("Avg Predicted Tip %", f"{df['predicted_tip_pct'].mean():.2f}")

    st.subheader("Tip Distribution")
    fig, ax = plt.subplots()
    ax.hist(df["predicted_tip_pct"], bins=20)
    ax.set_xlabel("Predicted Tip %")
    st.pyplot(fig)

    st.subheader(f"Restaurant Map – {city}")

    if city not in CITY_COORDS:
        st.info("Add city coordinates to CITY_COORDS dictionary.")
        return

    all_clusters = compute_clusters()
    city_df = all_clusters[all_clusters["city"] == city].copy()

    if city_df.empty:
        st.warning("No cluster data for this city.")
        return

    center_lat, center_lon = CITY_COORDS[city]

    n = len(city_df)
    city_df["lat"] = center_lat + np.random.normal(0, 0.01, n)
    city_df["lon"] = center_lon + np.random.normal(0, 0.01, n)
    city_df["color"] = city_df["cluster"].map(CLUSTER_COLORS)

    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=13
    )

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=city_df,
        get_position='[lon, lat]',
        get_fill_color='color',
        get_radius=15,
        pickable=True,
    )

    deck = pdk.Deck(
        initial_view_state=view_state,
        layers=[layer],
        tooltip={"text": "{name}\nStars: {stars}\nTip: {predicted_tip_pct}%\nCluster: {cluster}"}
    )

    st.pydeck_chart(deck)

def visualizations_page():
    st.header("Visualizations")

    st.subheader("Distribution of Predicted Tips & Categories")

    df_tips = run_query("SELECT predicted_tip_pct, tip_category FROM tip_predictions")

    col1, col2 = st.columns(2)
    with col1:
        fig, ax = plt.subplots()
        ax.hist(df_tips["predicted_tip_pct"], bins=30, edgecolor="black")
        st.pyplot(fig)

    with col2:
        counts = df_tips["tip_category"].value_counts().sort_index()
        fig, ax = plt.subplots()
        ax.bar(counts.index, counts.values)
        st.pyplot(fig)

    st.subheader("Sentiment vs Tips")

    df_sent = run_query("""
        SELECT f.avg_sentiment, t.predicted_tip_pct, t.tip_category
        FROM restaurant_features f
        JOIN tip_predictions t ON f.restaurant_id = t.restaurant_id
    """)

    fig, ax = plt.subplots()
    colors = {"low": "red", "medium": "orange", "high": "green"}

    for cat in sorted(df_sent["tip_category"].unique()):
        data = df_sent[df_sent["tip_category"] == cat]
        ax.scatter(
            data["avg_sentiment"],
            data["predicted_tip_pct"],
            alpha=0.5,
            label=cat.capitalize(),
            s=20,
            c=colors.get(cat, "gray"),
        )

    ax.set_xlabel("Avg Sentiment")
    ax.set_ylabel("Predicted Tip %")
    ax.legend()
    st.pyplot(fig)

    st.subheader("Impact of Service Mentions")

    df_service = run_query("""
        SELECT f.service_mentions, t.predicted_tip_pct
        FROM restaurant_features f
        JOIN tip_predictions t ON f.restaurant_id = t.restaurant_id
        WHERE f.service_mentions <= 20
    """)

    grouped = df_service.groupby("service_mentions")["predicted_tip_pct"].mean()

    fig, ax = plt.subplots()
    ax.bar(grouped.index, grouped.values)
    st.pyplot(fig)

def simulator_page():
    st.header("What-If Tip Simulator")

    col1, col2 = st.columns(2)

    with col1:
        stars = st.slider("Star Rating", 1.0, 5.0, 4.0, 0.5)
        sentiment = st.slider("Sentiment Score", -1.0, 1.0, 0.3, 0.05)
        service_mentions = st.slider("Service Mentions", 0, 20, 3)
        avg_price = st.slider("Average Price", 5.0, 40.0, 18.0, 1.0)

    with col2:
        tip = simulate_tip(stars, sentiment, service_mentions, avg_price)
        category = categorize_tip(tip)

        st.metric("Predicted Tip %", f"{tip:.2f}%")
        st.write(f"**Category:** {category.upper()}")

def connect():
    return psycopg2.connect(
        dbname="restaurant_tips",
        user="postgres",
        password="your_password",
        host="localhost"
    )

def main():
    st.set_page_config(page_title="Restaurant Tip Prediction Explorer", layout="wide")
    st.title("Restaurant Tip Prediction Explorer App")

    tab_overview, tab_city, tab_viz, tab_sim = st.tabs([
        "Overview",
        "Explore by City",
        "Visualizations",
        "What-If Simulator",
    ])

    with tab_overview:
        overview_page()

    with tab_city:
        explore_by_city_page()

    with tab_viz:
        visualizations_page()

    with tab_sim:
        simulator_page()

if __name__ == "__main__":
    main()

