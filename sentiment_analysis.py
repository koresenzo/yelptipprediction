import psycopg2
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

vader = SentimentIntensityAnalyzer()

def has_good_service(text):
    if not text:
        return False
    text = text.lower()
    good_words = ['great service', 'excellent service', 'friendly staff',
                  'attentive', 'helpful', 'good service']
    for word in good_words:
        if word in text:
            return True
    return False

def analyze_all():
    conn = connect()
    cur = conn.cursor()
    
    cur.execute("SELECT restaurant_id FROM restaurants")
    restaurant_ids = [row[0] for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    print(f"Analyzing {len(restaurant_ids)} restaurants...")
    
    count = 0
    for rest_id in restaurant_ids:
        result = process_restaurant(rest_id)
        if result:
            count += 1
            if count % 100 == 0:
                print(f"  Processed {count} restaurants...")
    
    print(f"Done! Analyzed {count} restaurants")

def process_restaurant(restaurant_id):
    conn = connect()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT review_text, stars FROM reviews 
        WHERE restaurant_id = %s
    """, (restaurant_id,))
    reviews = cur.fetchall()
    
    if len(reviews) == 0:
        cur.close()
        conn.close()
        return None
    
    sentiments = []
    positive = 0
    negative = 0
    service = 0
    
    for text, stars in reviews:
        sent = analyze_sentiment(text)
        sentiments.append(sent)
        
        if stars >= 4:
            positive += 1
        if stars <= 2:
            negative += 1
        
        if has_good_service(text):
            service += 1
    
    avg_sentiment = sum(sentiments) / len(sentiments)
    
    cur.execute("""
        SELECT AVG(price) FROM menu_items 
        WHERE restaurant_id = %s
    """, (restaurant_id,))
    avg_price = cur.fetchone()[0] or 0
    
    cur.execute("""
        INSERT INTO restaurant_features 
            (restaurant_id, avg_sentiment, positive_reviews, negative_reviews, 
            service_mentions, avg_price)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (restaurant_id) DO UPDATE
        SET avg_sentiment    = EXCLUDED.avg_sentiment,
            positive_reviews = EXCLUDED.positive_reviews,
            negative_reviews = EXCLUDED.negative_reviews,
            service_mentions = EXCLUDED.service_mentions,
            avg_price        = EXCLUDED.avg_price
    """, (restaurant_id, avg_sentiment, positive, negative, service, avg_price))

    
    conn.commit()
    cur.close()
    conn.close()
    
    return {
        'sentiment': avg_sentiment,
        'positive': positive,
        'service': service
    }

def show_results():
    conn = connect()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT r.name, r.city, f.avg_sentiment, f.service_mentions
        FROM restaurants r
        JOIN restaurant_features f ON r.restaurant_id = f.restaurant_id
        ORDER BY f.avg_sentiment DESC
        LIMIT 10
    """)
    
    print("\nTop 10 by sentiment:")
    for name, city, sentiment, service in cur.fetchall():
        print(f"  {name} ({city}) - Sentiment: {sentiment:.3f}, Service: {service}")
    
    cur.close()
    conn.close()

def analyze_sentiment(text):
    if not text:
        return 0
    scores = vader.polarity_scores(text)
    return scores['compound']

def connect():
    conn = psycopg2.connect(
        dbname="restaurant_tips",
        user="postgres",
        password="your_password",
        host="localhost"
    )
    return conn

if __name__ == "__main__":
    print("Sentiment Analysis")
    
    analyze_all()
    show_results()
