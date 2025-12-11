# Yelp Tip Prediction Model
A PostgreSQL-based system that predicts restaurant tip percentages by analyzing customer review sentiment using VADER and training machine learning models to help food service workers identify high-tipping restaurants before accepting employment.

### Link to Database
<img width="1200" height="675" alt="image" src="https://github.com/user-attachments/assets/c0379016-181b-4878-8d24-6d6d8fd711e5" />

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
