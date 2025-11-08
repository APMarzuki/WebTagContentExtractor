#!/usr/bin/env python3
"""
WebTagContent Extractor - CLI Main Entry Point
"""

import argparse
import sys
import os
import json

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scraper import WebTagScraper
from src.selenium_scraper import EnhancedSeleniumScraper as SeleniumScraper
from src.exporter import DataExporter


def load_presets():
    """Load scraping presets from JSON file"""
    try:
        presets_path = os.path.join(os.path.dirname(__file__), 'presets.json')
        with open(presets_path, 'r', encoding='utf-8') as f:
            return json.load(f)['presets']
    except Exception as e:
        print(f"⚠️ Could not load presets: {e}")
        return []


def list_presets():
    """Display available presets"""
    presets = load_presets()
    if not presets:
        print("❌ No presets available")
        return

    print("\n🎪 AVAILABLE SCRAPING PRESETS:")
    print("=" * 60)
    for i, preset in enumerate(presets, 1):
        print(f"{i:2d}. {preset['name']}")
        print(f"    📍 {preset['url']}")
        print(f"    🎯 Selector: {preset['selector']}")
        print(f"    🏷️  Attribute: {preset['attribute']}")
        print(f"    ⚡ Mode: {preset['mode']}")
        print(f"    📝 {preset['description']}")
        print()


def get_preset_by_name(name):
    """Get preset by name"""
    presets = load_presets()
    for preset in presets:
        if preset['name'].lower() == name.lower():
            return preset
    return None


