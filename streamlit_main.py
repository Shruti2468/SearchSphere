import streamlit as st
import mysql.connector
from sentence_transformers import SentenceTransformer
import numpy as np
import os
import geocoder
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
from dotenv import load_dotenv

load_dotenv()

device = "cpu"
model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
model_name = "sshleifer/distilbart-cnn-12-6"
tokenizer = AutoTokenizer.from_pretrained(model_name)
summarization_model = AutoModelForSeq2SeqLM.from_pretrained(model_name, device_map=None)
summarizer = pipeline("summarization", model=summarization_model, tokenizer=tokenizer, device=-1)

conn = mysql.connector.connect(
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME"),
)
cursor = conn.cursor(dictionary=True)

st.set_page_config(page_title="SearchSphere", layout="wide")
st.title("SearchSphere: Semantic + Geo Restaurant Search")

def vector_to_mysql_string(vector: np.ndarray) -> str:
    return "[" + ",".join([str(x) for x in vector]) + "]"

def display_or_na(val):
    return val if val is not None else "N/A"

def search_database(query_vec: np.ndarray, k=5, lat=None, lon=None, radius_km=None):
    vec_str = vector_to_mysql_string(query_vec)

    sql = f"""
        SELECT 
            id, name, link, price, ratings, address, reviews,
            ST_Distance_Sphere(
                POINT(ST_Y(location), ST_X(location)), 
                POINT({lon}, {lat})
            ) AS distance_m,
            VEC_DISTANCE_COSINE(embedding, VEC_FromText('{vec_str}')) AS semantic_score
        FROM restaurants
        WHERE ST_Distance_Sphere(
                POINT(ST_Y(location), ST_X(location)), 
                POINT({lon}, {lat})
            ) <= {radius_km * 1000}
        ORDER BY semantic_score
        LIMIT {k};
        """

    cursor.execute(sql)
    return cursor.fetchall()

def summarize_review(review_text, user_query):
    review_text = review_text[:4000]  
    prompt = (
        f"Extract the reviews from the text and summarize them, removing junk words and keeping only useful information. "
        f"Do not include address.\n"
        f"User query: {user_query}\n"
        f"Review: {review_text}\n"
        "Keep it short and clear."
    )
    summary = summarizer(prompt, do_sample=False, max_new_tokens=150)
    return summary[0]['summary_text']

st.subheader("Your Location")

user_lat=12.97390
user_lon=77.59471
st.info(f"Detected location: ({user_lat:.5f}, {user_lon:.5f})")

# g = geocoder.ip('me')
# user_lat, user_lon = g.latlng if g.ok else (None, None)
# if user_lat is None or user_lon is None:
#     st.warning("Could not detect location automatically. Please enter manually:")
#     user_lat = st.number_input("Latitude", value=12.9716, format="%.6f")
#     user_lon = st.number_input("Longitude", value=77.5946, format="%.6f")
# else:
#     st.info(f"Detected location: ({user_lat:.5f}, {user_lon:.5f})")


query = st.text_input("Enter your query (e.g., quiet, pet-friendly café with Wi-Fi):")
num_results = st.slider("Number of results to show", min_value=1, max_value=20, value=5)
max_distance_km = st.slider("Search within (km)", min_value=1, max_value=20, value=5)

if st.button("Search") and query.strip() != "":
    with st.spinner("Searching..."):
        query_vec = model.encode([query])[0]
        results = search_database(
            query_vec=query_vec,
            k=num_results,
            lat=user_lat,
            lon=user_lon,
            radius_km=max_distance_km
        )

    if not results:
        st.warning("No results found.")
    else:
        st.success(f"Found {len(results)} results!")
        for i, res in enumerate(results, 1):
            summary_text = summarize_review(res['reviews'], query)
            st.markdown(f"### {i}. {display_or_na(res['name'])}")
            st.markdown(f"{summary_text}")
            st.markdown(f"- **Price:** {display_or_na(res['price'])}")
            st.markdown(f"- **Address:** {display_or_na(res['address'])}")
            st.markdown(f"- **Link:** {display_or_na(res['link'])}")
            if 'distance_m' in res:
                st.markdown(f"- **Distance:** {res['distance_m']/1000:.2f} km")
            st.markdown(f"- **Semantic score:** {res['semantic_score']:.4f}")
            st.markdown("---")
