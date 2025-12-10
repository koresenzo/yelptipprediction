import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def plot_tip_distribution():
    conn = connect()
    
    query = """
        SELECT predicted_tip_pct, tip_category
        FROM tip_predictions
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    plt.hist(df['predicted_tip_pct'], bins=30, color='skyblue', edgecolor='black')
    plt.xlabel('Predicted Tip %')
    plt.ylabel('Number of Restaurants')
    plt.title('Distribution of Predicted Tips')
    plt.axvline(df['predicted_tip_pct'].mean(), color='red', linestyle='--', 
                label=f'Mean: {df["predicted_tip_pct"].mean():.2f}%')
    plt.legend()
    
    plt.subplot(1, 2, 2)
    category_counts = df['tip_category'].value_counts()
    colors = {'low': '#ff9999', 'medium': '#ffcc99', 'high': '#99ff99'}
    plt.bar(category_counts.index, category_counts.values, 
            color=[colors[cat] for cat in category_counts.index])
    plt.xlabel('Tip Category')
    plt.ylabel('Number of Restaurants')
    plt.title('Restaurants by Tip Category')
    
    plt.tight_layout()
    plt.savefig('tip_distribution.png', dpi=300, bbox_inches='tight')
    print("Saved: tip_distribution.png")
    plt.close()

def plot_sentiment_vs_tips():
    conn = connect()
    
    query = """
        SELECT 
            f.avg_sentiment,
            t.predicted_tip_pct,
            t.tip_category
        FROM restaurant_features f
        JOIN tip_predictions t ON f.restaurant_id = t.restaurant_id
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    plt.figure(figsize=(10, 6))
    
    colors = {'low': 'red', 'medium': 'orange', 'high': 'green'}
    for category in ['low', 'medium', 'high']:
        data = df[df['tip_category'] == category]
        plt.scatter(data['avg_sentiment'], data['predicted_tip_pct'], 
                   alpha=0.5, label=category.capitalize(), c=colors[category], s=50)
    
    plt.xlabel('Average Sentiment Score')
    plt.ylabel('Predicted Tip %')
    plt.title('Relationship Between Sentiment and Tips')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.savefig('sentiment_vs_tips.png', dpi=300, bbox_inches='tight')
    print("Saved: sentiment_vs_tips.png")
    plt.close()

def plot_service_impact():
    conn = connect()
    
    query = """
        SELECT 
            f.service_mentions,
            t.predicted_tip_pct
        FROM restaurant_features f
        JOIN tip_predictions t ON f.restaurant_id = t.restaurant_id
        WHERE f.service_mentions <= 20
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    plt.figure(figsize=(10, 6))
    
    grouped = df.groupby('service_mentions')['predicted_tip_pct'].mean()
    plt.bar(grouped.index, grouped.values, color='steelblue', edgecolor='black')
    plt.xlabel('Number of Service Mentions')
    plt.ylabel('Average Predicted Tip %')
    plt.title('Impact of Service Mentions on Tips')
    plt.grid(True, alpha=0.3, axis='y')
    
    plt.savefig('service_impact.png', dpi=300, bbox_inches='tight')
    print("Saved: service_impact.png")
    plt.close()

def plot_top_restaurants():
    conn = connect()
    
    query = """
        SELECT 
            r.name,
            t.predicted_tip_pct
        FROM restaurants r
        JOIN tip_predictions t ON r.restaurant_id = t.restaurant_id
        WHERE t.tip_category = 'high'
        ORDER BY t.predicted_tip_pct DESC
        LIMIT 10
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    plt.figure(figsize=(10, 6))
    
    plt.barh(df['name'], df['predicted_tip_pct'], color='lightgreen', edgecolor='black')
    plt.xlabel('Predicted Tip %')
    plt.ylabel('Restaurant')
    plt.title('Top 10 Restaurants for Tips')
    plt.gca().invert_yaxis()
    
    for i, v in enumerate(df['predicted_tip_pct']):
        plt.text(v + 0.1, i, f'{v:.1f}%', va='center')
    
    plt.tight_layout()
    plt.savefig('top_restaurants.png', dpi=300, bbox_inches='tight')
    print("Saved: top_restaurants.png")
    plt.close()

def generate_summary_stats():
    conn = connect()
    cur = conn.cursor()
    
    print("\n")
    print("Statistics Summary:")
    print("\n")
    
    cur.execute("SELECT COUNT(*) FROM restaurants")
    print(f"\nTotal Restaurants: {cur.fetchone()[0]:,}")
    
    cur.execute("SELECT COUNT(*) FROM reviews")
    print(f"Total Reviews: {cur.fetchone()[0]:,}")
    
    cur.execute("""
        SELECT 
            AVG(predicted_tip_pct) as avg_tip,
            MIN(predicted_tip_pct) as min_tip,
            MAX(predicted_tip_pct) as max_tip
        FROM tip_predictions
    """)
    avg, min_tip, max_tip = cur.fetchone()
    print(f"\nAverage Predicted Tip: {avg:.2f}%")
    print(f"Min Predicted Tip: {min_tip:.2f}%")
    print(f"Max Predicted Tip: {max_tip:.2f}%")
    
    cur.execute("""
        SELECT tip_category, COUNT(*) 
        FROM tip_predictions 
        GROUP BY tip_category
    """)
    print(f"\nRestaurants by Category:")
    for category, count in cur.fetchall():
        print(f" {category.capitalize()}: {count:,}")
    
    cur.execute("""
        SELECT 
            AVG(f.avg_sentiment) as avg_sentiment,
            AVG(f.service_mentions) as avg_service
        FROM restaurant_features f
    """)
    avg_sent, avg_serv = cur.fetchone()
    print(f"\nAverage Sentiment Score: {avg_sent:.3f}")
    print(f"Average Service Mentions: {avg_serv:.1f}")
    
    cur.close()
    conn.close()

def connect():
    conn = psycopg2.connect(
        dbname="restaurant_tips",
        user="postgres",
        password="your_password",
        host="localhost"
    )
    return conn

if __name__ == "__main__":
    print("\n")
    print("Generating Visuals")
    print("\n")
    
    plot_tip_distribution()
    plot_sentiment_vs_tips()
    plot_service_impact()
    plot_top_restaurants()
    generate_summary_stats()
    
    print("\n")
    print("All Visuals Generated")
    print("\n")


