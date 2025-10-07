#!/usr/bin/env python3
"""
WebTagContent Extractor - CLI Main Entry Point
"""

import argparse
import sys
import os

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scraper import WebTagScraper
from src.exporter import DataExporter


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description='WebTagContent Extractor - Extract content from HTML tags'
    )

    parser.add_argument('url', help='Website URL to scrape')
    parser.add_argument('selector', help='CSS selector for target elements')
    parser.add_argument('-o', '--output', default='extracted_data.csv',
                        help='Output filename (default: extracted_data.csv)')
    parser.add_argument('-a', '--attribute', default='text',
                        help='Attribute to extract (text, class, href, etc.)')

    args = parser.parse_args()

    try:
        # Initialize scraper
        scraper = WebTagScraper()

        # Scrape data
        print(f"Scraping data from: {args.url}")
        data = scraper.scrape(
            args.url,
            args.selector,
            args.attribute
        )

        if data:
            # Export data
            exporter = DataExporter()
            output_path = exporter.export(data, args.output, 'csv')
            print(f"Successfully extracted {len(data)} items to: {output_path}")
        else:
            print("No data found with the given selector.")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()