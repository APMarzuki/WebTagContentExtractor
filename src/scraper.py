"""
Enhanced Web Scraper with JavaScript content handling
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
from urllib.parse import urljoin, urlparse

class WebTagScraper:
    def __init__(self):
        self.session = requests.Session()
        self.setup_session()

    def setup_session(self):
        """Configure HTTP session with headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

    def scrape(self, url, css_selector, attribute='text', contains_text=None, timeout=30, delay=0):
        """
        Extract content from web page using CSS selector

        Args:
            url: Target website URL
            css_selector: CSS selector to find elements
            attribute: Attribute to extract ('text', 'class', 'href', etc.)
            contains_text: Filter elements containing specific text
            timeout: Request timeout in seconds
            delay: Additional delay in seconds for JavaScript content
        """
        try:
            print(f"🔄 Downloading content from: {url}")

            # Add delay if specified (for JavaScript content)
            if delay > 0:
                print(f"⏳ Waiting {delay} seconds for content to load...")
                time.sleep(delay)

            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Debug: Show page title to verify we got the page
            title = soup.find('title')
            if title:
                print(f"📄 Page title: {title.get_text(strip=True)}")

            elements = soup.select(css_selector)

            if not elements:
                print(f"❌ No elements found with selector: {css_selector}")
                print("💡 Try these alternatives:")
                print("   - Simpler selector like 'div' or 'a'")
                print("   - Check if content loads via JavaScript")
                print("   - Try the page in browser to see actual content")
                return []

            extracted_data = []
            for element in elements:
                try:
                    # Apply text filter if specified
                    if contains_text and contains_text not in str(element):
                        continue

                    # Extract content based on attribute
                    content = self._extract_attribute(element, attribute)
                    if content and content.strip():
                        extracted_data.append(content)

                except Exception as e:
                    logging.warning(f"Error processing element: {e}")
                    continue

            print(f"✅ Found {len(extracted_data)} items matching the criteria")

            # Show sample of what was found
            if extracted_data:
                sample = extracted_data[:3]  # Show first 3 items
                print(f"📋 Sample results: {sample}")

            return extracted_data

        except requests.RequestException as e:
            print(f"❌ Network error: {e}")
            return []
        except Exception as e:
            print(f"❌ Scraping error: {e}")
            return []

    def _extract_attribute(self, element, attribute):
        """Extract specific attribute from element"""
        if attribute == 'text':
            return element.get_text(strip=True)
        elif attribute in element.attrs:
            return element[attribute]
        elif attribute == 'html':
            return str(element)
        else:
            return element.get(attribute, '')

    def scrape_with_retry(self, url, css_selector, attribute='text', retries=2, delay=3):
        """
        Try scraping with increasing delays for JavaScript content
        """
        for attempt in range(retries + 1):
            print(f"🔄 Attempt {attempt + 1}/{retries + 1}")
            result = self.scrape(url, css_selector, attribute, delay=delay * attempt)
            if result:
                return result
            elif attempt < retries:
                print(f"⏳ Retrying with longer delay...")

        return []

# Test function to verify the scraper
def test_scraper():
    """Test the scraper with different websites"""
    scraper = WebTagScraper()

    test_cases = [
        {
            'name': 'HTTPBin Test (Should Work)',
            'url': 'https://httpbin.org/html',
            'selector': 'h1, p',
            'attribute': 'text'
        },
        {
            'name': 'Enforce Tac Exhibitors (JavaScript - May Fail)',
            'url': 'https://www.enforcetac.com/en/exhibitors-products/find-exhibitors',
            'selector': '[data-testid="company-results-item"]',
            'attribute': 'aria-label',
            'delay': 5  # Longer delay for JavaScript
        },
        {
            'name': 'Simple Test Site',
            'url': 'https://example.com',
            'selector': 'h1, p',
            'attribute': 'text'
        }
    ]

    for test in test_cases:
        print(f"\n🧪 Testing: {test['name']}")
        print(f"🔗 URL: {test['url']}")
        print(f"🎯 Selector: {test['selector']}")

        result = scraper.scrape(
            test['url'],
            test['selector'],
            test['attribute'],
            delay=test.get('delay', 0)
        )

        if result:
            print(f"✅ SUCCESS: Found {len(result)} items")
            print(f"📋 Sample: {result[:2]}")
        else:
            print(f"❌ FAILED: No results (likely JavaScript content)")

if __name__ == "__main__":
    test_scraper()