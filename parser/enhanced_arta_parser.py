# minsky_doc_parser.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json

BASE_URL = "http://rtd.lan.arta.kz/docs/guide/ru/minsky/"

def get_all_doc_links(index_url=BASE_URL):
    response = requests.get(index_url)
    response.encoding = "utf-8"  # 👈 Force UTF-8 decoding
    soup = BeautifulSoup(response.text, "html.parser")

    toc_links = []
    for link in soup.select("div.toctree-wrapper a.reference.internal"):
        href = link.get("href")
        full_url = urljoin(index_url, href)
        toc_links.append((link.text.strip(), full_url))
    
    return toc_links

# def scrape_doc_page(url):
#     response = requests.get(url)
#     response.encoding = "utf-8"  # 👈 Force UTF-8 decoding
#     soup = BeautifulSoup(response.text, "html.parser")
#
#     content_div = soup.find("div", {"role": "main"})
#     if not content_div:
#         return ""
#
#     text_parts = []
#     for tag in content_div.find_all(['h1', 'h2', 'h3', 'p', 'li']):
#         text_parts.append(tag.get_text(strip=True))
#
#     return "\n".join(text_parts)


def scrape_doc_page(url):
    response = requests.get(url)
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")

    content_div = soup.find("div", {"role": "main"})
    if not content_div:
        return []

    sections = []
    current_section = {"title": "", "text": []}

    for tag in content_div.find_all(['h1', 'h2', 'h3', 'p', 'li']):
        if tag.name in ['h1', 'h2', 'h3']:
            # If we already have a section, save it
            if current_section["title"] and current_section["text"]:
                sections.append({
                    "title": current_section["title"],
                    "text": "\n".join(current_section["text"])
                })
            # Start new section
            current_section = {
                "title": tag.get_text(strip=True),
                "text": []
            }
        else:
            # Continue adding to current section
            current_section["text"].append(tag.get_text(strip=True))

    # Add the last section if not empty
    if current_section["title"] and current_section["text"]:
        sections.append({
            "title": current_section["title"],
            "text": "\n".join(current_section["text"])
        })

    return sections


# def parse_minsky_docs_to_json(output_file="minsky_docs.json"):
#     toc_links = get_all_doc_links()
#
#     documents, metadatas, ids = [], [], []
#     for idx, (title, url) in enumerate(toc_links, start=1):
#         print(f"Scraping ({idx}/{len(toc_links)}): {title} -> {url}")
#         text = scrape_doc_page(url)
#
#         if text:  # Check if the list of sections is not empty
#             # Format the sections into a single document
#             formatted_text = ""
#             for section in text:
#                 formatted_text += f"# {section['title']}\n{section['text']}\n\n"
#             
#             documents.append(formatted_text)
#             metadatas.append({'source': title})
#             ids.append(str(idx))
#
#     with open(output_file, "w", encoding="utf-8") as f:
#         json.dump({
#             "documents": documents,
#             "metadatas": metadatas,
#             "ids": ids
#         }, f, ensure_ascii=False, indent=2)
#
#     print(f"✅ Saved {len(documents)} documents to {output_file}")


def parse_minsky_docs_to_json(output_file="minsky_docs.json"):
    toc_links = get_all_doc_links()

    documents, metadatas, ids = [], [], []
    section_counter = 1

    for idx, (page_title, url) in enumerate(toc_links, start=1):
        print(f"Scraping ({idx}/{len(toc_links)}): {page_title} -> {url}")
        sections = scrape_doc_page(url)

        for section in sections:
            documents.append(section["text"])
            metadatas.append({
                "source": f"{page_title} — {section['title']}",
                "url": url
            })
            ids.append(str(section_counter))
            section_counter += 1

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "documents": documents,
            "metadatas": metadatas,
            "ids": ids
        }, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved {len(documents)} document sections to {output_file}")


if __name__ == "__main__":
    parse_minsky_docs_to_json()

