"""
Standalone selector finder for InfoSecurity Europe
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

def manual_selector_finder():
    """Manually find the best selector"""

    print("🎯 Manual Selector Finder for InfoSecurity Europe")
    print("=" * 60)

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get("https://www.infosecurityeurope.com/en-gb/exhibitor-directory/product-directory.html")
        time.sleep(5)

        # Load more content
        for i in range(2):
            try:
                load_more = driver.find_element(By.CSS_SELECTOR, 'a[class*="more"]')
                driver.execute_script("arguments[0].click();", load_more)
                time.sleep(2)
                print(f"📄 Loaded additional content {i+1}")
            except:
                break

        print("\n🔍 MANUAL INSPECTION GUIDE:")
        print("1. The page is now loaded in the background")
        print("2. Please manually inspect the page in a regular browser:")
        print("3. Go to: https://www.infosecurityeurope.com/en-gb/exhibitor-directory/product-directory.html")
        print("4. Right-click on a COMPANY NAME (not product)")
        print("5. Click 'Inspect' and look for:")
        print("   - Class names like 'company-name', 'exhibitor-title'")
        print("   - Data attributes like 'data-company'")
        print("   - HTML structure around company names")
        print("\n6. Come back and enter the best selector below:")

        # Show some sample elements to help
        print("\n📋 Some elements found on page:")
        sample_elements = driver.find_elements(By.CSS_SELECTOR, 'h3, h2, [class*="title"], [class*="name"]')[:10]
        for i, elem in enumerate(sample_elements, 1):
            text = elem.text.strip()
            if text:
                classes = elem.get_attribute('class') or ''
                print(f"  {i}. '{text}' - classes: '{classes}'")

        return True

    finally:
        driver.quit()

if __name__ == "__main__":
    manual_selector_finder()

    print("\n" + "=" * 60)
    print("💡 Based on manual inspection, try these selectors in your app:")
    print("   1. Try: '.exhibitor-company'")
    print("   2. Try: '.company-title'")
    print("   3. Try: '[data-company-name]'")
    print("   4. Try: '.exhibitor-item h3'")
    print("=" * 60)