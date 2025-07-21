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

def write_to_json(articles):
    print(f"Total articles to process: {len(articles)}")
    articles_json = []
    for idx, article in enumerate(articles):
        print(f"Proceeding with article index {idx}")
        url = article["web_url"]
        user_agent = "Mozilla/5.0"

        save_api = waybackpy.WaybackMachineSaveAPI(url, user_agent)
        archive_url = None
        while archive_url is None:
            try:
                archive_url = save_api.save()
            except waybackpy.exceptions.TooManyRequestsError:
                print("Wayback Machine rate limit hit. Waiting 5 minutes before retrying...")
                time.sleep(300) 

        response = requests.get(archive_url)
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
            print(f"Current total articles processed: {total_articles}")
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