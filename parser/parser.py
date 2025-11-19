import requests
from bs4 import BeautifulSoup
import re
import json

def parse_constitution_to_json(output_file="constitution_docs.json"):
    url = "https://www.akorda.kz/en/constitution-of-the-republic-of-kazakhstan-50912"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    documents, metadatas, ids = [], [], []
    current_doc = ""
    current_article_title = ""
    counter = 1

    article_pattern = re.compile(r'\bArticle\s+\d+\b', re.IGNORECASE)

    for tag in soup.find_all(['h2', 'h3', 'p']):
        text = tag.get_text(strip=True)

        if article_pattern.fullmatch(text):
            if current_article_title and current_doc:
                documents.append(current_doc.strip())
                metadatas.append({'source': current_article_title})
                ids.append(str(counter))
                counter += 1

            current_article_title = text
            current_doc = text + "\n"

        elif tag.name == 'p' and current_article_title:
            current_doc += text + " "

    if current_article_title and current_doc:
        documents.append(current_doc.strip())
        metadatas.append({'source': current_article_title})
        ids.append(str(counter))

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "documents": documents,
            "metadatas": metadatas,
            "ids": ids
        }, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(documents)} articles to {output_file}")

if __name__ == "__main__":
    parse_constitution_to_json()


