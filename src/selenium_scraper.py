"""
Enhanced Selenium Scraper with Exhibitor Directory Specialization
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging

class EnhancedSeleniumScraper:
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
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print("✅ Enhanced Selenium Chrome driver initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Enhanced Selenium driver: {e}")
            raise

    def handle_load_more_exhibitors(self, max_clicks=20):
        """
        Specialized method for exhibitor directories with Load More buttons

        Args:
            max_clicks: Maximum number of Load More clicks
        """
        print(f"🔄 Handling exhibitor directory Load More (max {max_clicks} clicks)...")

        click_count = 0
        last_company_count = 0
        no_new_companies_count = 0

        while click_count < max_clicks:
            click_count += 1

            # Count current companies before clicking
            current_companies = self.driver.find_elements(By.CSS_SELECTOR, '.exhibitor-name, .company-name, h2, h3, [class*="exhibitor"], [class*="company"]')
            current_count = len(current_companies)
            print(f"📊 Before click {click_count}: {current_count} companies")

            # Try to find and click Load More button
            load_more_clicked = False
            load_more_selectors = [
                'button[class*="load"]',
                'button[class*="more"]',
                'a[class*="load"]',
                'a[class*="more"]',
                '.load-more',
                '.show-more',
                'button:contains("Load")',
                'button:contains("More")',
                'button:contains("Show")',
                '[data-load-more]',
                '.btn[class*="more"]'
            ]

            for selector in load_more_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            print(f"🔄 Clicking Load More: {selector}")
                            self.driver.execute_script("arguments[0].click();", button)
                            load_more_clicked = True

                            # Wait for new content to load
                            time.sleep(4)
                            break
                    if load_more_clicked:
                        break
                except:
                    continue

            # Count companies after clicking
            new_companies = self.driver.find_elements(By.CSS_SELECTOR, '.exhibitor-name, .company-name, h2, h3, [class*="exhibitor"], [class*="company"]')
            new_count = len(new_companies)

            print(f"📊 After click {click_count}: {new_count} companies")

            # Check if we got new companies
            if new_count > current_count:
                print(f"✅ Loaded {new_count - current_count} new companies")
                no_new_companies_count = 0
            else:
                no_new_companies_count += 1
                print("⚠️ No new companies loaded")

            # Break conditions
            if not load_more_clicked:
                print("✅ No more Load More buttons found")
                break

            if no_new_companies_count >= 2:
                print("✅ No new companies for 2 consecutive clicks - stopping")
                break

            if new_count >= 691:  # Target count reached
                print("🎯 Reached target company count!")
                break

        print(f"✅ Completed Load More process: {click_count} clicks")
        return click_count

    def scrape_exhibitor_directory(self, url, css_selector, attribute='text', contains_text=None, max_load_more=15):
        """
        Specialized method for exhibitor directories

        Args:
            url: Exhibitor directory URL
            css_selector: CSS selector for company names
            attribute: Attribute to extract
            contains_text: Filter text
            max_load_more: Maximum Load More clicks
        """
        try:
            print(f"🚀 Opening exhibitor directory: {url}")
            self.driver.get(url)

            # Wait for initial load
            print("⏳ Waiting for initial page load...")
            time.sleep(5)

            # Wait for initial companies
            print(f"⏳ Waiting for initial companies: {css_selector}")
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
            )

            # Handle Load More buttons
            self.handle_load_more_exhibitors(max_load_more)

            # Final scroll to ensure all content is loaded
            print("🔄 Final scroll to load any remaining content...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            # Extract all companies
            elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)

            if not elements:
                print(f"❌ No companies found with selector: {css_selector}")
                return []

            print(f"✅ Found {len(elements)} elements total")

            extracted_data = []
            for element in elements:
                try:
                    if attribute == 'text':
                        content = element.text.strip()
                    else:
                        content = element.get_attribute(attribute)

                    if content and (not contains_text or contains_text in content):
                        extracted_data.append(content)

                except Exception as e:
                    print(f"⚠️ Error processing element: {e}")
                    continue

            # Remove duplicates while preserving order
            unique_data = []
            for item in extracted_data:
                if item not in unique_data:
                    unique_data.append(item)

            print(f"🎯 Extracted {len(unique_data)} unique companies")

            # Show sample results
            if unique_data:
                sample = unique_data[:10]
                print(f"📋 Sample companies: {sample}")

            return unique_data

        except Exception as e:
            print(f"❌ Exhibitor directory scraping error: {e}")
            return []

    def handle_pagination(self, max_pages=20):
        """
        Handle pagination by clicking next buttons or load more
        """
        print(f"🔄 Handling pagination (max {max_pages} pages)...")

        page_count = 0

        while page_count < max_pages:
            page_count += 1
            print(f"📄 Processing page {page_count}...")

            # Wait for content to load
            time.sleep(3)

            # Try to find and click "Load More" or "Next" buttons
            load_more_selectors = [
                'button[class*="load"]',
                'button[class*="more"]',
                'a[class*="load"]',
                'a[class*="more"]',
                '.load-more',
                '.show-more',
                '.next',
                '.pagination-next',
                'button:contains("Load")',
                'button:contains("More")',
                'button:contains("Show")',
                'a:contains("Next")',
                'a:contains(">")'
            ]

            clicked = False
            for selector in load_more_selectors:
                try:
                    button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if button.is_displayed() and button.is_enabled():
                        print(f"🔄 Clicking: {selector}")
                        self.driver.execute_script("arguments[0].click();", button)
                        clicked = True
                        time.sleep(3)
                        break
                except:
                    continue

            if not clicked:
                print("✅ No more pages/buttons found")
                break

        print(f"✅ Processed {page_count} pages")
        return page_count

    def scroll_until_no_new_content(self, css_selector, max_scrolls=20, scroll_pause=3):
        """
        Scroll until no new elements are loaded
        """
        print(f"🔄 Scrolling to load all content for: {css_selector}")

        last_element_count = 0
        same_count_streak = 0
        scroll_attempts = 0

        while scroll_attempts < max_scrolls and same_count_streak < 3:
            scroll_attempts += 1

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            print(f"📜 Scroll {scroll_attempts}/{max_scrolls} - Waiting {scroll_pause}s...")
            time.sleep(scroll_pause)

            current_elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)
            current_count = len(current_elements)

            print(f"📊 Element count: {current_count} (previous: {last_element_count})")

            if current_count == last_element_count:
                same_count_streak += 1
                print(f"✅ Count stable {same_count_streak}/3")
            else:
                same_count_streak = 0

            last_element_count = current_count

        print(f"✅ Final element count: {last_element_count}")
        return last_element_count

    def scrape_with_complete_coverage(self, url, css_selector, attribute='text', contains_text=None,
                                    timeout=30, max_scrolls=25, scroll_pause=3, handle_pagination=True):
        """
        Comprehensive scraping with pagination and scroll support
        """
        try:
            print(f"🚀 Opening browser: {url}")
            self.driver.get(url)

            time.sleep(5)

            print(f"⏳ Waiting for initial elements: {css_selector}")
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
            )

            if handle_pagination:
                self.handle_pagination(max_pages=10)

            final_count = self.scroll_until_no_new_content(css_selector, max_scrolls, scroll_pause)

            elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)

            if not elements:
                print(f"❌ No elements found with selector: {css_selector}")
                return []

            print(f"✅ Found {len(elements)} elements after comprehensive loading")

            extracted_data = []
            for element in elements:
                try:
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

            if extracted_data:
                sample = extracted_data[:5]
                print(f"📋 Sample: {sample}")

            return extracted_data

        except TimeoutException:
            print(f"❌ Timeout waiting for elements: {css_selector}")
            return []
        except Exception as e:
            print(f"❌ Comprehensive scraping error: {e}")
            return []

    def scrape(self, url, css_selector, attribute='text', contains_text=None, timeout=30):
        """Standard scrape (backward compatibility)"""
        return self.scrape_with_complete_coverage(url, css_selector, attribute, contains_text, timeout, handle_pagination=False)

    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("✅ Enhanced Selenium browser closed")

    def __del__(self):
        """Ensure browser closes on destruction"""
        self.close()

# Test function for InfoSecurity Europe Exhibitor Directory
def test_infosecurity_exhibitors_complete():
    """Test complete exhibitor directory scraping"""
    scraper = EnhancedSeleniumScraper(headless=False)

    try:
        print("🧪 Testing Complete Exhibitor Directory Scraping...")

        results = scraper.scrape_exhibitor_directory(
            url="https://www.infosecurityeurope.com/en-gb/exhibitor-directory.html",
            css_selector='.exhibitor-name, .company-name, h2, h3, [class*="exhibitor"], [class*="company"]',
            attribute='text',
            max_load_more=15
        )

        if results:
            print(f"🎉 SUCCESS! Found {len(results)} companies!")
            print(f"📈 Expected: ~691 companies")
            print(f"📊 Coverage: {len(results)}/691 ({len(results)/691*100:.1f}%)")

            for i, company in enumerate(results[:15], 1):
                print(f"  {i}. {company}")

        else:
            print("❌ No companies found")

    finally:
        scraper.close()

if __name__ == "__main__":
    test_infosecurity_exhibitors_complete()