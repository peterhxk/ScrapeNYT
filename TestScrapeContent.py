from waybackpy import WaybackMachineSaveAPI
import requests
from bs4 import BeautifulSoup

url = "https://www.nytimes.com/2025/07/20/us/politics/ice-agents-masks.html"
user_agent = "Mozilla/5.0"

save_api = WaybackMachineSaveAPI(url, user_agent)
archive_url = save_api.save()

response = requests.get(archive_url)
soup = BeautifulSoup(response.text, "html.parser")

article_body = soup.find("section", {"name": "articleBody"})
if article_body:
    paragraphs = article_body.find_all("p")
    text = "\n".join([p.get_text() for p in paragraphs])
    print("Article content:\n", text)
else:
    print("Could not find article body. Try extracting all <p> tags as fallback.")
    paragraphs = soup.find_all("p")
    text = "\n".join([p.get_text() for p in paragraphs])
    print("Fallback content:\n", text)
