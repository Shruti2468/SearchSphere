import pandas as pd
import time
from selenium import webdriver
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import json

HEADLESS = False
SCROLL_PAUSE = 1.5
MAX_SCROLL_ITERS = 200
BASE_URL = "https://www.zomato.com"

def setup_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    if HEADLESS:
        options.add_argument("--headless=new")
    return webdriver.Chrome(service=Service(), options=options)

def safe_text(tag):
    return tag.get_text(strip=True) if tag else ""

def scroll_to_bottom(driver, pause=3):
    screen_height = driver.execute_script("return window.screen.height;")
    i = 1
    while True:
        driver.execute_script(f"window.scrollTo(0, {screen_height}*{i});")
        i += 1
        time.sleep(pause)
        scroll_height = driver.execute_script("return document.body.scrollHeight;")
        if (screen_height) * i > scroll_height:
            break

def parse_json_ld(soup):
    try:
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                candidates = data if isinstance(data, list) else [data]
                for item in candidates:
                    if isinstance(item, dict) and item.get('@type') == 'Restaurant':
                        addr = item.get('address', {})
                        address = ", ".join([str(addr.get(k, '')).strip() for k in 
                                           ['streetAddress', 'addressLocality', 'addressRegion', 'postalCode', 'addressCountry'] 
                                           if addr.get(k)])
                        geo = item.get('geo', {})
                        lat = geo.get('latitude', '') or geo.get('lat', '')
                        lng = geo.get('longitude', '') or geo.get('lng', '') or geo.get('lon', '')
                        if address or lat or lng:
                            return address, str(lat), str(lng)
            except:
                continue
    except:
        pass
    return "", "", ""

def extract_additional_info(soup):
    try:
        add_div = soup.find("div", class_=lambda x: x and 'additional-info' in x)
        if add_div:
            items = [p.get_text(strip=True) for p in add_div.find_all('p') if p.get_text(strip=True)]
            return " | ".join(items)
    except:
        pass
    return ""

def find_reviews_link(soup):
    try:
        tab = soup.find(lambda tag: tag.has_attr('id') and str(tag['id']).startswith('tablink_'))
        if tab:
            a = tab.find('a', string=lambda s: s and 'reviews' in s.lower())
            if a and a.get('href'):
                return urljoin(BASE_URL, a['href'])
        a = soup.find('a', string=lambda s: s and 'reviews' in s.lower())
        if a and a.get('href'):
            return urljoin(BASE_URL, a['href'])
        a = soup.find('a', href=lambda h: h and '/reviews' in h)
        if a and a.get('href'):
            return urljoin(BASE_URL, a['href'])
    except:
        pass
    return ""

def fetch_reviews(driver, url):
    try:
        driver.get(url)
        time.sleep(2)
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(MAX_SCROLL_ITERS):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        soup = BeautifulSoup(driver.page_source, "html.parser")
        candidates = soup.find_all(lambda t: t.name in ['div','p','span'] and t.get_text(strip=True))
        reviews = []
        seen = set()
        for cand in candidates:
            txt = cand.get_text(strip=True)
            if len(txt) > 20 and not txt.lower().startswith("reviews") and txt not in seen:
                seen.add(txt)
                reviews.append(txt)
        return " | ".join(reviews)
    except Exception as e:
        print(f"Error fetching reviews: {e}")
        return ""

def scrape_restaurants():
    start = time.time()
    driver = setup_driver()
    driver.get(f"{BASE_URL}/bangalore/restoran")
    time.sleep(2)
    scroll_to_bottom(driver)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    divs = soup.find_all('div', class_='jumbo-tracker')
    data = []
    for idx, parent in enumerate(divs):
        print(f"[{idx+1}/{len(divs)}] Processing restaurant...")
        link_tag = parent.find("a")
        link = urljoin(BASE_URL, link_tag['href']) if link_tag and 'href' in link_tag.attrs else ""
        name = safe_text(parent.find("h4"))
        p_tags = parent.find_all('p')
        cuisine = safe_text(p_tags[0]) if len(p_tags) >= 1 else ""
        price = safe_text(p_tags[1]) if len(p_tags) >= 2 else ""   
        description = additional_info = reviews = address = lat = lng = ""
        if link:
            try:
                driver.get(link)
                time.sleep(1.5)
                page_soup = BeautifulSoup(driver.page_source, "html.parser")
                desc_tag = page_soup.find('meta', {'name': 'description'})
                description = desc_tag['content'].strip() if desc_tag and desc_tag.get('content') else ""
                additional_info = extract_additional_info(page_soup)
                address, lat, lng = parse_json_ld(page_soup)
                reviews_link = find_reviews_link(page_soup)
                if reviews_link:
                    print(f"    -> Fetching reviews from {reviews_link}")
                    reviews = fetch_reviews(driver, reviews_link)
                time.sleep(1.0)
            except Exception as e:
                print(f"    -> Error: {e}")
        data.append({
            'name': name,
            'link': link,
            'cuisine': cuisine,
            'price_for_one': price,
            'address': address,
            'latitude': lat,
            'longitude': lng,
            'description': description,
            'additional_info': additional_info,
            'all_reviews': reviews
        })
    driver.quit()
    
    df = pd.DataFrame(data)
    df.to_csv("Bangalore_restaurants_complete.csv", index=False, encoding='utf-8')
    print(f"\nSaved {len(df)} restaurants to Bangalore_restaurants_complete.csv")
    print(f"Elapsed time: {time.time() - start:.2f}s")
    return df

if __name__ == "__main__":
    df = scrape_restaurants()
