from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime, timedelta
import time
import trafilatura
import waybackpy
import json
from newspaper import Article
import random

load_dotenv()

NYT_API_KEY = os.getenv("NYT_API_KEY")

total_articles_recorded = 0


#Scrape 5000+ articles from New York Times.
#title, name of the newspaper, url, publish date, writers, article content and other metadata

def get_nyt_articles(start_date, end_date, page, max_retries = 6):
    url = f"https://api.nytimes.com/svc/search/v2/articlesearch.json?begin_date={start_date}&end_date={end_date}&page={page}&api-key={NYT_API_KEY}"
    
    USER_AGENTS = [
        # Chrome - Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    # Chrome - macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
    # Chrome - Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    # Firefox - Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
    # Firefox - macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13.2; rv:109.0) Gecko/20100101 Firefox/117.0",
    # Edge - Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.35",
    # Opera - Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.64 Safari/537.36 OPR/98.0.4759.15",
    # Safari - iPhone
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    # Safari - iPad
    "Mozilla/5.0 (iPad; CPU OS 15_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
    # Chrome - Android
    "Mozilla/5.0 (Linux; Android 12; Pixel 6 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.131 Mobile Safari/537.36",

    ]
    requestHeaders = {
        "Accept": "application/json",
        "User-Agent": random.choice(USER_AGENTS)
    }
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, headers=requestHeaders)
            if response.status_code == 200:
                print("request success, auto sleep for 2.5-5.0s")
                time.sleep(random.uniform(2.5, 5.0))
                return response.json()
            elif response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    time.sleep(int(retry_after))
                    continue
                retries += 1
                raise Exception("429 Too many requests from NYT")
        except Exception as e:
            print(f"Request failed: {e}")
            sleep_time = random.uniform(20+2 ** retries, 20+2 ** (retries + 1))
            print(f"Rate limited. Sleeping {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
    print("Max retries reached. Skipping this request.")
    log_failed_request(start_date,end_date,page)
    return None

def append_article_to_jsonl(article_data, filename="nyt_articles.jsonl"):
    global total_articles_recorded
    with open(filename, "a", encoding="utf-8") as f:
        f.write(json.dumps(article_data, ensure_ascii=False) + "\n")
    total_articles_recorded += 1
    print(f"total articles recorded to file: {total_articles_recorded}")

def log_failed_url(url, filename="failed_urls.txt"):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(url + "\n")
def log_failed_request(start_date, end_date, page, filename="failed_requests.txt"):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"{start_date},{end_date},{page}"+"\n")

def write_to_json(articles):
    print(f"Total articles to process: {len(articles)}")
    articles_json = []
    for idx, article in enumerate(articles):
        print(f"Proceeding with article index {idx}")
        url = article["web_url"]

        try:
            article_from_newspaper = Article(url)
            article_from_newspaper.download()
            article_from_newspaper.parse()
            text = article_from_newspaper.text
        except Exception as e:
            print(f"Could not extract article body, skipping article of {url}")
            log_failed_url(url)
            continue
        
        title = article["headline"]["main"]
        article_data = {
            "title": title,
            "newspaper": article["source"],
            "url": article["web_url"],
            "publish_date": article["pub_date"],
            "writers": article["byline"]["original"],
            "content": text
        }
        append_article_to_jsonl(article_data)
        print(f"Article with title: {title} appended to nyt_articles.json")
    print("All articles are written to nyt_articles.json")

def main():
    # today = datetime.today().strftime('%Y%m%d')
    today = datetime.today()
    #get 500 articles from everyweek for the past 20 weeks
    i = 0
    total_articles = 0
    while True:
        start_date = today - timedelta(days=30+30*i)
        start_date_str = start_date.strftime('%Y%m%d')
        end_date = today - timedelta(days=30*i)
        end_date_str = end_date.strftime('%Y%m%d')
        page = 0
        print(f"now fetching starting {start_date_str}, ending {end_date_str}")
        while True:
            print(f"Current total articles parsed into program: {total_articles}")
            articles = get_nyt_articles(start_date_str, end_date_str, page)
            if not articles:
                print("Received none from this request, proceed to next week")
                break
            docs = articles['response']['docs'] 
            if not docs:
                break
            print(f"Proceeding with extracting article content, length {len(docs)}")
            total_articles+=10
            write_to_json(docs)
            
            page+=1
        i += 1
        


if __name__ == "__main__":
    main()