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


load_dotenv()

NYT_API_KEY = os.getenv("NYT_API_KEY")

total_articles_recorded = 0


#Scrape 5000+ articles from New York Times.
#title, name of the newspaper, url, publish date, writers, article content and other metadata

def get_nyt_articles(start_date, end_date, page, max_retries = 5):
    url = f"https://api.nytimes.com/svc/search/v2/articlesearch.json?begin_date={start_date}&end_date={end_date}&page={page}&api-key={NYT_API_KEY}"
    requestHeaders = {
        "Accept": "application/json"
    }
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, headers=requestHeaders)
            if response.status_code == 429:
                print("Received 429 Too Many Requests. Sleeping for 10s")
                time.sleep(10)
                retries += 1
                continue
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            if retries < max_retries -1:
                print("Retrying in 10 seconds...")
                time.sleep(10)
                retries += 1
            else:
                print("Max retries reached. Skipping this request.")
                return None

def append_article_to_jsonl(article_data, filename="nyt_articles.jsonl"):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(json.dumps(article_data, ensure_ascii=False) + "\n")
    total_articles_recorded += 1
    print(f"total articles recorded to file: {total_articles_recorded}")

def robust_get(url, max_retries=5, wait_seconds=60):
    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {wait_seconds} seconds... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_seconds)
            else:
                print("Max retries reached. Skipping this article.")
                return None

def safe_save_to_wayback(url, user_agent, max_retries=5):
    retries = 0
    while retries < max_retries:
        try:
            save_api = waybackpy.WaybackMachineSaveAPI(url, user_agent)
            return save_api.save()
        except waybackpy.exceptions.TooManyRequestsError:
            print("Wayback Machine rate limit hit. Waiting 5 minutes before retrying...")
            time.sleep(300)
            retries += 1
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: {e}. Waiting 1 minute before retrying...")
            time.sleep(60)
            retries += 1
        except Exception as e:
            print(f"Unexpected error during save: {e}. Skipping this article.")
            return None
    print("Max retries reached for archiving. Skipping this article.")
    return None

def safe_lookup_wayback(url, user_agent, max_retries=5):
    retries = 0
    while retries < max_retries:
        try:
            lookup_api = waybackpy.WaybackMachineCDXServerAPI(url, user_agent)
            return lookup_api.newest().archive_url
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error during lookup: {e}. Waiting 1 minute before retrying...")
            time.sleep(60)
            retries += 1
        except Exception as e:
            print(f"Unexpected error during lookup: {e}. Skipping this article.")
            return None
    print("Max retries reached for lookup. Skipping this article.")
    return None

def write_to_json(articles):
    print(f"Total articles to process: {len(articles)}")
    articles_json = []
    for idx, article in enumerate(articles):
        print(f"Proceeding with article index {idx}")
        url = article["web_url"]
        user_agent = "Mozilla/5.0"

        #first check if its already archived
        archive_url = None
        loopup_api = waybackpy.WaybackMachineCDXServerAPI(url, user_agent)
        try:
            snapshot_url = loopup_api.newest()
            archive_url = snapshot_url.archive_url
            print(f"already archived")
        except Exception:
            #if not archived, try to archive it
            archive_url = safe_save_to_wayback(url, user_agent)
        
        if archive_url is None:
            with open("failed_urls.txt", "a") as fail_log:
                fail_log.write(url + "\n")
            continue
        
        response = robust_get(archive_url)
        if response is None:
            print(f"Failed to fetch archived page for {url}, skipping.")
            continue
        soup = BeautifulSoup(response.text, "html.parser")

        article_body = soup.find("section", {"name": "articleBody"})
        if article_body:
            paragraphs = article_body.find_all("p")
            text = "\n".join([p.get_text() for p in paragraphs])
            print("Article content found")
        else:
            print("Could not find article body. Try extracting all <p> tags as fallback.")
            paragraphs = soup.find_all("p")
            text = "\n".join([p.get_text() for p in paragraphs])
            print("Fallback content found")
        
        if not text:
            print(f"Could not extract article body, skipping article of {url}")
            continue
        
        title = article["headline"]["main"]
        article_data = {
            "title": title,
            "newspaper": article["source"],
            "url": article["web_url"],
            "archive_url": archive_url,
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
            print(f"Proceeding with archiving to extract article content, length {len(docs)}")
            total_articles+=10
            write_to_json(docs)
            
            page+=1
        i += 1
        


if __name__ == "__main__":
    main()