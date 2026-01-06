import os
import json
import time
import random
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_faq_links(base_url):
    with sync_playwright() as p:
        # 1. Launch browser (headless=True for production, False to debug)
        browser = p.chromium.launch(headless=True)
        
        # 2. Set a realistic User-Agent
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        
        page = context.new_page()
        print(f"\n\nNavigating to: {base_url}")
        
        try:
            # 3. Navigate and wait for the network to be idle (important for React/Vue sites)
            page.goto(base_url, wait_until="networkidle")
            
            # 4. Randomized human-like delay
            time.sleep(random.uniform(2, 5)) 
            
            # Get the rendered HTML
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # 5. Extract Links (Binance FAQ links usually follow a pattern)
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if "/en/support/faq/" in href:
                    full_url = f"https://www.binance.com{href}" if href.startswith('/') else href
                    links.append(full_url)
            
            return list(set(links)) # Return unique links
            
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            browser.close()

def scrape_article_content(url, page):
    """Navigates to a specific FAQ and extracts structured data."""
    print(f"Scraping: {url}")
    
    try:
        page.goto(url, wait_until="networkidle")
        time.sleep(random.uniform(1.5, 3)) # Polite delay
        
        soup = BeautifulSoup(page.content(), 'html.parser')
        
        # Note: Selectors might change, but typically FAQ titles are in <h1> 
        # and content is in a specific div class.
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "No Title"
        
        # Logic to grab the main article body (removing navs, footers, etc.)
        # Binance articles often live in a 'div' with specific typography classes
        content_div = soup.find('div', {'class': 'css-18z6mjt'}) # Example class
        if not content_div:
            # Fallback to general article body if specific class is missed
            content_div = soup.find('article') or soup.find('main')
            
        content = content_div.get_text(separator="\n", strip=True) if content_div else ""

        return {
            "url": url,
            "title": title,
            "content": content,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        print(f"Failed to scrape {url}: {e}")
        return None
    
def run_etl(url_list):
    all_data = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        for url in url_list[:5]: 
            data = scrape_article_content(url, page)
            if data:
                all_data.append(data)
        
        browser.close()
    
    # Save as JSON (The ETL 'Load' step)
    if not os.path.exists('./json'):
        os.makedirs('./json')
    with open('./json/binance_faq_data.json', 'wb') as f:
        f.write(json.dumps(all_data, indent=4, ensure_ascii=False).encode('utf8'))
    
    print(f"Successfully saved {len(all_data)} articles to binance_faq_data.json")



# Get all links
faq_main_url = "https://www.binance.com/en/support/faq"
article_urls = scrape_faq_links(faq_main_url)

print(f"\nFound {len(article_urls)} articles.")
for link in article_urls[:5]: # Print first 5
    print(f'\t{link}')

# Scrape content inside
run_etl(article_urls)