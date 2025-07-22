from newspaper import Article

url = 'https://www.nytimes.com/2025/07/20/obituaries/edwin-feulner-dead.html'

try:
    article = Article(url)
    article.download()
    article.parse()
    print("Title:", article.title)
    print("Authors:", article.authors)
    print("Publish Date:", article.publish_date)
    print("Top Image:", article.top_image)
    print("Text:\n", article.text)  # Print first 1000 characters
except Exception as e:
    print(f"Failed to extract article: {e}")