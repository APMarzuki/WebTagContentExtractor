"""
Selenium-based scraper for JavaScript-rendered content
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging


class SeleniumScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.setup_driver()

    def setup_driver(self):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print("✅ Selenium Chrome driver initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Selenium driver: {e}")
            raise

    def scrape(self, url, css_selector, attribute='text', contains_text=None, timeout=30, wait_for_element=None):
        """
        Extract content from JavaScript-rendered pages

        Args:
            url: Website URL
            css_selector: CSS selector to find elements
            attribute: Attribute to extract
            contains_text: Filter elements containing text
            timeout: Maximum wait time in seconds
            wait_for_element: Specific element to wait for before scraping
        """
        try:
            print(f"🚀 Opening browser: {url}")
            self.driver.get(url)

            # Wait for page to load
            print("⏳ Waiting for page to load...")
            time.sleep(3)

            # Wait for specific element if provided
            if wait_for_element:
                print(f"⏳ Waiting for element: {wait_for_element}")
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element))
                )

            # Wait for the target elements
            print(f"⏳ Waiting for elements with selector: {css_selector}")
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
            )

            # Find elements
            elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)

            if not elements:
                print(f"❌ No elements found with selector: {css_selector}")
                return []

            print(f"✅ Found {len(elements)} elements")

            extracted_data = []
            for element in elements:
                try:
                    # Get element text or attribute
                    if attribute == 'text':
                        content = element.text.strip()
                    else:
                        content = element.get_attribute(attribute)

                    if content and (not contains_text or contains_text in content):
                        extracted_data.append(content)

                except Exception as e:
                    print(f"⚠️ Error processing element: {e}")
                    continue

            print(f"🎯 Extracted {len(extracted_data)} items")

            # Show sample results
            if extracted_data:
                sample = extracted_data[:5]
                print(f"📋 Sample: {sample}")

            return extracted_data

        except Exception as e:
            print(f"❌ Selenium scraping error: {e}")
            return []

    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("✅ Browser closed")

    def __del__(self):
        """Ensure browser closes on destruction"""
        self.close()


# Test function
def test_selenium():
    """Test Selenium scraper"""
    scraper = SeleniumScraper(headless=False)  # Set to False to see browser

    try:
        print("🧪 Testing Selenium with Enforce Tac...")
        results = scraper.scrape(
            url="https://www.enforcetac.com/en/exhibitors-products/find-exhibitors",
            css_selector='[data-testid="company-results-item"]',
            attribute='aria-label',
            timeout=20,
            wait_for_element='[data-testid="company-results-item"]'
        )

        if results:
            print(f"🎉 SUCCESS! Found {len(results)} exhibitors!")
            for i, company in enumerate(results[:10], 1):
                print(f"  {i}. {company}")
        else:
            print("❌ No results found")

    finally:
        scraper.close()


if __name__ == "__main__":
    test_selenium()