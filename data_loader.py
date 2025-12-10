import psycopg2
from datasets import load_dataset
import random

def connect():
    conn = psycopg2.connect(
        dbname="restaurant_tips",
        user="postgres",
        password="your_password",
        host="localhost"
    )
    return conn

def load_yelp_data():
    print("Loading Yelp dataset from Hugging Face...")
    print("This may take a few minutes on first run...")
    
    dataset = load_dataset("yelp_review_full", split="train[:50000]")
    
    conn = connect()
    cur = conn.cursor()
    
    restaurant_count = 0
    review_count = 0
    
    restaurants = {}
    
    print(f"\nProcessing {len(dataset)} reviews...")
    
    cities = ["Las Vegas", "Phoenix", "Charlotte", "Pittsburgh", "Toronto", 
              "Montreal", "Cleveland", "Madison", "Scottsdale", "Henderson"]
    states = ["NV", "AZ", "NC", "PA", "ON", "QC", "OH", "WI", "AZ", "NV"]
    price_ranges = ["$", "$", "$$", "$$"]
    
    for i, item in enumerate(dataset):
        business_id = f"business_{i % 5000}"
        
        if business_id not in restaurants:
            city_idx = random.randint(0, len(cities)-1)
            
            cur.execute("""
                INSERT INTO restaurants 
                (restaurant_id, name, city, state, stars, review_count, price_range)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (restaurant_id) DO NOTHING
            """, (
                business_id,
                f"Restaurant {i % 5000}",
                cities[city_idx],
                states[city_idx],
                round(random.uniform(2.5, 5.0), 1),
                0,
                random.choice(price_ranges)
            ))
            restaurants[business_id] = True
            restaurant_count += 1
        
        review_id = f"review_{i}"
        stars = item['label'] + 1
        text = item['text']
        
        cur.execute("""
            INSERT INTO reviews 
            (review_id, restaurant_id, stars, review_text, review_date)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (review_id) DO NOTHING
        """, (
            review_id,
            business_id,
            stars,
            text,
            '2015-01-01'
        ))
        review_count += 1
        
        if review_count % 5000 == 0:
            print(f"  Loaded {review_count} reviews, {len(restaurants)} restaurants...")
            conn.commit()
    
    conn.commit()
    
    print("\nUpdating review counts...")
    cur.execute("""
        UPDATE restaurants r
        SET review_count = (
            SELECT COUNT(*) FROM reviews 
            WHERE restaurant_id = r.restaurant_id
        )
    """)
    conn.commit()
    
    cur.execute("SELECT restaurant_id, price_range FROM restaurants")
    restaurant_list = cur.fetchall()
    
    items = [
        ('Burger', 12.99),
        ('Pasta', 14.99),
        ('Salad', 9.99),
        ('Pizza', 13.99),
        ('Steak', 24.99)
    ]
    
    menu_count = 0
    print("Creating menu items...")
    
    for rest_id, price_range in restaurant_list:
        mult = 1.0
        if price_range == '$': mult = 1.5
        elif price_range == '$': mult = 2.5
        elif price_range == '$$': mult = 4.0
        
        for name, price in items:
            cur.execute("""
                INSERT INTO menu_items (restaurant_id, item_name, price)
                VALUES (%s, %s, %s)
            """, (rest_id, name, price * mult))
            menu_count += 1
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("\n")
    print("Data Loading Complete")
    print(“\n”)
    print(f"Restaurants: {restaurant_count:,}")
    print(f"Reviews: {review_count:,}")
    print(f"Menu items: {menu_count:,}")

if __name__ == "__main__":
    print("\n”)
    print("Yelp Data Loader")
    print("\n”)
    load_yelp_data()

