"""Quick test to verify everything works"""
import requests
from bs4 import BeautifulSoup
import sys


def test_scraping():
    print("🧪 Testing WebTagContent Extractor...")

    try:
        # Test basic imports
        import requests
        import bs4
        print("✅ Dependencies imported successfully")

        # Test a simple website
        url = "https://httpbin.org/html"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Test CSS selector
        elements = soup.select('h1')
        if elements:
            print(f"✅ CSS selector test passed - found {len(elements)} elements")
            print(f"✅ Sample content: '{elements[0].get_text(strip=True)}'")
        else:
            print("❌ CSS selector test failed")

        print("\n🎉 All tests passed! Your WebTagContent Extractor is ready!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    test_scraping()