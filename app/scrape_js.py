#!/usr/bin/env python3
"""
JavaScript-enabled web scraper for Pi Share Receiver.
Uses Playwright to render JavaScript-heavy pages.
"""

import sys
import json
import time
import asyncio
import os
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

async def scrape_with_playwright(url, output_path):
    """Scrape a webpage using Playwright for JavaScript support."""
    try:
        print(f"Starting Playwright scraping for {url}")
        
        # Create the Playwright browser instance
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            
            # Create a new page
            page = await context.new_page()
            
            try:
                # Try to navigate to the URL with a timeout
                print(f"Navigating to {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Wait for content to load
                print("Waiting for content to stabilize...")
                await asyncio.sleep(5)  # Give extra time for JS to execute
                
                # Check for additional wait conditions
                try:
                    # Common page load indicators
                    await page.wait_for_selector("article, .content, main, #content", timeout=5000)
                except PlaywrightTimeoutError:
                    # It's okay if we couldn't find specific content selectors
                    print("Could not find specific content selectors, continuing with page as-is")
                
                # Get the final HTML content
                html_content = await page.content()
                
                # Save the HTML for debugging
                html_debug_path = f"{output_path}.html"
                with open(html_debug_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"Saved HTML to {html_debug_path}")
                
                # Get the page title
                title = await page.title()
                
                # Take a screenshot for reference
                screenshot_path = f"{output_path}.png"
                await page.screenshot(path=screenshot_path)
                print(f"Saved screenshot to {screenshot_path}")
                
                # Parse the HTML with BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Start extracting content
                structured_content = []
                
                # Extract title and add as a heading
                if title:
                    structured_content.append({
                        "type": "h1",
                        "content": title
                    })
                
                # Try to find the main content container
                main_content = (
                    soup.find('article') or 
                    soup.find('main') or 
                    soup.find('div', class_='content') or 
                    soup.find('div', id='content') or 
                    soup.find('div', class_='main') or
                    soup.find('div', class_='article') or
                    soup.body
                )
                
                # Remove script, style, and navigational elements
                if main_content:
                    for element in main_content(["script", "style", "nav", "footer", "header", "aside"]):
                        element.extract()
                
                # Extract headings
                for i in range(1, 7):
                    headings = main_content.find_all(f'h{i}') if main_content else []
                    for heading in headings:
                        text = heading.get_text(strip=True)
                        if text:
                            structured_content.append({
                                "type": f"h{i}",
                                "content": text
                            })
                
                # Extract paragraphs
                paragraphs = main_content.find_all('p') if main_content else []
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and len(text) > 10:  # Only include substantial paragraphs
                        structured_content.append({
                            "type": "paragraph",
                            "content": text
                        })
                
                # Extract lists
                lists = main_content.find_all(['ul', 'ol']) if main_content else []
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
                
                # Extract blockquotes
                quotes = main_content.find_all('blockquote') if main_content else []
                for quote in quotes:
                    text = quote.get_text(strip=True)
                    if text:
                        structured_content.append({
                            "type": "blockquote",
                            "content": text
                        })
                
                # Extract pre/code blocks
                code_blocks = main_content.find_all(['pre', 'code']) if main_content else []
                for code in code_blocks:
                    # Skip if inside another code block (to avoid duplicates)
                    if code.find_parent('pre') or code.find_parent('code'):
                        continue
                        
                    text = code.get_text(strip=True)
                    if text:
                        structured_content.append({
                            "type": "code",
                            "content": text
                        })
                
                # If we couldn't find structured content, try extracting from the body
                if not structured_content or len(structured_content) <= 1:
                    # Method: Extract all text and split into paragraphs
                    all_text = soup.body.get_text("\n", strip=True) if soup.body else ""
                    if all_text:
                        paragraphs = [p.strip() for p in all_text.split('\n\n') if p.strip()]
                        for paragraph in paragraphs[:20]:  # Limit to first 20 paragraphs
                            if len(paragraph) > 30:  # Only include substantial paragraphs
                                structured_content.append({
                                    "type": "paragraph",
                                    "content": paragraph
                                })
                
                # If still no content, add a fallback message
                if not structured_content:
                    structured_content.append({
                        "type": "paragraph",
                        "content": "No content could be extracted from this page."
                    })
                
                # For debugging/development, add metadata
                structured_content.append({
                    "type": "paragraph",
                    "content": f"Scraped at: {time.strftime('%Y-%m-%d %H:%M:%S')} using Playwright"
                })
                
                # Extract images (up to 5 main images)
                images = []
                if main_content:
                    imgs = main_content.find_all('img')
                    for i, img in enumerate(imgs):
                        if i >= 5:  # Limit to 5 images
                            break
                            
                        src = img.get('src', '')
                        if not src:
                            continue
                            
                        # Convert relative URLs to absolute
                        if not src.startswith(('http://', 'https://')):
                            # Use page's base URL
                            base_url = await page.evaluate("document.baseURI")
                            if base_url:
                                from urllib.parse import urljoin
                                src = urljoin(base_url, src)
                            else:
                                from urllib.parse import urljoin
                                src = urljoin(url, src)
                        
                        alt = img.get('alt', 'Image')
                        
                        images.append({
                            "id": f"img_{i}",
                            "src": src,
                            "alt": alt
                        })
                
                # Create the result object
                result = {
                    "title": title,
                    "structured_content": structured_content,
                    "images": images
                }
                
                # Save as JSON
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2)
                
                print(f"Successfully scraped {url} with {len(structured_content)} content blocks and {len(images)} images")
                return 0
            
            except Exception as e:
                print(f"Error during page processing: {e}")
                raise
            
            finally:
                # Close the browser
                await browser.close()
    
    except Exception as e:
        print(f"Error in Playwright scraping: {e}")
        
        # Create error result
        error_result = {
            "title": f"Error: Could not scrape {url}",
            "structured_content": [{
                "type": "paragraph",
                "content": f"Failed to scrape content: {str(e)}"
            }],
            "images": []
        }
        
        # Save error result
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(error_result, f, indent=2)
        
        return 1

def main():
    if len(sys.argv) != 3:
        print("Usage: python scrape_js.py <url> <output_path>")
        sys.exit(1)
    
    url = sys.argv[1]
    output_path = sys.argv[2]
    
    # Run the async function
    exit_code = asyncio.run(scrape_with_playwright(url, output_path))
    sys.exit(exit_code)

if __name__ == "__main__":
    main()