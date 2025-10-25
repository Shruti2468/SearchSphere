import os
import mysql.connector

# ---------- CONFIG ----------
DB_CONFIG = {
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", "root"),
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3308")),
    "database": os.getenv("DB_NAME", "hackathon"),
    "raise_on_warnings": True,
    "autocommit": False,
}
import pandas as pd

df =pd.read_csv("Bangalore_restaurants_cleaned_rag.csv")
df_new=df[['name', 'link', 'cuisine', 'price', 'location',
       'ratings', 'address', 'review_passages', 'embedding']]


# ---------- CONNECT ----------
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)
print("✅ Connected to MySQL")

# ---------- INSERT DATA ----------
insert_query = """
INSERT INTO restaurant2 
(name, link, cuisine, price, location, ratings, address, reviews, embedding)
VALUES (%s, %s, %s, %s, ST_PointFromText(%s), %s, %s, %s, VEC_FromText(%s))
"""

for _, row in df_new.iterrows():
    try:
        point = f"POINT{(row['location'])}"
        print(point)
    except:
        point = 'POINT(0 0)'

    try:
        embedding = row['embedding']
        if pd.isna(embedding) or embedding in ["", "[]", None]:
            embedding_str = "[]"
        else:
            embedding_str = str(embedding)
    except:
        embedding_str = "[]"

    cursor.execute(insert_query, (
        row['name'] if pd.notna(row['name']) else None,
        row['link'] if pd.notna(row['link']) else None,
        row['cuisine'] if pd.notna(row['cuisine']) else None,
        float(row['price']) if pd.notna(row['price']) else None,
        point,
        float(row['ratings']) if pd.notna(row['ratings']) else None,
        row['address'] if pd.notna(row['address']) else None,
        row['review_passages'] if pd.notna(row['review_passages']) else None,
        embedding_str
    ))

# ---------- COMMIT AND CLOSE ----------
conn.commit()
cursor.close()
conn.close()
print("✅ Data inserted successfully into 'restaurant2' table!")

# ---------- CONNECT ----------
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)
print("✅ Connected to MySQL")

# Check which database is currently in use
cursor.execute("SELECT DATABASE() AS current_db;")
result = cursor.fetchone()
print(f"🔹 Currently connected to database: {result['current_db']}")
