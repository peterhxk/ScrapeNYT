from newspaper import Article

url = 'https://www.nytimes.com/2025/07/20/obituaries/edwin-feulner-dead.html'
article = Article(url)

article.download()
article.parse()

print(article.title)
print(article.text)


# try:
#     article = Article(url, language='en')
#     article.download()
#     article.parse()
#     article.nlp()
#     print("Summary:", article.summary)
#     print("keywords:", article.keywords)
#     # print("Title:", article.title)
#     # print("Authors:", article.authors)
#     # print("Publish Date:", article.publish_date)
#     # print("Top Image:", article.top_image)
#     # print("Text:\n", article.text)
# except Exception as e:
#     print(f"Failed to extract article: {e}")