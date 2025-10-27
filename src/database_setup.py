import os
import mysql.connector
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

conn = mysql.connector.connect(
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
)
cursor = conn.cursor()

create_database = "CREATE DATABASE IF NOT EXISTS search_sphere;"
cursor.execute(create_database)
cursor.execute("USE search_sphere;")

create_table_query = """
CREATE TABLE IF NOT EXISTS restaurants (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    link VARCHAR(500),
    cuisine VARCHAR(255),
    price DECIMAL(10, 2),
    location POINT,
    ratings DECIMAL(3, 1),
    address VARCHAR(500),
    reviews TEXT,
    embedding VECTOR(384) NOT NULL,
    VECTOR INDEX (embedding) M = 10 DISTANCE = COSINE
);
"""
cursor.execute(create_table_query)

insert_query = """
INSERT INTO restaurants
(name, link, cuisine, price, location, ratings, address, reviews, embedding)
VALUES (%s, %s, %s, %s, ST_PointFromText(%s), %s, %s, %s, VEC_FromText(%s))
"""

df = pd.read_csv("../Bangalore_restaurants.csv")
df_new = df[[
    "name", "link", "cuisine", "price", "location",
    "ratings", "address", "review_passages", "embedding"
]]

for _, row in df_new.iterrows():
    try:
        point = f"POINT{(row['location'])}" if pd.notna(row["location"]) else "POINT(0 0)"
    except Exception:
        point = "POINT(0 0)"
    try:
        embedding = row["embedding"]
        if pd.isna(embedding) or embedding in ["", "[]", None]:
            embedding_str = "[]"
        else:
            embedding_str = str(embedding)
    except Exception:
        embedding_str = "[]"

    try:
        cursor.execute(insert_query, (
            row["name"] if pd.notna(row["name"]) else None,
            row["link"] if pd.notna(row["link"]) else None,
            row["cuisine"] if pd.notna(row["cuisine"]) else None,
            float(row["price"]) if pd.notna(row["price"]) and str(row["price"]).strip() != "" else None,
            point,
            float(row["ratings"]) if pd.notna(row["ratings"]) and str(row["ratings"]).strip() != "" else None,
            row["address"] if pd.notna(row["address"]) else None,
            row["review_passages"] if pd.notna(row["review_passages"]) else None,
            embedding_str
        ))
    except Exception as e:
        print(f" Skipped a row due to error: {e}")

conn.commit()
cursor.close()
conn.close()
print(" Data inserted successfully into 'restaurants' table!")


"""
for reference to check if the location is entered correctly since normal select dosent work
SELECT id,
    name,
    ST_AsText(location) AS location_text
FROM restaurant;
"""