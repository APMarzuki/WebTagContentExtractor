"""
Stealth test for Milipol with anti-bot evasion
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

def stealth_milipol_test():
    """Test Milipol with stealth techniques"""

    print("🕵️‍♂️ Starting stealth test for Milipol...")

    # Enhanced stealth options
    chrome_options = Options()

    # Remove automation indicators
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    # Normal browser appearance
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Remove headless for better stealth
    # chrome_options.add_argument("--headless")  # Commented out for better stealth

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Execute stealth scripts
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        print("🌐 Loading Milipol with stealth mode...")
        driver.get("https://www.milipol.com/en/catalogue")

        # Wait longer for page load
        time.sleep(8)

        # Check if we're blocked
        page_source = driver.page_source
        if "blocked" in page_source.lower() or "unable to access" in page_source.lower():
            print("❌ Still blocked by anti-bot protection")
            print("💡 Trying manual inspection method...")
            return False
        else:
            print("✅ Possibly bypassed protection! Checking for content...")

            # Quick content check
            if "exhibitor" in page_source.lower() or "catalogue" in page_source.lower():
                print("🎉 Found exhibition content!")

                # Try to find exhibitors
                elements = driver.find_elements(By.CSS_SELECTOR, "div, span, a, h1, h2, h3, h4")
                potential_exhibitors = []

                for elem in elements[:50]:  # Check first 50 elements
                    text = elem.text.strip()
                    if text and len(text) > 3 and len(text) < 100:
                        # Look for company-like patterns
                        if any(word in text.lower() for word in ['inc', 'ltd', 'gmbh', 'corp', 'company', 'group']):
                            potential_exhibitors.append(text)
                        elif text.istitle() and len(text.split()) <= 5:
                            potential_exhibitors.append(text)

                if potential_exhibitors:
                    print(f"🎯 Found {len(potential_exhibitors)} potential exhibitors:")
                    for exhibitor in potential_exhibitors[:10]:
                        print(f"   • {exhibitor}")
                    return True
                else:
                    print("ℹ️  No clear exhibitor names found automatically")
                    return False
            else:
                print("❌ No exhibition content found")
                return False

    except Exception as e:
        print(f"💥 Error: {e}")
        return False
    finally:
        driver.quit()
        print("✅ Browser closed")

def manual_method():
    """Guide for manual extraction"""
    print("\n" + "=" * 60)
    print("📋 MANUAL EXTRACTION METHOD:")
    print("Since automated access is blocked, here's the manual approach:")
    print("")
    print("1. 📱 Visit in your regular browser: https://www.milipol.com/en/catalogue")
    print("2. 🕵️‍♂️ Manually inspect the page (F12 → Elements tab)")
    print("3. 🔍 Look for exhibitor names and their HTML structure")
    print("4. 📝 Note the CSS classes/attributes around company names")
    print("5. 🎯 Share what you find for custom selector")
    print("")
    print("💡 Look for patterns like:")
    print("   - Company names inside <div class='company-name'>")
    print("   - Cards with <div class='card'> containing company names")
    print("   - Data attributes like data-company='Company Name'")
    print("=" * 60)

if __name__ == "__main__":
    success = stealth_milipol_test()
    if not success:
        manual_method()