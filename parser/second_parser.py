# minsky_form_api_parser.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import re
import os

# Target URL specifically for form scripting API
FORM_API_URL = "http://rtd.lan.arta.kz/docs/guide/ru/minsky/form_scripting.html"

def get_form_api_links(url=FORM_API_URL):
    """Get all links to the API documentation sections from the form scripting page."""
    response = requests.get(url)
    response.encoding = "utf-8"  # Force UTF-8 decoding
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find all links in the table of contents that match our API sections
    api_links = []
    
    # Look for the section links in the table of contents
    # The sections typically have numbered patterns like "3.5.x"
    toc_sections = soup.select("div.toctree-wrapper a.reference.internal")
    
    for link in toc_sections:
        href = link.get("href")
        text = link.text.strip()
        
        # Check if this is one of the API sections (starting with numbers like 3.5.x)
        if re.match(r'^\d+\.\d+\.\d+', text):
            full_url = urljoin(url, href)
            api_links.append((text, full_url))
    
    return api_links

def scrape_api_section(url):
    """Scrape a specific API documentation section."""
    response = requests.get(url)
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")

    # Find the main content div
    content_div = soup.find("div", {"role": "main"})
    if not content_div:
        return None

    # Get the section title (h1, h2, or h3)
    section_title = None
    for h_tag in content_div.find_all(['h1', 'h2', 'h3'], limit=1):
        section_title = h_tag.get_text(strip=True)
        break
    
    if not section_title:
        return None
    
    # Extract the section content
    content = []
    
    # Find the section element that contains our target content
    section_element = None
    for element in content_div.find_all(['div', 'section']):
        if element.find(['h1', 'h2', 'h3']) and section_title in element.find(['h1', 'h2', 'h3']).get_text():
            section_element = element
            break
    
    if not section_element:
        section_element = content_div  # Fallback to main content div
    
    # Extract all relevant content (paragraphs, code blocks, tables, lists)
    for tag in section_element.find_all(['p', 'pre', 'code', 'table', 'ul', 'ol', 'li', 'div', 'blockquote']):
        # Skip navigation elements and TOC
        if tag.get('class') and any(c in ['toctree-wrapper', 'toc', 'navigation'] for c in tag.get('class')):
            continue
            
        # For code blocks, preserve formatting
        if tag.name in ['pre', 'code']:
            text = tag.get_text()
            content.append(f"```\n{text}\n```")
        # For tables, try to preserve structure
        elif tag.name == 'table':
            # Simple table extraction - could be enhanced
            rows = []
            for tr in tag.find_all('tr'):
                cells = []
                for td in tr.find_all(['td', 'th']):
                    cells.append(td.get_text(strip=True))
                if cells:
                    rows.append(" | ".join(cells))
            if rows:
                content.append("\n".join(rows))
        # For lists, preserve structure
        elif tag.name in ['ul', 'ol'] and tag.parent.name not in ['ul', 'ol']:
            items = []
            for li in tag.find_all('li', recursive=False):
                items.append(f"- {li.get_text(strip=True)}")
            if items:
                content.append("\n".join(items))
        # For paragraphs and other text elements
        elif tag.name in ['p', 'blockquote'] or (tag.name == 'div' and not tag.find(['div', 'pre', 'code', 'table'])):
            text = tag.get_text(strip=True)
            if text and tag.parent.name not in ['li']:
                content.append(text)
    
    return {
        "title": section_title,
        "text": "\n\n".join(content),
        "url": url
    }

