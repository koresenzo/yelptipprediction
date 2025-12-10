import psycopg2
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import train_test_split

def train_linear(X_train, X_test, y_train, y_test):
    print("\n Linear Regression ")
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    predictions = model.predict(X_test)
    
    errors = [abs(predictions[i] - y_test.iloc[i]) for i in range(len(predictions))]
    avg_error = sum(errors) / len(errors)
    
    print(f"Average error: {avg_error:.2f}%")
    
    return model

def train_logistic(X_train, X_test, y_train, y_test):
    print("\n Logistic Regression ")
    
    def to_category(tip):
        if tip < 16:
            return 'low'
        elif tip <= 22:
            return 'medium'
        else:
            return 'high'
    
    y_train_cat = [to_category(t) for t in y_train]
    y_test_cat = [to_category(t) for t in y_test]
    
    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train_cat)
    
    predictions = model.predict(X_test)
    
    correct = sum([1 for i in range(len(predictions)) if predictions[i] == y_test_cat[i]])
    accuracy = correct / len(predictions)
    
    print(f"Accuracy: {accuracy:.1%}")
    
    return model, to_category

def show_top():
    conn = connect()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT r.name, r.city, r.stars, t.predicted_tip_pct
        FROM restaurants r
        JOIN tip_predictions t ON r.restaurant_id = t.restaurant_id
        WHERE t.tip_category = 'high'
        ORDER BY t.predicted_tip_pct DESC
        LIMIT 10
    """)
    
    print("\nTop 10 restaurants for tips:")
    for name, city, stars, tip in cur.fetchall():
        print(f"  {name} ({city}) - {stars}stars - {tip:.1f}%")
    
    cur.close()
    conn.close()

def get_data():
    conn = connect()
    
    query = """
        SELECT 
            r.restaurant_id,
            r.stars,
            r.price_range,
            f.avg_sentiment,
            f.positive_reviews,
            f.service_mentions,
            f.avg_price
        FROM restaurants r
        JOIN restaurant_features f ON r.restaurant_id = f.restaurant_id
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    df['price_num'] = df['price_range'].map({
        '$': 1,
        '$$': 2,
        '$$$': 3,
        '$$$$': 4
    })

    df['price_num'] = df['price_num'].fillna(2)
    
    return df

def make_tips(df):
    tips = []

    for i in range(len(df)):
        row = df.iloc[i]

        
        tip = 15.0  
        
        tip += row['avg_sentiment'] * 5.0   
        
        tip += (row['stars'] - 3.0) * 1.2    

        
        service = min(row['service_mentions'], 6)
        tip += service * 0.3                

        
        avg_price = row['avg_price'] if row['avg_price'] else 15
        if avg_price > 25:
            tip += 1.0
        if avg_price < 10:
            tip -= 1.0

        
        tip += np.random.normal(0, 2.0)  

       
        tip = max(8, min(tip, 30))

        tips.append(tip)

    return tips

def save_predictions(df, linear_model, logistic_model, cat_func):
    conn = connect()
    cur = conn.cursor()
    
    features = ['stars', 'price_num', 'avg_sentiment', 'service_mentions', 'avg_price']
    X = df[features]
    
    tip_pcts = linear_model.predict(X)
    tip_cats = logistic_model.predict(X)
    
    print("\nSaving predictions...")
    
    for i in range(len(df)):
        rest_id = df.iloc[i]['restaurant_id']
        cur.execute("""
            INSERT INTO tip_predictions 
                (restaurant_id, predicted_tip_pct, tip_category)
            VALUES (%s, %s, %s)
            ON CONFLICT (restaurant_id) DO UPDATE
            SET predicted_tip_pct = EXCLUDED.predicted_tip_pct,
                tip_category       = EXCLUDED.tip_category
        """, (rest_id, float(tip_pcts[i]), tip_cats[i]))
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"Saved {len(df)} predictions")

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
    print("Tip Prediction Model")
    print("\n")
    
    print("\nLoading data...")
    df = get_data()
    print(f"Loaded {len(df)} restaurants")
    
    df['tip'] = make_tips(df)
    
    features = ['stars', 'price_num', 'avg_sentiment', 'service_mentions', 'avg_price']
    X = df[features]
    y = df['tip']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    linear = train_linear(X_train, X_test, y_train, y_test)
    logistic, cat_func = train_logistic(X_train, X_test, y_train, y_test)
    
    save_predictions(df, linear, logistic, cat_func)
    
    show_top()
    
    print("\nPrediction Done")



