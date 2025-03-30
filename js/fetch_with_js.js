const puppeteer = require('puppeteer');
const fs = require('fs');

// Get command line arguments
const url = process.argv[2];
const outputPath = process.argv[3];

if (!url || !outputPath) {
  console.error('Usage: node fetch_with_js.js <url> <output_path>');
  process.exit(1);
}

(async () => {
  try {
    console.log(`Fetching content from ${url} with JavaScript support...`);
    
    // Launch a headless browser
    const browser = await puppeteer.launch({
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox'] // Needed on some Linux systems
    });
    
    const page = await browser.newPage();
    
    // Set a reasonable viewport
    await page.setViewport({ width: 1280, height: 800 });
    
    // Setup timeout - 30 seconds
    await page.setDefaultNavigationTimeout(30000);
    
    // Navigate to the URL
    await page.goto(url, { waitUntil: 'networkidle2' });
    
    // Wait for content to load (additional wait)
    await page.waitForTimeout(2000);
    
    // Take a screenshot for debugging
    await page.screenshot({ path: `${outputPath}.png` });
    
    // Extract page content
    const result = await page.evaluate(() => {
      // Get the page title
      const title = document.title;
      
      // Get all text content
      const bodyText = document.body.innerText;
      
      // Try to find main content containers
      const mainContentSelectors = [
        'article', 'main', 'div.content', 'div#content', 
        'div.main', 'div.article', 'div.post'
      ];
      
      let mainContent = null;
      for (const selector of mainContentSelectors) {
        const element = document.querySelector(selector);
        if (element) {
          mainContent = element.innerText;
          break;
        }
      }
      
      // Extract visible paragraphs
      const paragraphs = [];
      document.querySelectorAll('p').forEach(p => {
        // Check if the paragraph is visible
        const style = window.getComputedStyle(p);
        if (style.display !== 'none' && style.visibility !== 'hidden' && p.innerText.trim()) {
          paragraphs.push(p.innerText.trim());
        }
      });
      
      // Extract headings
      const headings = [];
      document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(h => {
        const style = window.getComputedStyle(h);
        if (style.display !== 'none' && style.visibility !== 'hidden' && h.innerText.trim()) {
          headings.push({
            level: parseInt(h.tagName.substring(1)),
            text: h.innerText.trim()
          });
        }
      });
      
      // Extract images
      const images = [];
      document.querySelectorAll('img').forEach(img => {
        const style = window.getComputedStyle(img);
        if (style.display !== 'none' && style.visibility !== 'hidden' && 
            img.src && img.height > 50 && img.width > 50) { // Filter out tiny images
          images.push({
            src: img.src,
            alt: img.alt || '',
            width: img.width,
            height: img.height
          });
        }
      });
      
      // Extract lists
      const lists = [];
      document.querySelectorAll('ul, ol').forEach(list => {
        const style = window.getComputedStyle(list);
        if (style.display !== 'none' && style.visibility !== 'hidden') {
          const items = [];
          list.querySelectorAll('li').forEach(li => {
            if (li.innerText.trim()) {
              items.push(li.innerText.trim());
            }
          });
          
          if (items.length > 0) {
            lists.push({
              type: list.tagName.toLowerCase(), // 'ul' or 'ol'
              items: items
            });
          }
        }
      });
      
      // Combine into result object
      return {
        title,
        bodyText,
        mainContent,
        paragraphs,
        headings,
        images,
        lists,
        htmlContent: document.documentElement.outerHTML
      };
    });
    
    // Save the HTML content for debugging
    fs.writeFileSync(`${outputPath}.html`, result.htmlContent);
    
    // Process and structure the content
    const structured = {
      title: result.title,
      structured_content: []
    };
    
    // Add headings to structured content
    result.headings.forEach(heading => {
      structured.structured_content.push({
        type: `h${heading.level}`,
        content: heading.text
      });
    });
    
    // Add paragraphs to structured content
    result.paragraphs.forEach(paragraph => {
      structured.structured_content.push({
        type: 'paragraph',
        content: paragraph
      });
    });
    
    // Add lists to structured content
    result.lists.forEach(list => {
      structured.structured_content.push({
        type: 'list',
        list_type: list.type,
        items: list.items
      });
    });
    
    // If no structured content was found but there's text in the body
    if (structured.structured_content.length === 0 && result.bodyText) {
      // Split body text into paragraphs
      const bodyTextParagraphs = result.bodyText.split('\n\n')
        .filter(p => p.trim().length > 0)
        .map(p => p.trim());
      
      if (bodyTextParagraphs.length > 0) {
        bodyTextParagraphs.forEach(paragraph => {
          structured.structured_content.push({
            type: 'paragraph',
            content: paragraph
          });
        });
      } else if (result.bodyText.trim()) {
        // If no paragraphs, use the whole body text
        structured.structured_content.push({
          type: 'paragraph',
          content: result.bodyText.trim()
        });
      }
    }
    
    // If still no structured content, add a fallback message
    if (structured.structured_content.length === 0) {
      structured.structured_content.push({
        type: 'paragraph',
        content: 'No content could be extracted from this page.'
      });
    }
    
    // Save structured content to the output file
    fs.writeFileSync(outputPath, JSON.stringify(structured, null, 2));
    
    console.log(`Content successfully extracted and saved to ${outputPath}`);
    
    // Close the browser
    await browser.close();
    
    process.exit(0);
  } catch (error) {
    console.error('Error:', error);
    
    // Create an error result
    const errorResult = {
      title: 'Error fetching content',
      structured_content: [{
        type: 'paragraph',
        content: `Error fetching content: ${error.message}`
      }]
    };
    
    // Save error result to output file
    fs.writeFileSync(outputPath, JSON.stringify(errorResult, null, 2));
    
    process.exit(1);
  }
})();