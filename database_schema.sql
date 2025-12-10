DROP TABLE IF EXISTS tip_predictions;
DROP TABLE IF EXISTS restaurant_features;
DROP TABLE IF EXISTS menu_items;
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS restaurants;

CREATE TABLE restaurants (
    restaurant_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(50),
    stars DECIMAL(2,1),
    review_count INT,
    price_range VARCHAR(5)
);

CREATE TABLE reviews (
    review_id VARCHAR(50) PRIMARY KEY,
    restaurant_id VARCHAR(50),
    stars INT,
    review_text TEXT,
    review_date DATE,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id)
);

CREATE TABLE menu_items (
    item_id SERIAL PRIMARY KEY,
    restaurant_id VARCHAR(50),
    item_name VARCHAR(200),
    price DECIMAL(8,2),
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id)
);


CREATE TABLE tip_predictions (
    restaurant_id VARCHAR(50) PRIMARY KEY,
    predicted_tip_pct DECIMAL(5,2),
    tip_category VARCHAR(20),
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id)
);



CREATE TABLE restaurant_features (
    restaurant_id VARCHAR(50) PRIMARY KEY,
    avg_sentiment DECIMAL(4,3),
    positive_reviews INT,
    negative_reviews INT,
    service_mentions INT,
    avg_price DECIMAL(8,2),
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id)
);


CREATE INDEX idx_city ON restaurants(city);
CREATE INDEX idx_restaurant_reviews ON reviews(restaurant_id);
