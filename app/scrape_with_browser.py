import sys
import time
import json
import traceback
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_with_selenium(url, output_path):
    """Scrape a webpage using Selenium with Firefox headless browser."""
    print(f"Starting Selenium scraping for {url}")
    driver = None
    
    try:
        # Set up Firefox options
        firefox_options = Options()
        firefox_options.add_argument("--headless")
        
        # Create a Firefox webdriver
        print("Creating Firefox webdriver...")
        driver = webdriver.Firefox(options=firefox_options)
        
        # Set page load timeout
        driver.set_page_load_timeout(30)
        
        # Navigate to the URL
        print(f"Navigating to URL: {url}")
        driver.get(url)
        
        # Wait for the page to load (extra time for JavaScript-dependent pages)
        print("Waiting for page to load...")
        time.sleep(5)  # Give some time for JavaScript to execute
        
        # Take a screenshot for debugging purposes
        print("Taking screenshot...")
        driver.save_screenshot(f"{output_path}.png")
        
        # Extract page content
        print("Extracting page title...")
        title = driver.title
        
        print("Extracting body text...")
        body_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Initialize structured content
        structured_content = []
        
        # Extract headings
        print("Extracting headings...")
        for heading_level in range(1, 7):
            headings = driver.find_elements(By.TAG_NAME, f"h{heading_level}")
            for heading in headings:
                if heading.is_displayed() and heading.text.strip():
                    structured_content.append({
                        "type": f"h{heading_level}",
                        "content": heading.text.strip()
                    })
        
        # Extract paragraphs
        print("Extracting paragraphs...")
        paragraphs = driver.find_elements(By.TAG_NAME, "p")
        for paragraph in paragraphs:
            if paragraph.is_displayed() and paragraph.text.strip():
                structured_content.append({
                    "type": "paragraph",
                    "content": paragraph.text.strip()
                })
        
        # Extract lists
        print("Extracting lists...")
        lists = driver.find_elements(By.CSS_SELECTOR, "ul, ol")
        for list_elem in lists:
            if list_elem.is_displayed():
                list_type = list_elem.tag_name  # 'ul' or 'ol'
                list_items = list_elem.find_elements(By.TAG_NAME, "li")
                
                items = []
                for item in list_items:
                    if item.is_displayed() and item.text.strip():
                        items.append(item.text.strip())
                
                if items:
                    structured_content.append({
                        "type": "list",
                        "list_type": list_type,
                        "items": items
                    })
        
        # If no structured content found but there's body text,
        # add body text as paragraphs
        if not structured_content and body_text:
            print("No structured content found, using body text...")
            paragraphs = [p.strip() for p in body_text.split('\n\n') if p.strip()]
            
            for paragraph in paragraphs:
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
            "title": title,
            "structured_content": structured_content
        }
        
        # Save result as JSON
        print(f"Saving content to {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        print("Selenium scraping completed successfully")
        return 0
    
    except Exception as e:
        print(f"Error in Selenium scraping: {e}")
        traceback.print_exc()
        
        # Create error result
        error_result = {
            "title": f"Error: Could not scrape {url}",
            "structured_content": [{
                "type": "paragraph",
                "content": f"Failed to scrape content with Selenium: {str(e)}"
            }]
        }
        
        # Save error result
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(error_result, f, indent=2)
        
        return 1
    
    finally:
        # Close the browser
        if driver:
            print("Closing browser...")
            driver.quit()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scrape_with_browser.py <url> <output_path>")
        sys.exit(1)
    
    url = sys.argv[1]
    output_path = sys.argv[2]
    
    exit_code = scrape_with_selenium(url, output_path)
    sys.exit(exit_code)