def scrape_with_preset(preset):
    """Scrape using a preset configuration"""
    print(f"🎪 Using preset: {preset['name']}")
    print(f"🔗 URL: {preset['url']}")
    print(f"🎯 Selector: {preset['selector']}")
    print(f"🏷️  Attribute: {preset['attribute']}")
    print(f"⚡ Mode: {preset['mode']}")

    if preset['mode'] == 'selenium':
        scraper = SeleniumScraper(headless=True)
        try:
            # Use specialized exhibition method for Selenium
            if 'exhibition' in preset['name'].lower() or 'exhibitor' in preset['name'].lower():
                data = scraper.scrape_exhibition_exhibitors(
                    preset['url'],
                    preset['selector'],
                    preset['attribute']
                )
            else:
                data = scraper.scrape(
                    preset['url'],
                    preset['selector'],
                    preset['attribute'],
                    timeout=30
                )
        finally:
            scraper.close()
    else:
        scraper = WebTagScraper()
        # Use specialized exhibition method for simple scraper
        if 'exhibition' in preset['name'].lower() or 'exhibitor' in preset['name'].lower():
            data = scraper.scrape_exhibition_exhibitors(
                preset['url'],
                preset['selector'],
                preset['attribute']
            )
        else:
            data = scraper.scrape(
                preset['url'],
                preset['selector'],
                preset['attribute'],
                delay=5
            )

    return data


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description='🎪 WebTagContent Extractor - Extract content from HTML tags with exhibition support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic scraping
  python main.py https://example.com "h1, p" -o output.csv

  # Use a preset
  python main.py --preset "International Cyber Expo - All Exhibitors"

  # List all presets
  python main.py --list-presets

  # Exhibition scraping with Selenium
  python main.py https://www.internationalcyberexpo.com/exhibitors-list ".m-exhibitors-list_list_items_item_header_title" --mode selenium

  # Multiple pages
  python main.py https://example.com/exhibitors "h2" --pages 5 --page-param page
        """
    )

    # Main arguments
    parser.add_argument('url', nargs='?', help='Website URL to scrape')
    parser.add_argument('selector', nargs='?', help='CSS selector for target elements')

    # Preset mode
    parser.add_argument('-p', '--preset', help='Use a predefined scraping preset')
    parser.add_argument('-l', '--list-presets', action='store_true',
                        help='List all available presets')

    # Output options
    parser.add_argument('-o', '--output', default='extracted_data.csv',
                        help='Output filename (default: extracted_data.csv)')
    parser.add_argument('-f', '--format', choices=['csv', 'json', 'txt'], default='csv',
                        help='Output format (default: csv)')

    # Extraction options
    parser.add_argument('-a', '--attribute', default='text',
                        help='Attribute to extract (text, class, href, etc.)')
    parser.add_argument('-m', '--mode', choices=['simple', 'selenium', 'auto'], default='auto',
                        help='Scraping mode (default: auto)')

    # Advanced options
    parser.add_argument('--pages', type=int, default=1,
                        help='Number of pages to scrape (for pagination)')
    parser.add_argument('--page-param', default='page',
                        help='URL parameter name for pagination (default: page)')
    parser.add_argument('--delay', type=float, default=2,
                        help='Delay between requests in seconds (default: 2)')
    parser.add_argument('--timeout', type=int, default=30,
                        help='Request timeout in seconds (default: 30)')
    parser.add_argument('--headless', action='store_true', default=True,
                        help='Run browser in headless mode (Selenium only)')

    args = parser.parse_args()

    # Handle list presets
    if args.list_presets:
        list_presets()
        return

    # Handle preset mode
    if args.preset:
        preset = get_preset_by_name(args.preset)
        if not preset:
            print(f"❌ Preset '{args.preset}' not found")
            print("💡 Use --list-presets to see available presets")
            sys.exit(1)

        data = scrape_with_preset(preset)

    # Handle manual mode
    elif args.url and args.selector:
        print(f"🎯 Manual scraping mode")
        print(f"🔗 URL: {args.url}")
        print(f"🎯 Selector: {args.selector}")
        print(f"🏷️  Attribute: {args.attribute}")
        print(f"⚡ Mode: {args.mode}")

        if args.mode == 'selenium' or (args.mode == 'auto' and args.pages > 1):
            # Use Selenium for JavaScript-heavy sites or multi-page scraping
            print("🚀 Using Selenium mode...")
            scraper = SeleniumScraper(headless=args.headless)
            try:
                if args.pages > 1:
                    # Handle multi-page scraping with Selenium
                    all_data = []
                    for page in range(1, args.pages + 1):
                        print(f"📄 Processing page {page}/{args.pages}")
                        page_url = f"{args.url}?{args.page_param}={page}" if '?' in args.url else f"{args.url}?{args.page_param}={page}"
                        page_data = scraper.scrape(
                            page_url,
                            args.selector,
                            args.attribute,
                            timeout=args.timeout
                        )
                        all_data.extend(page_data)
                        time.sleep(args.delay)
                    data = all_data
                else:
                    # Single page with Selenium
                    data = scraper.scrape(
                        args.url,
                        args.selector,
                        args.attribute,
                        timeout=args.timeout
                    )
            finally:
                scraper.close()
        else:
            # Use simple scraper
            scraper = WebTagScraper()
            if args.pages > 1:
                data = scraper.scrape_multiple_pages(
                    args.url,
                    args.selector,
                    args.attribute,
                    pages=args.pages,
                    page_param=args.page_param
                )
            else:
                data = scraper.scrape(
                    args.url,
                    args.selector,
                    args.attribute,
                    delay=args.delay,
                    timeout=args.timeout
                )

    else:
        print("❌ Please provide either a preset name or URL and selector")
        print("💡 Use --help for usage information")
        sys.exit(1)

    # Export results
    if data:
        exporter = DataExporter()
        output_path = exporter.export(data, args.output, args.format)

        print(f"✅ SUCCESS: Extracted {len(data)} items")
        print(f"💾 Saved to: {output_path}")

        # Show sample of results
        print(f"📋 Sample results:")
        for i, item in enumerate(data[:5], 1):
            print(f"   {i}. {item}")
        if len(data) > 5:
            print(f"   ... and {len(data) - 5} more items")

    else:
        print("❌ No data found with the given parameters")
        print("💡 Try:")
        print("   - Using a different CSS selector")
        print("   - Switching to Selenium mode with --mode selenium")
        print("   - Checking if the website requires JavaScript")
        print("   - Using --list-presets to try predefined configurations")
        sys.exit(1)


if __name__ == "__main__":
    main()