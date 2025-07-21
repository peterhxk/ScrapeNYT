with open("nyt_articles.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        article = json.loads(line)
        print(article)