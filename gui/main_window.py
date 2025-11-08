"""
Enhanced WebTagContent Extractor with Selenium Support + Pagination
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import sys
import csv
import json
from datetime import datetime
import webbrowser
import re

# Fix for PyInstaller executable
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    application_path = sys._MEIPASS
    config_dir = os.path.join(os.path.dirname(sys.executable), 'config')
else:
    # Running as script
    application_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_dir = os.path.join(application_path, 'config')

# Ensure config directory exists
if not os.path.exists(config_dir):
    os.makedirs(config_dir)

# Add paths for imports
sys.path.append(os.path.join(application_path, 'src'))

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

class SimpleScraper:
    """Simple scraper using requests + BeautifulSoup (for static sites)"""

    def __init__(self):
        if not HAS_REQUESTS:
            raise ImportError("requests/beautifulsoup4 not installed")
        self.session = requests.Session()
        self.setup_session()

    def setup_session(self):
        """Configure HTTP session with headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        })

    def detect_pagination(self, soup):
        """Detect if page has pagination and get total pages"""
        pagination_info = {}

        # Look for common pagination patterns
        pagination_selectors = [
            '.pagination',
            '.pager',
            '.page-numbers',
            '[class*="pagination"]',
            '[class*="pager"]',
            '.pagination-container'
        ]

        for selector in pagination_selectors:
            pagination_elements = soup.select(selector)
            if pagination_elements:
                # Try to find page numbers
                page_links = soup.select(f'{selector} a, {selector} li')
                page_numbers = []

                for element in page_links:
                    text = element.get_text(strip=True)
                    if text.isdigit():
                        page_numbers.append(int(text))

                if page_numbers:
                    pagination_info['total_pages'] = max(page_numbers)
                    pagination_info['selector'] = selector
                    break

        # Also check for "Page X of Y" text
        page_text_patterns = [
            'page', 'pagina', 'seite', 'página', 'ページ'
        ]

        for pattern in page_text_patterns:
            elements = soup.find_all(string=lambda text: text and pattern in text.lower())
            for element in elements:
                text = element.strip()
                matches = re.findall(r'(\d+)\s*of\s*(\d+)', text, re.IGNORECASE)
                if matches:
                    pagination_info['total_pages'] = int(matches[0][1])
                    break

        return pagination_info

    def scrape_multiple_pages(self, base_url, css_selector, attribute='text', contains_text=None, timeout=30):
        """Extract content from multiple pages with pagination"""
        try:
            # First, get the first page to detect pagination
            print(f"🔄 [PAGINATION] Analyzing: {base_url}")
            response = self.session.get(base_url, timeout=timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            pagination_info = self.detect_pagination(soup)

            all_data = []

            # Extract first page data
            first_page_data = self.scrape(base_url, css_selector, attribute, contains_text, timeout)
            all_data.extend(first_page_data)
            print(f"✅ [PAGINATION] Page 1: {len(first_page_data)} items")

            # If pagination detected, scrape additional pages
            if pagination_info and 'total_pages' in pagination_info:
                total_pages = pagination_info['total_pages']
                print(f"📖 [PAGINATION] Found {total_pages} pages total")

                for page in range(2, total_pages + 1):
                    try:
                        # Build page URL (handles different URL patterns)
                        page_url = self._build_page_url(base_url, page)
                        print(f"🔄 [PAGINATION] Scraping page {page}: {page_url}")

                        page_data = self.scrape(page_url, css_selector, attribute, contains_text, timeout)
                        all_data.extend(page_data)
                        print(f"✅ [PAGINATION] Page {page}: {len(page_data)} items")

                    except Exception as e:
                        print(f"⚠️ [PAGINATION] Error on page {page}: {e}")
                        continue

            print(f"🎯 [PAGINATION] Total items from all pages: {len(all_data)}")
            return all_data

        except Exception as e:
            print(f"❌ [PAGINATION] Error: {e}")
            return []

    def _build_page_url(self, base_url, page_number):
        """Build URL for specific page number"""
        if '?' in base_url:
            if 'page=' in base_url:
                # Replace existing page parameter
                return re.sub(r'page=\d+', f'page={page_number}', base_url)
            else:
                # Add page parameter
                return f"{base_url}&page={page_number}"
        else:
            # Add page parameter with ?
            return f"{base_url}?page={page_number}"

    def scrape(self, url, css_selector, attribute='text', contains_text=None, timeout=30, enable_scroll=True,
               max_scrolls=8, scroll_pause=2):
        """Enhanced scraping with scroll support"""
        try:
            print(f"🚀 [SELENIUM] Opening: {url}")
            self.driver.get(url)

            # Wait for page load
            import time
            time.sleep(3)

            # Wait for initial elements
            print(f"⏳ [SELENIUM] Waiting for: {css_selector}")
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
            )

            # Scroll to load all content if enabled
            if enable_scroll:
                print(f"🔄 [SELENIUM] Scrolling {max_scrolls} times to load all content...")
                last_height = self.driver.execute_script("return document.body.scrollHeight")

                for i in range(max_scrolls):
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    print(f"📜 [SELENIUM] Scroll {i + 1}/{max_scrolls} - Waiting {scroll_pause}s...")
                    time.sleep(scroll_pause)

                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        print("✅ [SELENIUM] No more content to load")
                        break
                    last_height = new_height

                # Scroll back to top
                self.driver.execute_script("window.scrollTo(0, 0);")

            # Find elements after scrolling
            elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)

            if not elements:
                print(f"❌ [SELENIUM] No elements found with: {css_selector}")
                return []

            print(f"✅ [SELENIUM] Found {len(elements)} elements")

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
                    print(f"⚠️ [SELENIUM] Error processing element: {e}")
                    continue

            print(f"🎯 [SELENIUM] Extracted {len(extracted_data)} items")
            return extracted_data

        except Exception as e:
            print(f"❌ [SELENIUM] Error: {e}")
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

