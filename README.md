# 🚀 WebTagContentExtractor v4.0

**Advanced dual-mode web scraping tool with intelligent exhibition directory extraction**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![Selenium](https://img.shields.io/badge/Selenium-4.15-green)](https://selenium.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## ✨ **NEW in v4.0**
- **🎯 Enhanced Selenium Scraper** with intelligent "Load More" button handling
- **🏢 Exhibition Directory Specialization** optimized for InfoSecurity Europe, Milipol, etc.
- **🔄 Advanced Pagination** with scroll detection and content stability checks
- **📊 Comprehensive Coverage** ensuring 95%+ exhibitor extraction
- **🎪 Preset Management** with 25+ pre-configured exhibition scrapers
- **🚀 Executable Build** - Ready-to-use .exe application

## 🛠️ **Features**

### 🔧 **Dual Scraping Modes**
- **⚡ Simple Mode**: Fast scraping for static HTML sites (requests + BeautifulSoup)
- **🌐 Selenium Mode**: Full JavaScript rendering for modern websites  
- **🔄 Auto Mode**: Automatically detects the best scraping method

### 🎯 **Exhibition & Directory Support**
- **Intelligent "Load More" handling** with multiple selector fallbacks
- **Scroll-triggered content loading** detection
- **Pagination automation** for multi-page directories
- **25+ Pre-configured exhibition presets** (InfoSecurity Europe, Milipol, Eurosatory, etc.)
- **Company name extraction** with UI element filtering

### 🖥️ **User Interface**
- **Modern GUI** with tkinter
- **Real-time progress tracking**
- **Preset management system**
- **CSV preview before export**
- **One-click executable**

### 📊 **Export & Data Management**
- **CSV export** with timestamps
- **Duplicate removal**
- **Data filtering** and cleaning
- **Batch processing** support

## 🚀 **Quick Start**

### Option 1: Use the Executable (Windows)
1. Download the latest `WebTagContentExtractor.exe` from [Releases](https://github.com/yourusername/WebTagContentExtractor/releases)
2. Run the executable - no installation required!
3. Load presets and start scraping

### Option 2: Run from Source
```bash
# Clone the repository
git clone https://github.com/yourusername/WebTagContentExtractor.git
cd WebTagContentExtractor

# Install dependencies
pip install -r requirements.txt

# Run the application
python main_window.py