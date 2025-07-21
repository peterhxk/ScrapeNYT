from dotenv import load_dotenv
import os
import requests


NYT_API_KEY = os.getenv("NYT_API_KEY")

def get_nyt_articles(query, start_date, end_date):
    url = f"https://api.nytimes.com/svc/search/v2/articlesearch.json?q={query}&begin_date={start_date}&end_date={end_date}&api-key={NYT_API_KEY}"
    response = requests.get(url)
    return response.json()

def main():
    query = "climate change"
    start_date = "2025-01-01"
    end_date = "2025-07-20"
    articles = get_nyt_articles(query, start_date, end_date)
    print(articles)

if __name__ == "__main__":
    main()