import sys
import json
import requests
import time
from bs4 import BeautifulSoup

def scrape_simple(url, output_path):
    """Simple scraper that makes multiple attempts to extract content."""
    try:
        print(f"Starting simple scraping for {url}")
        
        # Add user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Get the page
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Save the HTML for debugging
        with open(f"{output_path}.html", 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        # Get the title
        title = soup.title.string if soup.title else "Untitled"
        
        # Try different methods to extract content
        structured_content = []
        
        # Method 1: Extract all headings
        for i in range(1, 7):
            headings = soup.find_all(f'h{i}')
            for heading in headings:
                text = heading.get_text(strip=True)
                if text:
                    structured_content.append({
                        "type": f"h{i}",
                        "content": text
                    })
        
        # Method 2: Extract all paragraphs
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text:
                structured_content.append({
                    "type": "paragraph",
                    "content": text
                })
        
        # Method 3: Extract all list items
        lists = soup.find_all(['ul', 'ol'])
        for list_elem in lists:
            list_type = list_elem.name  # 'ul' or 'ol'
            items = []
            
            for li in list_elem.find_all('li'):
                text = li.get_text(strip=True)
                if text:
                    items.append(text)
            
            if items:
                structured_content.append({
                    "type": "list",
                    "list_type": list_type,
                    "items": items
                })
        
        # Method 4: Extract all divs with significant text
        divs = soup.find_all('div')
        for div in divs:
            # Only get divs with a decent amount of text
            text = div.get_text(strip=True)
            if len(text) > 50 and not any(text in p.get("content", "") for p in structured_content if p.get("type") == "paragraph"):
                structured_content.append({
                    "type": "paragraph",
                    "content": text[:500]  # Limit very long texts
                })
        
        # Method 5: If we couldn't find much, extract all text
        if len(structured_content) < 3:
            all_text = soup.get_text(" ", strip=True)
            if all_text:
                # Split into paragraphs at double newlines or when line has > 3 words
                paragraphs = []
                current = ""
                
                for line in all_text.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                        
                    if len(line.split()) > 3:  # Line with more than 3 words
                        if current:
                            paragraphs.append(current)
                            current = ""
                        paragraphs.append(line)
                    else:
                        if current:
                            current += " " + line
                        else:
                            current = line
                
                if current:
                    paragraphs.append(current)
                
                # Add the paragraphs to structured content
                for p in paragraphs:
                    if len(p) > 20 and not any(p in existing.get("content", "") for existing in structured_content):
                        structured_content.append({
                            "type": "paragraph", 
                            "content": p[:500]  # Limit length
                        })
        
        # If still no content, add a fallback message
        if not structured_content:
            structured_content.append({
                "type": "paragraph",
                "content": "No content could be extracted from this page. It may require JavaScript to display content."
            })
        
        # For debugging/development, add metadata
        structured_content.append({
            "type": "paragraph",
            "content": f"Scraped at: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        })
        
        # Create the result object
        result = {
            "title": title,
            "structured_content": structured_content
        }
        
        # Save as JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        return 0
    
    except Exception as e:
        print(f"Error in simple scraping: {e}")
        
        # Create error result
        error_result = {
            "title": f"Error: Could not scrape {url}",
            "structured_content": [{
                "type": "paragraph",
                "content": f"Failed to scrape content: {str(e)}"
            }]
        }
        
        # Save error result
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(error_result, f, indent=2)
        
        return 1

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scrape_simple.py <url> <output_path>")
        sys.exit(1)
    
    url = sys.argv[1]
    output_path = sys.argv[2]
    
    exit_code = scrape_simple(url, output_path)
    sys.exit(exit_code)