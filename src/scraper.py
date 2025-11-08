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

    def scrape_exhibition_exhibitors(self, url, css_selector, attribute='text', fallback_selectors=None):
        """
        Specialized method for exhibition websites with multiple selector fallbacks
        """
        if fallback_selectors is None:
            fallback_selectors = [
                css_selector,
                '.m-exhibitors-list_list_items_item_header_title',
                'h2[class*="title"]',
                '.js-librarylink-entry',
                '[class*="exhibitor"]',
                '[class*="company"]',
                'h2, h3, h4'
            ]

        print(f"🎪 Scraping exhibition: {url}")

        for selector in fallback_selectors:
            print(f"🎯 Trying selector: {selector}")
            results = self.scrape(url, selector, attribute, delay=3)

            if results:
                # Filter out UI elements and clean data
                cleaned_results = self._clean_exhibition_data(results)
                if cleaned_results:
                    print(f"✅ Success with selector: {selector}")
                    print(f"📊 Found {len(cleaned_results)} exhibitors")
                    return cleaned_results

        print("❌ No exhibitors found with any selector")
        return []

    def _clean_exhibition_data(self, data):
        """Clean and filter exhibition data"""
        cleaned = []
        ui_indicators = ['search', 'filter', 'loading', 'show', 'hide', 'next', 'previous', 'menu', 'button']

        for item in data:
            if not item or len(item.strip()) < 2:
                continue

            item_lower = item.lower()
            # Skip UI elements and navigation
            if any(indicator in item_lower for indicator in ui_indicators):
                continue

            # Skip very short items or items that look like page numbers
            if len(item.strip()) <= 3 and item.strip().isdigit():
                continue

            cleaned.append(item.strip())

        # Remove duplicates while preserving order
        unique_data = []
        seen = set()
        for item in cleaned:
            if item not in seen:
                seen.add(item)
                unique_data.append(item)

        return unique_data

    def scrape_multiple_pages(self, base_url, css_selector, attribute='text', pages=5, page_param='page'):
        """
        Scrape multiple pages with pagination
        """
        all_data = []

        for page in range(1, pages + 1):
            print(f"📄 Scraping page {page}/{pages}")

            # Construct URL with page parameter
            if '?' in base_url:
                url = f"{base_url}&{page_param}={page}"
            else:
                url = f"{base_url}?{page_param}={page}"

            page_data = self.scrape(url, css_selector, attribute, delay=2)
            all_data.extend(page_data)

            # Small delay between pages to be respectful
            time.sleep(1)

        # Clean and deduplicate
        cleaned_data = self._clean_exhibition_data(all_data)
        print(f"📊 Total unique exhibitors across {pages} pages: {len(cleaned_data)}")
        return cleaned_data

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

    def check_page_content(self, url):
        """
        Diagnostic method to check what content is available on the page
        """
        try:
            print(f"🔍 Analyzing page content: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Get page title
            title = soup.find('title')
            print(f"📄 Page title: {title.get_text(strip=True) if title else 'No title found'}")

            # Count different element types
            elements = {
                'h1': len(soup.find_all('h1')),
                'h2': len(soup.find_all('h2')),
                'h3': len(soup.find_all('h3')),
                'div': len(soup.find_all('div')),
                'span': len(soup.find_all('span')),
                'a': len(soup.find_all('a'))
            }

            print("📊 Element counts:")
            for element, count in elements.items():
                print(f"   {element}: {count}")

            # Show first few h2 elements (common for exhibitor names)
            h2_elements = soup.find_all('h2')[:5]
            if h2_elements:
                print("🔤 Sample h2 elements:")
                for i, h2 in enumerate(h2_elements, 1):
                    print(f"   {i}. {h2.get_text(strip=True)}")

            return True

        except Exception as e:
            print(f"❌ Error analyzing page: {e}")
            return False


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
            'name': 'Example.com',
            'url': 'https://example.com',
            'selector': 'h1, p',
            'attribute': 'text'
        },
        {
            'name': 'International Cyber Expo (Exhibition Test)',
            'url': 'https://www.internationalcyberexpo.com/exhibitors-list',
            'selector': '.m-exhibitors-list_list_items_item_header_title',
            'attribute': 'text',
            'method': 'exhibition'  # Use specialized method
        }
    ]

    for test in test_cases:
        print(f"\n🧪 Testing: {test['name']}")
        print(f"🔗 URL: {test['url']}")
        print(f"🎯 Selector: {test['selector']}")

        if test.get('method') == 'exhibition':
            # Use specialized exhibition method
            result = scraper.scrape_exhibition_exhibitors(
                test['url'],
                test['selector'],
                test['attribute']
            )
        else:
            # Use regular method
            result = scraper.scrape(
                test['url'],
                test['selector'],
                test['attribute'],
                delay=test.get('delay', 0)
            )

        if result:
            print(f"✅ SUCCESS: Found {len(result)} items")
            print(f"📋 Sample: {result[:3]}")
        else:
            print(f"❌ No results found")

            # Run diagnostic for exhibition sites
            if 'cyber' in test['name'].lower():
                print("🔍 Running page analysis...")
                scraper.check_page_content(test['url'])


def test_exhibition_scraping():
    """Test specialized exhibition scraping"""
    scraper = WebTagScraper()

    print("🎪 TESTING EXHIBITION SCRAPING")
    print("=" * 50)

    exhibition_tests = [
        {
            'name': 'International Cyber Expo',
            'url': 'https://www.internationalcyberexpo.com/exhibitors-list',
            'selector': '.m-exhibitors-list_list_items_item_header_title'
        },
        {
            'name': 'Intersec Dubai',
            'url': 'https://intersec.ae.messefrankfurt.com/dubai/en/exhibitor-search/exhibitor-search.html',
            'selector': '.ex-exhibitor-search-result-item_copy span'
        }
    ]

    for test in exhibition_tests:
        print(f"\n🎯 Testing: {test['name']}")
        results = scraper.scrape_exhibition_exhibitors(
            test['url'],
            test['selector']
        )

        if results:
            print(f"✅ Found {len(results)} exhibitors")
            for i, company in enumerate(results[:5], 1):
                print(f"   {i}. {company}")
            if len(results) > 5:
                print(f"   ... and {len(results) - 5} more")
        else:
            print("❌ No results - likely requires JavaScript/Selenium")


if __name__ == "__main__":
    print("🌐 WebTag Scraper - Enhanced Edition")
    print("Choose test mode:")
    print("1. Basic functionality test")
    print("2. Exhibition scraping test")

    choice = input("Enter choice (1 or 2): ").strip()

    if choice == "2":
        test_exhibition_scraping()
    else:
        test_scraper()