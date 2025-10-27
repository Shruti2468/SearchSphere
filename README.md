# SearchSphere: Semantic + Geo Restaurant Search

**Author:** Shruti Suresh  
**Domain:** NLP, Semantic Search, Geospatial Filtering, Streamlit App

---

##  Project Overview

**SearchSphere** allows users to search for restaurants in **Bangalore** using:

- **Semantic similarity of reviews** – Understands the meaning behind your natural language queries.  
- **Geo-location filtering** – Filters restaurants based on distance from your location.  
- **Summarized reviews** – Provides concise insights without reading lengthy reviews.

The project uses a preprocessed CSV file (`Bangalore_restaurants.csv`) and **MariaDB**.  
Web scraping is **not required** to run the application — you can directly use the provided CSV file.

The CSV file was created by scraping popular Bangalore restaurant pages from **Zomato**.  
You may modify or extend it by adding more restaurants if needed.

---

##  Setup Instructions

### 1. Prerequisites

- Python 3.11 or higher  
- MariaDB 10.11 or higher (with **VECTOR** support)  
- Chrome and ChromeDriver *(only required if you plan to run the web scraping code)*

> **Note:** Running the web scraping code is not required to use the database or the Streamlit app.



### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```


### 3. Database Setup
Run the **database_setup**.py script and update the environment variables with your database credentials.
This script creates the database, defines the table structure, and inserts values from the CSV file.

**Table Structure**

```bash
sql
Copy code
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
VECTOR INDEX (embedding) M = 10 DISTANCE = COSINE;
```

> Note: Cosine distance is used as it provided better results for this use case,
but Euclidean distance can also be used with MariaDB.

The CSV already contains embeddings and cleaned reviews.

### 4. Launch the Streamlit App

```bash
streamlit run streamlitmain.py
```

###  Using the App
Enter a query such as:
>- places with live sports screening and wheelchair access
>- cafes with vegan options and live music

Then:
- Select the number of restaurants to display.
- Set the maximum distance (in kilometers).
- Click Search to view results.

**The app will display:**
- Restaurant name, link, and address
- Price and distance
- Summarized reviews
- Semantic similarity score

### Quick Notes
- The LLM used in this demo is for demonstration purposes and may not always provide highly accurate summaries.
- The tester’s location is fixed to Bangalore for consistency.
- You can uncomment the geospatial query code to enable dynamic location-based filtering.

*MariaDB was chosen because it supports both vector search (for embeddings) and geospatial queries (for location filtering) within the same table — simplifying the implementation.*

### Features
- Semantic Search – Understands natural language queries
- Geo-filtering – Finds restaurants within a preferred distance
- Review Summarization – Provides concise summaries of reviews
- Fast Retrieval – Utilizes vector indexing for quick results

###  Tech Stack
Backend	*Python, MariaDB (Vector Support)*
Frontend	*Streamlit*
NLP	*Sentence Transformers (384-dimensional embeddings)*
Geospatial	*Point-based location filtering*
Automation	*Selenium with ChromeDriver*

### Future Enhancements
- Multi-city support
- Enhanced UI with restaurant images
- Advanced filtering (price range, ratings, cuisine type)
- Real-time review updates
- Interactive map visualization

License
This project was created for educational and demonstration purposes only.