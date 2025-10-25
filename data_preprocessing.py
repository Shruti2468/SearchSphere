
import re
import pandas as pd
from nltk.tokenize import sent_tokenize
import nltk
from sentence_transformers import SentenceTransformer
import numpy as np
import unicodedata
nltk.download('punkt')

def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text).lower()

    text = unicodedata.normalize("NFKD", text)

    text = re.sub(r'http\S+|www\.\S+|\S+@\S+', ' ', text)

    ui_noise = [
        r'star[-\w]+', r'votes for helpful', r'followers?', r'cross', r'otp',
        r'log in', r'sign up', r'apps for you', r'©.*?zomato', r'select country',
        r'select language', r'detect current location', r'direction[-\w]+',
        r'table[-\w]+', r'view gallery', r'photosmenu', r'related restaurants',
        r'top stores', r'using gps', r'\d{1,3}(\.\d)?\s*dining ratings',
        r'\d{1,3}(\.\d)?\s*delivery ratings', r'opens in new tab',
        r'\b\d+\s*(days|day|months|month|years|year)\s*ago\b',        
        r'\b[a-z\s]+[0-9]*\s*reviews[0-9]*\s*follow\b',              
        r'\d+\s*comments?',                                          
        r'tanisha gowda', r'jeevitha m', r'rohit roy', r'madhusudan kumar', r'hitesh chadha', 
        r'12345', r'chevron right', r'chevron down',              
        r'home india bengaluru', r'related to.*?block', r'frequent searches.*',  
        r'about zomato.*', r'privacy.*', r'terms of service.*', r'cookie policy.*', 
        r'new to zomato.*create account', r'sign in with google.*' 
    ]
    text = re.sub("|".join(ui_noise), ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'[^a-z0-9\s\.,]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\b(\w+)( \1\b)+', r'\1', text) 
    return text

def extract_unique_reviews(clean_text):
    if not clean_text.strip():
        return []
    sentences = sent_tokenize(clean_text)
    seen = set()
    unique_sentences = []
    for s in sentences:
        s_clean = s.strip()
        if s_clean and s_clean not in seen:
            seen.add(s_clean)
            unique_sentences.append(s_clean)
    return unique_sentences

def split_into_passages(sentences, max_sentences=3):
    passages = []
    for i in range(0, len(sentences), max_sentences):
        chunk = " ".join(sentences[i:i+max_sentences]).strip()
        if chunk:
            passages.append(chunk)
    return passages

def vector_to_mysql_string(vector: np.ndarray) -> str:
    return "[" + ",".join([str(float(x)) for x in vector]) + "]"

def process_row(row, model):
    cleaned_text_val = clean_text(row['all_reviews'])
    cleaned_text_val = cleaned_text_val.replace("location filldown trianglecurrent location search home india bengaluru", "")
    cleaned_text_val = str(row.get("additional_info", ""))+ " " +cleaned_text_val.lower()
    unique_reviews = extract_unique_reviews(cleaned_text_val)
    review_passages = split_into_passages(unique_reviews, max_sentences=3)
    embedding = model.encode([" ".join(unique_reviews)])[0]
    embedding_str = vector_to_mysql_string(embedding)

    return {
        'name': row['name'],
        'link': row['link'],
        'cuisine': str(row.get('cuisine', '')).replace(',', ' '),
        'price': re.sub(r'[^\d.]', '', str(row.get('price_for_one', ''))),
        'latitude': row['latitude'],
        'longitude': row['longitude'],
        'location': f"({row['latitude']} {row['longitude']})",
        'ratings': row.get('ratings', None),
        'additional_info_items': str(row.get('additional_info', '')).replace('|', ','), 
        'address': row.get('address', ''),
        'cleaned_text': cleaned_text_val,
        'cleaned_reviews': " ".join(unique_reviews),
        'unique_reviews': unique_reviews,
        'review_passages': review_passages,
        'embedding': embedding_str
    }

file_path = r"Bangalore_restaurants_complete.csv"
df = pd.read_csv(file_path)

df['price_for_one'] = df['price_for_one'].astype(str).str.replace('â‚¹', '').str.replace('for two', '').str.strip()
df['additional_info'] = df['additional_info'].astype(str).str.replace('|', ',')

model = SentenceTransformer('all-MiniLM-L6-v2')

processed_rows = df.apply(lambda row: process_row(row, model), axis=1)
processed_df = pd.DataFrame(processed_rows.tolist())
processed_df.to_csv("Bangalore_restaurants_cleaned_rag.csv", index=False, encoding='utf-8')

print(f"CSV updated with cleaned reviews, passages, and embeddings: Bangalore_restaurants_cleaned_rag.csv")
print(processed_df[['cleaned_reviews', 'review_passages', 'embedding']].head())
