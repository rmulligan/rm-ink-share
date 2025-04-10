"""Web scraping service that tries multiple methods."""

import os
import json
import subprocess
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebScraperService:
    """Scrapes web content using multiple fallback methods."""
    
    def __init__(self, temp_dir: str):
        """Initialize with temp directory for content files.
        
        Args:
            temp_dir: Directory to save temporary content
        """
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
        
        # Script paths - relative to current file location
        current_dir = os.path.dirname(os.path.abspath(__file__))
        app_dir = os.path.dirname(current_dir)
        self.scraper_scripts = {
            "playwright": os.path.join(app_dir, "scrape_js.py"),
            "simple": os.path.join(app_dir, "scrape_simple.py"),
            "browser": os.path.join(app_dir, "scrape_with_browser.py"),
            "requests_html": os.path.join(app_dir, "scrape_with_requests_html.py")
        }

    def scrape(self, url: str) -> Dict[str, Any]:
        """Scrape content from URL using multiple methods.
        
        Args:
            url: The URL to scrape
            
        Returns:
            Dict containing title, structured_content, and images
        """
        logger.info(f"Scraping URL: {url}")
        
        # Create temporary output path for content
        content_path = os.path.join(self.temp_dir, f"content_{hash(url)}.json")
        
        # Try manual title extraction first for reliability
        extracted_title = self._extract_title_directly(url)
        
        # Try different scrapers in order until one succeeds
        scrapers = [
            ("playwright", "Using Playwright for JavaScript-enabled scraping"),
            ("simple", "Using simple requests + BeautifulSoup scraping"),
            ("browser", "Using Selenium browser-based scraping"),
            ("requests_html", "Using requests-html scraping")
        ]
        
        for scraper_name, message in scrapers:
            script_path = self.scraper_scripts.get(scraper_name)
            if not script_path or not os.path.exists(script_path):
                logger.warning(f"Scraper script not found: {scraper_name}")
                continue
                
            logger.info(message)
            
            try:
                # Run the scraper script
                result = subprocess.run(
                    ["python3", script_path, url, content_path],
                    capture_output=True,
                    text=True,
                    check=False  # Don't raise an exception on non-zero exit
                )
                
                # Check if content was generated successfully
                if result.returncode == 0 and os.path.exists(content_path):
                    with open(content_path, 'r', encoding='utf-8') as f:
                        content = json.load(f)
                    
                    # Update the title if our extracted title is better
                    if extracted_title and (not content.get('title') or content.get('title') == "Untitled" or len(extracted_title) > len(content.get('title', ''))):
                        logger.info(f"Using directly extracted title: {extracted_title}")
                        content['title'] = extracted_title
                    
                    # Validate the content structure
                    content = self._validate_and_fix_content(content, url)
                    
                    # Save the updated content back to the file
                    with open(content_path, 'w', encoding='utf-8') as f:
                        json.dump(content, f, indent=2)
                    
                    logger.info(f"Successfully scraped with {scraper_name}")
                    return content
                else:
                    logger.warning(f"Failed to scrape with {scraper_name}: {result.stderr}")
            except Exception as e:
                logger.warning(f"Error using {scraper_name} scraper: {str(e)}")
        
        # If all scrapers fail, return a basic error content with the best title we have
        logger.error("All scrapers failed to extract content")
        title = extracted_title or f"Failed to Extract: {url}"
        return {
            "title": title,
            "structured_content": [{
                "type": "paragraph",
                "content": f"Could not extract content from {url}. All scraping methods failed."
            }, {
                "type": "paragraph",
                "content": "You can try visiting this page directly on your device."
            }],
            "images": []
        }
    
    def _extract_title_directly(self, url: str) -> str:
        """Extract title directly from URL using requests and BeautifulSoup.
        
        Args:
            url: The URL to extract title from
            
        Returns:
            Extracted title or empty string if failed
        """
        try:
            # Try to get a clean title directly
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to get title from various elements
            title = None
            
            # Try standard title tag
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
                
            # Try OpenGraph title which is often better
            if not title or len(title) < 3:
                og_title = soup.find('meta', property='og:title')
                if og_title and og_title.get('content'):
                    title = og_title['content'].strip()
            
            # Try Twitter title
            if not title or len(title) < 3:
                twitter_title = soup.find('meta', property='twitter:title')
                if twitter_title and twitter_title.get('content'):
                    title = twitter_title['content'].strip()
            
            # Try h1 if no title found
            if not title or len(title) < 3:
                h1 = soup.find('h1')
                if h1:
                    title = h1.get_text(strip=True)
            
            # If the title is too long, truncate it
            if title and len(title) > 100:
                title = title[:97] + "..."
                
            # Clean the title
            if title:
                title = title.replace('\n', ' ').replace('\r', '').strip()
                
            return title or self._generate_title_from_url(url)
            
        except Exception as e:
            logger.warning(f"Error extracting title directly: {e}")
            return self._generate_title_from_url(url)
    
    def _generate_title_from_url(self, url: str) -> str:
        """Generate a title from URL if no title can be extracted.
        
        Args:
            url: The URL to generate title from
            
        Returns:
            Generated title
        """
        try:
            parsed_url = urlparse(url)
            
            # Use domain as base
            domain = parsed_url.netloc.replace('www.', '')
            
            # Try to use path segments
            path = parsed_url.path
            if path and path not in ('/', ''):
                # Remove trailing slash
                if path.endswith('/'):
                    path = path[:-1]
                
                # Get last path segment
                segments = path.split('/')
                page = segments[-1] if segments else ''
                
                if page:
                    # Convert slug to title
                    page = page.replace('-', ' ').replace('_', ' ')
                    page = ' '.join(word.capitalize() for word in page.split())
                    
                    # Remove file extension if present
                    if '.' in page:
                        page = page.split('.')[0]
                    
                    return f"{page} - {domain}"
            
            # Fallback to just the domain
            return f"Page from {domain}"
            
        except Exception as e:
            logger.warning(f"Error generating title from URL: {e}")
            return "Web Page"
    
    def _validate_and_fix_content(self, content: Dict, url: str) -> Dict:
        """Validate and fix content structure.
        
        Args:
            content: The content to validate and fix
            url: The source URL
            
        Returns:
            Fixed content
        """
        # Ensure title exists and is not empty
        if not content.get('title') or len(content.get('title', '').strip()) < 2:
            content['title'] = self._generate_title_from_url(url)
        
        # Ensure content is not empty
        if not content.get('structured_content') or len(content.get('structured_content', [])) == 0:
            content['structured_content'] = [{
                "type": "paragraph",
                "content": f"This is a page from {url}. Content could not be properly extracted."
            }]
        
        # Convert legacy formats
        structured_content = content.get('structured_content', [])
        for i, item in enumerate(structured_content):
            # Handle list items format conversion
            if item.get('type') == 'list' and 'items' in item:
                list_items = item.pop('items', [])
                for j, list_item in enumerate(list_items):
                    structured_content.insert(i + j + 1, {
                        "type": "bullet",
                        "content": list_item
                    })
        
        # Ensure images list exists
        if 'images' not in content:
            content['images'] = []
            
        return content