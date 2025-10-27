import re
import unicodedata
from pathlib import Path
import numpy as np
import pandas as pd
import nltk
from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer

nltk.download("punkt", quiet=True)
model = SentenceTransformer("all-MiniLM-L6-v2")


def clean_text(text: str) -> str:
    if pd.isna(text) or str(text).strip() == "":
        return ""

    text = str(text).lower()
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"http\S+|www\.\S+|\S+@\S+", " ", text)

    ui_noise = [
        r"star[-\w]+",
        r"votes for helpful",
        r"followers?",
        r"cross",
        r"otp",
        r"log in",
        r"sign up",
        r"apps for you",
        r"©.*?zomato",
        r"select country",
        r"select language",
        r"detect current location",
        r"direction[-\w]+",
        r"table[-\w]+",
        r"view gallery",
        r"photosmenu",
        r"related restaurants",
        r"top stores",
        r"using gps",
        r"\d{1,3}(\.\d)?\s*dining ratings",
        r"\d{1,3}(\.\d)?\s*delivery ratings",
        r"opens in new tab",
        r"\b\d+\s*(days|day|months|month|years|year)\s*ago\b",
        r"\b[a-z\s]+[0-9]*\s*reviews[0-9]*\s*follow\b",
        r"\d+\s*comments?",
        r"chevron right",
        r"chevron down",
        r"home india bengaluru",
        r"related to.*?block",
        r"frequent searches.*",
        r"about zomato.*",
        r"privacy.*",
        r"terms of service.*",
        r"cookie policy.*",
        r"new to zomato.*create account",
        r"sign in with google.*",
    ]

    text = re.sub("|".join(ui_noise), " ", text, flags=re.IGNORECASE)
    text = re.sub(r"[^a-z0-9\s\.,]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\b(\w+)( \1\b)+", r"\1", text)
    return text


def extract_unique_reviews(cleaned_text: str) -> list[str]:
    if not cleaned_text or not cleaned_text.strip():
        return []
    sentences = sent_tokenize(cleaned_text)
    seen = set()
    unique_sentences = []
    for s in sentences:
        s_clean = s.strip()
        if s_clean and s_clean not in seen:
            seen.add(s_clean)
            unique_sentences.append(s_clean)
    return unique_sentences


def split_into_passages(sentences: list[str], max_sentences: int = 3) -> list[str]:
    passages = []
    for i in range(0, len(sentences), max_sentences):
        chunk = " ".join(sentences[i : i + max_sentences]).strip()
        if chunk:
            passages.append(chunk)
    return passages


def vector_to_mysql_string(vector: np.ndarray) -> str:
    return "[" + ",".join([str(float(x)) for x in vector]) + "]"


def process_row(row: pd.Series, model: SentenceTransformer) -> dict:
    all_reviews = row.get("all_reviews", "")
    additional_info = row.get("additional_info", "") or ""
    name = row.get("name", "")
    link = row.get("link", "")
    cuisine = row.get("cuisine", "") or ""
    price_for_one = row.get("price_for_one", "")
    latitude = row.get("latitude", None)
    longitude = row.get("longitude", None)
    ratings = row.get("ratings", None)
    address = row.get("address", "") or ""
    cleaned_text_val = clean_text(all_reviews)
    cleaned_text_val = cleaned_text_val.replace(
        "location filldown trianglecurrent location search home india bengaluru", ""
    )
    cleaned_text_val = f"{additional_info} {cleaned_text_val}".strip().lower()
    unique_reviews = extract_unique_reviews(cleaned_text_val)
    review_passages = split_into_passages(unique_reviews, max_sentences=3)
    text_for_embedding = " ".join(unique_reviews) if unique_reviews else ""
    embedding = model.encode([text_for_embedding])[0]
    embedding_str = vector_to_mysql_string(embedding)
    cuisine_clean = str(cuisine).replace(",", " ")
    additional_info_items = str(additional_info).replace("|", ",")
    price_str = re.sub(r"[^\d.]", "", str(price_for_one))

    return {
        "name": name,
        "link": link,
        "cuisine": cuisine_clean,
        "price": price_str,
        "latitude": latitude,
        "longitude": longitude,
        "location": f"({latitude} {longitude})" if pd.notna(latitude) and pd.notna(longitude) else "",
        "ratings": ratings,
        "additional_info_items": additional_info_items,
        "address": address,
        "cleaned_text": cleaned_text_val,
        "cleaned_reviews": " ".join(unique_reviews),
        "unique_reviews": unique_reviews,
        "review_passages": review_passages,
        "embedding": embedding_str,
    }


def main(csv: str) -> None:
    input_path = Path(csv)
    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {csv}")
    df = pd.read_csv(input_path, encoding="utf-8", dtype=str).fillna("")
    if "price_for_one" in df.columns:
        df["price_for_one"] = (
            df["price_for_one"]
            .astype(str)
            .str.replace("â‚¹", "", regex=False)
            .str.replace("for two", "", regex=False)
            .str.strip()
        )
    if "additional_info" in df.columns:
        df["additional_info"] = df["additional_info"].astype(str).str.replace("|", ",", regex=False)

    processed_rows = df.apply(lambda r: process_row(r, model), axis=1)
    processed_df = pd.DataFrame(processed_rows.tolist())
    processed_df.to_csv(csv, index=False, encoding="utf-8")
    print(f"CSV updated with cleaned reviews, passages, and embeddings: {csv}")
    print(processed_df[["cleaned_reviews", "review_passages", "embedding"]].head().to_string())


if __name__ == "__main__":
    CSV = "../Bangalore_restaurants.csv"
    main(CSV)