class SeleniumScraper:
    """Selenium scraper for JavaScript-rendered content"""

    def __init__(self, headless=True):
        if not HAS_SELENIUM:
            raise ImportError("selenium not installed")
        self.headless = headless
        self.driver = None
        self.setup_driver()

    def setup_driver(self):
        """Setup Chrome driver"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print("✅ [SELENIUM] Chrome driver initialized")
        except Exception as e:
            print(f"❌ [SELENIUM] Failed to initialize: {e}")
            raise

    def scrape(self, url, css_selector, attribute='text', contains_text=None, timeout=30,
               enable_scroll=True, max_scrolls=20, scroll_pause=3, handle_pagination=True):
        """Extract content from JavaScript-rendered pages"""
        try:
            print(f"🚀 [SELENIUM] Opening: {url}")
            self.driver.get(url)

            # Wait for page load
            import time
            time.sleep(3)

            # Wait for elements
            print(f"⏳ [SELENIUM] Waiting for: {css_selector}")
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
            )

            elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)

            if not elements:
                print(f"❌ [SELENIUM] No elements found with: {css_selector}")
                return []

            print(f"✅ [SELENIUM] Found {len(elements)} elements")

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
                    print(f"⚠️ [SELENIUM] Error processing element: {e}")
                    continue

            print(f"🎯 [SELENIUM] Extracted {len(extracted_data)} items")
            return extracted_data

        except Exception as e:
            print(f"❌ [SELENIUM] Error: {e}")
            return []

    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
            print("✅ [SELENIUM] Browser closed")

class DataExporter:
    """Data export functionality"""

    def __init__(self, output_dir="outputs"):
        self.output_dir = output_dir
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        """Create output directory if it doesn't exist"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def export(self, data, filename):
        """Export data to CSV file"""
        if not filename.endswith('.csv'):
            filename = filename + '.csv'

        output_path = os.path.join(self.output_dir, filename)

        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Number', 'Extracted_Content', 'Extraction_Date'])

                for i, item in enumerate(data, 1):
                    writer.writerow([i, item, datetime.now().strftime('%Y-%m-%d %H:%M:%S')])

            return output_path

        except Exception as e:
            raise Exception(f"Export failed: {e}")


