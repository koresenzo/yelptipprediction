# Yelp Tip Prediction Model
A PostgreSQL-based system that predicts restaurant tip percentages by analyzing customer review sentiment using VADER and training machine learning models to help food service workers identify high-tipping restaurants before accepting employment.

### Link to Database:
https://huggingface.co/datasets/Yelp/yelp_review_full

### Software needed
- PostgreSQL installed and running
- Python 3.8+

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Open PostgreSQL
psql restaurant_tips

# Run schema file
\i database_schema.sql

# Quit
\q
```

### Running the System

**Run full pipeline**
```bash
python3 run_all.py
```

**Run the App**

```bash
python3 -m streamlit run app.py
```
