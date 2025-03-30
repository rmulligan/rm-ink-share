import sys
import json
import traceback
from requests_html import HTMLSession

def scrape_with_requests_html(url, output_path):
    """Scrape a webpage using requests-html with JavaScript support."""
    print(f"Starting requests-html scraping for {url}")
    session = None
    
    try:
        # Create HTML Session
        print("Creating HTML session...")
        session = HTMLSession()
        
        # Send request to URL
        print(f"Sending request to {url}...")
        response = session.get(url)
        
        # Run JavaScript on the page
        print("Running JavaScript on the page...")
        # This might take some time on first run as it downloads Chromium
        response.html.render(timeout=30)
        
        # Save HTML for debugging
        print("Saving rendered HTML...")
        with open(f"{output_path}.html", 'w', encoding='utf-8') as f:
            f.write(response.html.html)
        
        # Extract title
        print("Extracting title...")
        title = response.html.find('title', first=True)
        title_text = title.text if title else "Untitled"
        
        # Initialize structured content
        structured_content = []
        
        # Extract headings
        print("Extracting headings...")
        for heading_level in range(1, 7):
            headings = response.html.find(f'h{heading_level}')
            for heading in headings:
                if heading.text.strip():
                    structured_content.append({
                        "type": f"h{heading_level}",
                        "content": heading.text.strip()
                    })
        
        # Extract paragraphs
        print("Extracting paragraphs...")
        paragraphs = response.html.find('p')
        for paragraph in paragraphs:
            if paragraph.text.strip():
                structured_content.append({
                    "type": "paragraph",
                    "content": paragraph.text.strip()
                })
        
        # Extract lists
        print("Extracting lists...")
        lists = response.html.find('ul, ol')
        for list_elem in lists:
            list_type = 'ul' if list_elem.tag == 'ul' else 'ol'
            list_items = list_elem.find('li')
            
            items = []
            for item in list_items:
                if item.text.strip():
                    items.append(item.text.strip())
            
            if items:
                structured_content.append({
                    "type": "list",
                    "list_type": list_type,
                    "items": items
                })
        
        # If no structured content found but there's body text, add it
        if not structured_content:
            print("No structured content found, using full text...")
            body_text = response.html.find('body', first=True)
            if body_text and body_text.text.strip():
                text_paragraphs = [p.strip() for p in body_text.text.split('\n\n') if p.strip()]
                
                for paragraph in text_paragraphs:
                    structured_content.append({
                        "type": "paragraph",
                        "content": paragraph
                    })
        
        # If still no content, add fallback message
        if not structured_content:
            print("No content found, adding fallback message...")
            structured_content.append({
                "type": "paragraph",
                "content": "No content could be extracted from this page."
            })
        
        # Create result object
        result = {
            "title": title_text,
            "structured_content": structured_content
        }
        
        # Save result as JSON
        print(f"Saving content to {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        print("requests-html scraping completed successfully")
        return 0
    
    except Exception as e:
        print(f"Error in requests-html scraping: {e}")
        traceback.print_exc()
        
        # Create error result
        error_result = {
            "title": f"Error: Could not scrape {url}",
            "structured_content": [{
                "type": "paragraph",
                "content": f"Failed to scrape content with requests-html: {str(e)}"
            }]
        }
        
        # Save error result
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(error_result, f, indent=2)
        
        return 1
    
    finally:
        # Close the session
        if session:
            print("Closing session...")
            session.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scrape_with_requests_html.py <url> <output_path>")
        sys.exit(1)
    
    url = sys.argv[1]
    output_path = sys.argv[2]
    
    exit_code = scrape_with_requests_html(url, output_path)
    sys.exit(exit_code)