def parse_form_api_docs(output_file="minsky_form_api_docs.json"):
    """Parse the Minsky form API documentation and save to JSON file."""
    # First, get all the links to API sections
    api_links = get_form_api_links()
    
    if not api_links:
        print("❌ No API section links found. Check the URL and HTML structure.")
        return
    
    print(f"Found {len(api_links)} API section links to parse.")
    
    # Now, scrape each section
    documents = []
    metadatas = []
    ids = []
    
    for idx, (title, url) in enumerate(api_links, start=1):
        print(f"Scraping ({idx}/{len(api_links)}): {title} -> {url}")
        
        # For sections with fragments (#), we need to handle them specially
        if '#' in url:
            base_url, fragment = url.split('#', 1)
            
            # First try to get the content from the fragment
            response = requests.get(base_url)
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Try to find the specific fragment
            fragment_element = soup.find(id=fragment)
            
            if fragment_element:
                # Construct a section from the fragment
                section_title = title
                
                # Get the text from this fragment and its children
                content = []
                for tag in fragment_element.find_all(['p', 'pre', 'code', 'table', 'ul', 'ol', 'li']):
                    text = tag.get_text(strip=True)
                    if text:
                        content.append(text)
                
                if content:
                    section_data = {
                        "title": section_title,
                        "text": "\n\n".join(content),
                        "url": url
                    }
                else:
                    # If no content found in fragment, try regular scraping
                    section_data = scrape_api_section(base_url)
                    if section_data:
                        section_data["title"] = title  # Override with our section title
                        section_data["url"] = url
            else:
                # If fragment not found, try regular scraping
                section_data = scrape_api_section(base_url)
                if section_data:
                    section_data["title"] = title  # Override with our section title
                    section_data["url"] = url
        else:
            # Regular URL without fragment
            section_data = scrape_api_section(url)
        
        # Add the section data if valid
        if section_data and section_data["text"].strip():
            documents.append(section_data["text"])
            metadatas.append({
                "title": section_data["title"],
                "url": section_data["url"]
            })
            ids.append(str(idx))
        else:
            print(f"⚠️ No content found for section: {title}")
    
    # Save the results to JSON
    output_data = {
        "documents": documents,
        "metadatas": metadatas,
        "ids": ids
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Saved {len(documents)} API documentation sections to {output_file}")

def parse_all_subsections(output_file="minsky_form_api_complete.json"):
    """Parse all subsections from the form scripting page, including nested sections."""
    # First, get the main page
    response = requests.get(FORM_API_URL)
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find all section links, including subsections like 3.5.3.1, 3.5.3.2, etc.
    all_links = []
    
    # The links are often in the toctree-wrapper or in the content
    for link in soup.select("a.reference.internal"):
        href = link.get("href")
        text = link.text.strip()
        
        # Check if this matches a section pattern (numbers separated by dots)
        if re.match(r'^\d+(\.\d+)+', text):
            full_url = urljoin(FORM_API_URL, href)
            all_links.append((text, full_url))
    
    # Sort links by their section numbers for proper ordering
    def section_sort_key(item):
        # Extract numbers from section title (e.g., "3.5.3.1" -> [3, 5, 3, 1])
        numbers = [int(n) for n in re.findall(r'\d+', item[0])]
        return numbers
    
    all_links.sort(key=section_sort_key)
    
    print(f"Found {len(all_links)} section links (including subsections).")
    
    # Now scrape each section
    documents = []
    metadatas = []
    ids = []
    
    for idx, (title, url) in enumerate(all_links, start=1):
        print(f"Scraping ({idx}/{len(all_links)}): {title} -> {url}")
        
        # Handle URLs with fragments
        base_url = url.split('#')[0] if '#' in url else url
        
        # Scrape the section
        section_data = scrape_api_section(base_url)
        
        if section_data:
            # If we have a fragment, try to extract just that part
            if '#' in url:
                fragment = url.split('#')[1]
                response = requests.get(base_url)
                response.encoding = "utf-8"
                soup = BeautifulSoup(response.text, "html.parser")
                
                fragment_element = soup.find(id=fragment)
                if fragment_element:
                    # Extract text from this specific fragment
                    fragment_text = []
                    for tag in fragment_element.find_all(['p', 'pre', 'code', 'table', 'ul', 'ol', 'li']):
                        text = tag.get_text(strip=True)
                        if text:
                            fragment_text.append(text)
                    
                    if fragment_text:
                        section_data["text"] = "\n\n".join(fragment_text)
            
            # Add this section
            section_data["title"] = title  # Use the title from the TOC
            documents.append(section_data["text"])
            metadatas.append({
                "title": title,
                "url": url
            })
            ids.append(str(idx))
    
    # Save results
    output_data = {
        "documents": documents,
        "metadatas": metadatas,
        "ids": ids
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Saved {len(documents)} API documentation sections to {output_file}")

if __name__ == "__main__":
    # Use this to parse just the main API sections
    parse_form_api_docs()
    
    # Use this to parse all sections including subsections
    parse_all_subsections()
