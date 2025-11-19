import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin

BASE_URL = "http://tdd.lan.arta.kz/docs/synergy/tags/minsky/user-manual/html/en.index.html"

def scrape_manual(output_file="user_manual_docs.json"):
    base_domain = BASE_URL.rsplit('/', 1)[0] + "/"
    response = requests.get(BASE_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    documents = []
    metadatas = []
    ids = []

    # --- Step 1: Find all TOC links ---
    toc_links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.endswith(".html") and not href.startswith("http"):
            full_url = urljoin(base_domain, href)
            toc_links.append((full_url, link.text.strip()))

    print(f"Found {len(toc_links)} pages in the manual.")

    # --- Step 2: Visit each page and scrape content ---
    counter = 1
    for url, link_text in toc_links:
        try:
            page = requests.get(url)
            page_soup = BeautifulSoup(page.text, "html.parser")

            # Collect main headings and paragraphs
            content = ""
            for tag in page_soup.find_all(['h1', 'h2', 'h3', 'p']):
                text = tag.get_text(strip=True)
                if text:
                    content += text + "\n"

            if content.strip():
                documents.append(content.strip())
                metadatas.append({'source': link_text or f"Page {counter}", 'url': url})
                ids.append(str(counter))
                counter += 1

        except Exception as e:
            print(f"⚠️ Error fetching {url}: {e}")

    # --- Step 3: Save to JSON file ---
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "documents": documents,
            "metadatas": metadatas,
            "ids": ids
        }, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved {len(documents)} pages to {output_file}")

if __name__ == "__main__":
    scrape_manual()

