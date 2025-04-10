import os
import time
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup
import uuid
from .interfaces import IWebScraperService

class WebScraperService(IWebScraperService):
    def __init__(self, temp_dir: str):
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)

    def scrape(self, url: str) -> Dict:
        """Scrape webpage content and return structured data"""
        try:
            print(f"Scraping URL: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = self._extract_title(soup)
            
            # Process content
            content_list = []
            image_list = []
            self._process_content_elements(soup.body, content_list, image_list, url)
            
            return {
                "title": title,
                "structured_content": content_list,
                "images": image_list
            }
            
        except Exception as e:
            print(f"Error scraping URL: {e}")
            return {
                "title": "Error Processing URL",
                "structured_content": [{"type": "paragraph", "content": f"Error: {str(e)}"}],
                "images": []
            }

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title from page"""
        if soup.title:
            return soup.title.string.strip()
        
        h1 = soup.find('h1')
        if h1:
            return h1.get_text().strip()
        
        return "Untitled Document"

    def _process_content_elements(self, element, content_list: List, image_list: List, base_url: str):
        """Process HTML elements into structured content"""
        if not element:
            return

        # Process headings
        for i in range(1, 7):
            for heading in element.find_all(f'h{i}', recursive=False):
                content_list.append({
                    "type": f"h{i}",
                    "content": heading.get_text().strip()
                })

        # Process paragraphs
        for p in element.find_all('p', recursive=False):
            text = p.get_text().strip()
            if text:
                content_list.append({
                    "type": "paragraph",
                    "content": text
                })

        # Process images
        for img in element.find_all('img', recursive=False):
            src = img.get('src', '')
            if src:
                if not src.startswith(('http://', 'https://')):
                    src = self._make_absolute_url(base_url, src)
                
                img_id = str(uuid.uuid4())
                image_list.append({
                    "id": img_id,
                    "src": src,
                    "alt": img.get('alt', '')
                })
                
                content_list.append({
                    "type": "image",
                    "image_id": img_id
                })

        # Process other block elements
        for child in element.children:
            if hasattr(child, 'name'):
                self._process_content_elements(child, content_list, image_list, base_url)

    def _make_absolute_url(self, base_url: str, relative_url: str) -> str:
        """Convert relative URL to absolute URL"""
        from urllib.parse import urljoin
        return urljoin(base_url, relative_url)