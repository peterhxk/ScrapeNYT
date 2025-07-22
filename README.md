Hi,

For answers to Machine Learning Media Bias by Tegmark et al. article, you may headover to MachineLearningMediaBias.txt

To run the model for scraping NYT, you may follow these steps:
1. Run: pip install -r requirements.txt
2. Headover to https://developer.nytimes.com/ and get your own nytime API key (make sure you enable the Article Search API)
3. Add the API key to .env file
4. Run: python ScrapeNYT.py

The program saves the scraped information to nyt_articles.jsonl. You may then use Read_jsonl.py to extract from it.
Data format:

data
  - title
  - newspaper
  - url
  - archive_url
  - publish_date
  - writers
  - content

Unsuccessful fetches will be appended to failed_urls.txt
