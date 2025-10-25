# SearchSphere: Semantic + Geo Restaurant Search

**Author:** Shruti Suresh  
**Domain:** NLP, Semantic Search, Geospatial Filtering, Streamlit App

---

## **Project Overview**

SearchSphere allows searching restaurants in Bangalore using:

- **Semantic similarity of reviews** - Natural language understanding of your queries
- **Geo-location filtering** - Distance-based filtering from your location
- **Summarized reviews** - Quick insights without reading lengthy reviews

The project uses a preprocessed CSV (`Bangalore_restaurants_cleaned_rag.csv`) and MariaDB. No web scraping is needed to run the code , you can just use the csv provided.

---

## **Setup Instructions**

### 1️ Prerequisites

- Python 3.11+
- MariaDB 10.11+ (or MySQL 8.0+ with VECTOR support)
- Chrome + ChromeDriver (ensure version matches your Chrome)
- Internet connection

### 2️ Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3️ Database Setup

Start MariaDB and create a database (default: `hackathon`):

```sql
CREATE DATABASE hackathon;
```

Ensure the `restaurant2` table exists with the following structure:

```sql
CREATE TABLE restaurant2 (
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
```

### 4️ Insert Preprocessed Data

Run the Python script to insert the CSV data into MariaDB:

```bash
python insert_to_db.py
```

> **Note:** CSV already contains embeddings and cleaned reviews. No scraping needed.

### 5️ Launch the Streamlit App

```bash
streamlit run streamlitmain.py
```

---

## **Using the App**

1. **Enter your query**, e.g.:

   ```
   -> places with Live sports screening and is Wheelchair accessible
   -> cafes with vegan options and live music
   ```

2. **Select number of restaurants** to show

3. **Set maximum distance** (in km)

4. **Click Search** to view results

The app will display:

- Restaurant Name, Link, and Address
- Price and Distance
- Summarized Reviews
- Semantic similarity score

---

## **Quick Notes**

- The LLM used in this demo is intended for demonstration purposes and may not provide highly accurate responses.
- The tester’s location is currently fixed to Bangalore for consistency. You can uncomment the geospatial query code to enable dynamic location-based filtering.
- MariaDB is used as the database because it supports both vector search (for embeddings) and geospatial queries (for location filtering) within the same table, simplifying implementation for this demo.

---

## **Features**

**Semantic Search** - Understands natural language queries  
**Geo-filtering** - Find restaurants within your preferred distance  
**Review Summarization** - Get the essence without reading everything  
**Fast Retrieval** - Vector indexing for quick results

---

## **Tech Stack**

- **Backend:** Python, MariaDB with Vector Support
- **Frontend:** Streamlit
- **NLP:** Sentence Transformers (384-dimensional embeddings)
- **Geospatial:** Point-based location filtering
- **Browser Automation:** Selenium with ChromeDriver

---

## **Future Enhancements**

- 🌐 Multi-city support
- 🎨 Enhanced UI with restaurant images
- 📊 Advanced filtering (price range, ratings, cuisine type)
- 💬 Real-time review updates
- 🗺️ Interactive map visualization

---

## **License**

This project is created for educational and demonstration purposes.

---

**Happy Searching!**