class ConfigManager:
    """Configuration management"""

    def __init__(self, config_dir):
        self.config_dir = config_dir
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Create config directory if it doesn't exist"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

    def load_presets(self):
        """Load website presets from presets.json"""
        try:
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                base_path = os.path.dirname(sys.executable)

                # Try multiple possible locations
                possible_paths = [
                    os.path.join(base_path, 'presets.json'),  # Same folder as .exe
                    os.path.join(sys._MEIPASS, 'presets.json'),  # PyInstaller temp folder
                ]

                for presets_path in possible_paths:
                    print(f"🔍 [EXE DEBUG] Trying presets path: {presets_path}")
                    print(f"🔍 [EXE DEBUG] File exists: {os.path.exists(presets_path)}")
                    if os.path.exists(presets_path):
                        print(f"✅ [EXE DEBUG] Found presets at: {presets_path}")
                        with open(presets_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            presets = data.get('presets', [])
                            print(f"✅ [EXE DEBUG] Loaded {len(presets)} presets")
                            return presets

                # If we get here, no presets found
                print("❌ [EXE DEBUG] Could not find presets.json in any location")
                # List files for debugging
                print(f"🔍 [EXE DEBUG] Files in {base_path}:")
                if os.path.exists(base_path):
                    for file in os.listdir(base_path):
                        print(f"   - {file}")
                return self.get_default_presets()

            else:
                # Running as script
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                presets_path = os.path.join(base_path, 'presets.json')

                print(f"🔍 [SCRIPT DEBUG] Looking for presets at: {presets_path}")
                print(f"🔍 [SCRIPT DEBUG] File exists: {os.path.exists(presets_path)}")

                if os.path.exists(presets_path):
                    with open(presets_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        presets = data.get('presets', [])
                        print(f"✅ [SCRIPT DEBUG] Loaded {len(presets)} presets")
                        return presets
                else:
                    print(f"❌ [SCRIPT DEBUG] Presets file not found")
                    return self.get_default_presets()

        except Exception as e:
            print(f"❌ Error loading presets: {e}")
            import traceback
            traceback.print_exc()
            return self.get_default_presets()

    def get_default_presets(self):
        """Return default presets if file loading fails"""
        return [
            {
                "name": "HTTPBin Test Page",
                "url": "https://httpbin.org/html",
                "selector": "h1, p",
                "attribute": "text",
                "mode": "simple",
                "description": "Reliable test page - always works!"
            },
            {
                "name": "Example.com Elements",
                "url": "https://example.com",
                "selector": "h1, p, a",
                "attribute": "text",
                "mode": "simple",
                "description": "Simple example website for testing"
            }
        ]

    def save_presets(self, presets):
        """Save presets to JSON file"""
        try:
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            presets_path = os.path.join(base_path, 'presets.json')

            with open(presets_path, 'w', encoding='utf-8') as f:
                json.dump({"presets": presets}, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(presets)} presets to: {presets_path}")
            return True
        except Exception as e:
            print(f"Error saving presets: {e}")
            return False

class WebTagExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WebTagContent Extractor v3.0 - With Pagination Support")
        self.root.geometry("1000x800")
        self.root.minsize(900, 700)

        # Initialize components
        self.simple_scraper = None
        self.selenium_scraper = None
        self.current_data = None
        self.current_mode = "auto"  # auto, simple, selenium
        self.config_manager = ConfigManager(config_dir)
        self.presets = self.config_manager.load_presets()  # Now loads array, not object

        self.setup_ui()
        self.check_dependencies()

    def check_dependencies(self):
        """Check available dependencies"""
        status_text = "✅ "
        if HAS_REQUESTS:
            status_text += "Simple scraper available | "
        else:
            status_text += "❌ Simple scraper missing | "

        if HAS_SELENIUM:
            status_text += "Selenium available"
        else:
            status_text += "❌ Selenium missing"

        print(status_text)

    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="🚀 WebTagContent Extractor v3.0 - With Pagination",
                               font=('Arial', 18, 'bold'))
        title_label.pack(pady=10)

        # Description
        desc_label = ttk.Label(main_frame,
                              text="Extract content with Simple mode (fast) or Selenium mode (JavaScript sites) - Now with Auto Pagination!",
                              font=('Arial', 10))
        desc_label.pack(pady=5)

        # Input section
        self.setup_input_section(main_frame)

        # Mode selection
        self.setup_mode_section(main_frame)

        # Presets section
        self.setup_presets_section(main_frame)

        # Action buttons
        self.setup_action_buttons(main_frame)

        # Results section
        self.setup_results_section(main_frame)

        # Status bar
        self.setup_status_bar(main_frame)

    def setup_input_section(self, parent):
        """Setup input controls"""
        input_frame = ttk.LabelFrame(parent, text="🔧 Scraping Parameters", padding="15")
        input_frame.pack(fill=tk.X, pady=10)

        # URL
        ttk.Label(input_frame, text="🌐 Website URL:").grid(row=0, column=0, sticky=tk.W, pady=8)
        self.url_entry = ttk.Entry(input_frame, width=80, font=('Consolas', 9))
        self.url_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=8, padx=(10, 0))
        self.url_entry.insert(0, "https://www.enforcetac.com/en/exhibitors-products/find-exhibitors")

        # CSS Selector
        ttk.Label(input_frame, text="🎯 CSS Selector:").grid(row=1, column=0, sticky=tk.W, pady=8)
        self.selector_entry = ttk.Entry(input_frame, width=80, font=('Consolas', 9))
        self.selector_entry.insert(0, "[data-testid='company-results-item']")
        self.selector_entry.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=8, padx=(10, 0))

        # Attribute
        ttk.Label(input_frame, text="📋 Attribute:").grid(row=2, column=0, sticky=tk.W, pady=8)
        self.attribute_combo = ttk.Combobox(input_frame, values=['text', 'class', 'href', 'id', 'src', 'title', 'alt', 'aria-label', 'data-company-name'],
                                           width=77, font=('Consolas', 9))
        self.attribute_combo.set('aria-label')
        self.attribute_combo.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=8, padx=(10, 0))

        # Contains filter
        ttk.Label(input_frame, text="🔍 Contains Text (optional):").grid(row=3, column=0, sticky=tk.W, pady=8)
        self.contains_entry = ttk.Entry(input_frame, width=80, font=('Consolas', 9))
        self.contains_entry.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=8, padx=(10, 0))

        # Pagination option
        self.pagination_var = tk.BooleanVar()
        pagination_check = ttk.Checkbutton(input_frame, text="🔄 Extract ALL pages (auto-detect pagination)",
                                          variable=self.pagination_var)
        pagination_check.grid(row=4, column=1, columnspan=2, sticky=tk.W, pady=8, padx=(10, 0))

        # Configure grid weights
        input_frame.columnconfigure(1, weight=1)

    def setup_mode_section(self, parent):
        """Setup scraping mode selection"""
        mode_frame = ttk.LabelFrame(parent, text="⚡ Scraping Mode", padding="10")
        mode_frame.pack(fill=tk.X, pady=10)

        self.mode_var = tk.StringVar(value="auto")

        ttk.Radiobutton(mode_frame, text="🔄 Auto (Detect Best)", variable=self.mode_var,
                       value="auto").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_frame, text="⚡ Simple (Fast - Static Sites)", variable=self.mode_var,
                       value="simple").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_frame, text="🌐 Selenium (JavaScript Sites)", variable=self.mode_var,
                       value="selenium").pack(side=tk.LEFT, padx=10)

        # Mode info label
        self.mode_info = ttk.Label(mode_frame, text="Auto mode will try Simple first, then Selenium if needed",
                                  font=('Arial', 9, 'italic'))
        self.mode_info.pack(side=tk.LEFT, padx=20)

    def setup_presets_section(self, parent):
        """Setup presets dropdown"""
        presets_frame = ttk.LabelFrame(parent, text="📚 Quick Presets", padding="10")
        presets_frame.pack(fill=tk.X, pady=10)

        ttk.Label(presets_frame, text="Load preset:").pack(side=tk.LEFT, padx=5)

        self.preset_var = tk.StringVar()

        # UPDATED: Handle new array structure
        preset_names = []
        for preset in self.presets:  # Now it's a list, not dict
            mode = preset.get('mode', 'auto')
            name = preset.get('name', 'Unnamed Preset')
            preset_names.append(f"{name} ({mode})")

        self.preset_combo = ttk.Combobox(presets_frame, textvariable=self.preset_var,
                                        values=preset_names, width=40, state="readonly")
        self.preset_combo.pack(side=tk.LEFT, padx=5)
        self.preset_combo.bind('<<ComboboxSelected>>', self.on_preset_selected)

        ttk.Button(presets_frame, text="Load Preset",
                  command=self.load_selected_preset).pack(side=tk.LEFT, padx=5)

    def setup_action_buttons(self, parent):
        """Setup action buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=15)

        # Main actions
        ttk.Button(button_frame, text="🎯 Extract Content",
                  command=self.start_extraction).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="💾 Export to CSV",
                  command=self.export_results).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="🧹 Clear Results",
                  command=self.clear_results).pack(side=tk.LEFT, padx=5)

        # Utility buttons
        ttk.Button(button_frame, text="📊 Preview CSV",
                  command=self.preview_csv).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="❓ Help",
                  command=self.show_help).pack(side=tk.RIGHT, padx=5)

    def setup_results_section(self, parent):
        """Setup results display"""
        results_frame = ttk.LabelFrame(parent, text="📊 Extracted Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Results counter and mode info
        info_frame = ttk.Frame(results_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        self.results_counter = ttk.Label(info_frame, text="Items found: 0", font=('Arial', 10, 'bold'))
        self.results_counter.pack(side=tk.LEFT)

        self.mode_used_label = ttk.Label(info_frame, text="Mode: Not used", font=('Arial', 9, 'italic'))
        self.mode_used_label.pack(side=tk.RIGHT)

        # Results text area
        text_frame = ttk.Frame(results_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.results_text = scrolledtext.ScrolledText(text_frame, width=100, height=20,
                                                     font=('Consolas', 9), wrap=tk.WORD)
        self.results_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

    def setup_status_bar(self, parent):
        """Setup status bar"""
        self.status_var = tk.StringVar(value="✅ Ready - Choose mode and extract content")
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN, padding=(5, 2))
        status_bar.pack(fill=tk.X, pady=5)

    def clean_security_policing_urls(self, urls):
        """Extract company names from Security & Policing UK URLs"""
        cleaned_names = []
        for url in urls:
            # Extract the part between /exhibitors-list-2025/ and the next /
            if '/exhibitors-list-2025/' in url:
                # Get the segment after exhibitors-list-2025/
                segment = url.split('/exhibitors-list-2025/')[-1].split('/')[0]
                # Remove -2, -3 suffixes
                if segment.endswith('-2') or segment.endswith('-3'):
                    segment = segment[:-2]
                # Replace hyphens with spaces and title case
                clean_name = segment.replace('-', ' ').title()
                cleaned_names.append(clean_name)
            else:
                # Keep original if it doesn't match the pattern
                cleaned_names.append(url)
        return cleaned_names

    def on_preset_selected(self, event):
        """When preset is selected from dropdown"""
        self.load_selected_preset()

    def load_selected_preset(self):
        """Load the selected preset"""
        selected_display = self.preset_var.get()

        # UPDATED: Search in array instead of dict
        for preset in self.presets:
            mode = preset.get('mode', 'auto')
            preset_display = f"{preset.get('name', 'Unnamed')} ({mode})"

            if preset_display == selected_display:
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, preset.get('url', ''))
                self.selector_entry.delete(0, tk.END)
                self.selector_entry.insert(0, preset.get('selector', ''))
                self.attribute_combo.set(preset.get('attribute', 'text'))
                self.mode_var.set(preset.get('mode', 'auto'))
                self.contains_entry.delete(0, tk.END)
                self.contains_entry.insert(0, preset.get('contains_text', ''))
                self.status_var.set(f"✅ Loaded: {preset.get('name', 'Preset')}")
                break

    def initialize_scrapers(self):
        """Initialize scrapers with error handling"""
        errors = []

        if self.mode_var.get() in ["auto", "simple"] and HAS_REQUESTS:
            if self.simple_scraper is None:
                try:
                    self.simple_scraper = SimpleScraper()
                except ImportError as e:
                    errors.append(f"Simple scraper: {e}")

        if self.mode_var.get() in ["auto", "selenium"] and HAS_SELENIUM:
            if self.selenium_scraper is None:
                try:
                    self.selenium_scraper = SeleniumScraper(headless=True)
                except ImportError as e:
                    errors.append(f"Selenium: {e}")

        return len(errors) == 0, errors

    def start_extraction(self):
        """Start the content extraction process"""
        url = self.url_entry.get().strip()
        selector = self.selector_entry.get().strip()

        if not url or not selector:
            messagebox.showerror("Error", "Please enter both URL and CSS selector")
            return

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        # Initialize scrapers
        success, errors = self.initialize_scrapers()
        if not success:
            messagebox.showerror("Dependency Error",
                               "Missing required dependencies:\n" + "\n".join(errors))
            return

        self.status_var.set("⏳ Starting extraction...")
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "🔄 Starting extraction...\n\n")
        self.mode_used_label.config(text="Mode: Starting...")

        # Run in thread to prevent GUI freeze
        thread = threading.Thread(target=self.run_extraction, args=(url, selector))
        thread.daemon = True
        thread.start()

    def run_extraction(self, url, selector):
        """Run extraction in separate thread"""
        try:
            mode = self.mode_var.get()
            attribute = self.attribute_combo.get()
            contains_text = self.contains_entry.get().strip() or None
            use_pagination = getattr(self, 'pagination_var', tk.BooleanVar()).get()

            data = []
            used_mode = "none"

            if mode == "auto":
                # Try simple first, then selenium if needed
                print("🔄 [AUTO] Trying simple mode first...")
                self.root.after(0, lambda: self.mode_used_label.config(text="Mode: Trying Simple..."))
                self.root.after(0, lambda: self.status_var.set("⏳ Auto: Trying simple mode..."))

                if use_pagination:
                    data = self.simple_scraper.scrape_multiple_pages(url, selector, attribute, contains_text)
                    used_mode = "simple (multi-page)"
                else:
                    data = self.simple_scraper.scrape(url, selector, attribute, contains_text)

                if data:
                    used_mode = "simple" if not use_pagination else "simple (multi-page)"
                else:
                    print("🔄 [AUTO] Simple mode failed, trying Selenium...")
                    self.root.after(0, lambda: self.mode_used_label.config(text="Mode: Trying Selenium..."))
                    self.root.after(0, lambda: self.status_var.set("⏳ Auto: Trying Selenium mode..."))

                    data = self.selenium_scraper.scrape(url, selector, attribute, contains_text)
                    used_mode = "selenium"

            elif mode == "simple":
                print("⚡ [SIMPLE] Using simple mode...")
                self.root.after(0, lambda: self.mode_used_label.config(text="Mode: Simple"))
                if use_pagination:
                    data = self.simple_scraper.scrape_multiple_pages(url, selector, attribute, contains_text)
                    used_mode = "simple (multi-page)"
                else:
                    data = self.simple_scraper.scrape(url, selector, attribute, contains_text)
                    used_mode = "simple"

            elif mode == "selenium":
                print("🌐 [SELENIUM] Using Selenium mode...")
                self.root.after(0, lambda: self.mode_used_label.config(text="Mode: Selenium"))
                data = self.selenium_scraper.scrape(url, selector, attribute, contains_text)
                used_mode = "selenium"

            self.root.after(0, self.display_results, data, used_mode)

        except Exception as e:
            self.root.after(0, self.display_error, str(e))

    def display_results(self, data, used_mode):
        """Display results in the text area"""
        self.results_text.delete(1.0, tk.END)

        # Auto-clean Security & Policing UK URLs
        current_url = self.url_entry.get().strip()
        if 'securityandpolicing.co.uk' in current_url and 'exhibitors-list-2025' in current_url:
            data = self.clean_security_policing_urls(data)
            used_mode = f"{used_mode} (cleaned)"

        if data:
            self.results_counter.config(text=f"Items found: {len(data)}")
            self.mode_used_label.config(text=f"Mode: {used_mode.upper()} - SUCCESS")

            self.results_text.insert(tk.END, f"✅ Success! Found {len(data)} items using {used_mode} mode:\n\n")

            for i, item in enumerate(data, 1):
                display_item = item if len(item) < 200 else item[:200] + "..."
                self.results_text.insert(tk.END, f"{i:4d}. {display_item}\n")

            if any(len(item) >= 200 for item in data):
                self.results_text.insert(tk.END, "\n💡 Note: Some items were truncated for display\n")

            self.status_var.set(f"✅ Successfully extracted {len(data)} items using {used_mode} mode")
            self.current_data = data
        else:
            self.results_counter.config(text="Items found: 0")
            self.mode_used_label.config(text=f"Mode: {used_mode.upper()} - FAILED")
            self.results_text.insert(tk.END, "❌ No content found.\n\n")
            self.results_text.insert(tk.END, "💡 Tips:\n")
            self.results_text.insert(tk.END, "• Try Selenium mode for JavaScript sites\n")
            self.results_text.insert(tk.END, "• Check selector in browser DevTools\n")
            self.results_text.insert(tk.END, "• Some sites block automated requests\n")
            self.status_var.set("❌ No results found")
            self.current_data = None

    def display_error(self, error_msg):
        """Display error message"""
        self.results_text.insert(tk.END, f"\n❌ Error: {error_msg}")
        self.status_var.set("Error occurred during extraction")
        self.mode_used_label.config(text="Mode: ERROR")

    def export_results(self):
        """Export results to CSV file"""
        if not self.current_data:
            messagebox.showwarning("Warning", "No data to export. Please extract content first.")
            return

        default_name = f"extracted_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filename = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ],
            title="Export extracted content as CSV",
            initialfile=default_name
        )

        if filename:
            try:
                exporter = DataExporter()
                output_path = exporter.export(self.current_data, filename)

                messagebox.showinfo("Success",
                                  f"✅ Data exported successfully!\n\n"
                                  f"File: {os.path.basename(output_path)}\n"
                                  f"Location: {output_path}\n"
                                  f"Items: {len(self.current_data)}")
                self.status_var.set(f"💾 Exported {len(self.current_data)} items to CSV")

            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export: {e}")

    def preview_csv(self):
        """Show preview of what CSV export would look like"""
        if not self.current_data:
            messagebox.showwarning("Warning", "No data to preview. Please extract content first.")
            return

        preview_window = tk.Toplevel(self.root)
        preview_window.title("CSV Export Preview")
        preview_window.geometry("800x600")

        preview_text = scrolledtext.ScrolledText(preview_window, width=100, height=30, font=('Consolas', 9))
        preview_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Generate CSV preview
        preview_content = "Number,Extracted_Content,Extraction_Date\n"
        for i, item in enumerate(self.current_data[:10], 1):
            escaped_item = item.replace('"', '""')
            if ',' in item or '"' in item:
                escaped_item = f'"{escaped_item}"'
            preview_content += f'{i},{escaped_item},{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'

        if len(self.current_data) > 10:
            preview_content += f"... and {len(self.current_data) - 10} more items\n"

        preview_text.insert(tk.END, preview_content)
        preview_text.config(state=tk.DISABLED)

        ttk.Button(preview_window, text="Close", command=preview_window.destroy).pack(pady=10)

    def show_help(self):
        """Show help information"""
        help_text = """
WebTagContent Extractor v3.0 - Help Guide

⚡ SCRAPING MODES:
• AUTO: Tries Simple mode first, then Selenium if needed
• SIMPLE: Fast for static HTML sites (no JavaScript)
• SELENIUM: For JavaScript-rendered content (slower but powerful)

🎯 NEW FEATURE - PAGINATION:
• Check "Extract ALL pages" to automatically detect and scrape multiple pages
• Works with websites that have pagination (Page 1, 2, 3...)
• Combines all results into one list automatically

📋 RECOMMENDED USAGE:
• Simple sites (httpbin.org, example.com): Use SIMPLE mode
• Modern sites (Enforce Tac, React apps): Use SELENIUM mode
• Unknown sites: Start with AUTO mode
• Multi-page sites: Check "Extract ALL pages" checkbox

💡 TROUBLESHOOTING:
• If SIMPLE mode fails, try SELENIUM mode
• Use browser DevTools (F12) to find correct CSS selectors
• Some websites block all automated requests
        """

        help_window = tk.Toplevel(self.root)
        help_window.title("Help - WebTagContent Extractor v3.0")
        help_window.geometry("700x500")

        help_text_widget = scrolledtext.ScrolledText(help_window, width=80, height=30, font=('Arial', 10))
        help_text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        help_text_widget.insert(tk.END, help_text)
        help_text_widget.config(state=tk.DISABLED)

        ttk.Button(help_window, text="Close", command=help_window.destroy).pack(pady=10)

    def clear_results(self):
        """Clear results and reset UI"""
        self.results_text.delete(1.0, tk.END)
        self.results_counter.config(text="Items found: 0")
        self.mode_used_label.config(text="Mode: Not used")
        self.current_data = None
        self.status_var.set("✅ Ready - Choose mode and extract content")

    def on_closing(self):
        """Cleanup when application closes"""
        if self.selenium_scraper:
            self.selenium_scraper.close()
        self.root.destroy()

def main():
    """Main function to run the GUI"""
    root = tk.Tk()
    app = WebTagExtractorGUI(root)

    # Handle application close
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    root.mainloop()

if __name__ == "__main__":
    main()