# 🎯 Donation Finder - Clean Project Summary

## 🚀 **Project Overview**
A comprehensive command-line tool for discovering donation opportunities using Google Maps Places API with advanced features including user reviews, ZIP code search, and coordinate-based searches.

## 📁 **Clean Project Structure**
```
donations/
├── cli.py                    # Main CLI interface with comprehensive argument parsing
├── donation_finder.py        # Core Google Places API integration with reviews
├── zip_finder.py             # ZIP code to coordinate mapping functionality
├── zip_coordinates.json      # ZIP code coordinate database (500+ ZIP codes)
├── config.json              # Configuration settings for batch searches
├── requirements.txt         # Python dependencies (requests, python-dotenv)
├── .env.example            # API key template
├── README.md               # Complete documentation
├── .venv/                  # Virtual environment
└── results/                # All output files (JSON/CSV)
    ├── donation_opportunities_98004.csv
    ├── donation_opportunities_98004.json
    ├── donation_opportunities_coordinates.csv
    └── ... (other result files)
```

## ✨ **Key Features**

### 🔍 **Search Modes**
1. **Single ZIP Code**: `--zip 98004`
2. **Batch ZIP Codes**: `--zip-batch` (uses config.json)
3. **Coordinates**: `--lat 47.6101 --lng -122.2015`

### 📝 **Reviews Integration**
- `--include-reviews`: Fetch detailed user reviews
- `--max-reviews 3`: Control number of reviews per place
- `--reviews-for-all`: Include reviews even for low-rated places

### 📧 **Email Extraction**
- Automatically extracts email addresses from business websites when available
- Filters out generic emails (noreply, admin, webmaster, etc.)
- Displays email addresses in console output and saves to JSON/CSV
- Rate-limited web scraping with respectful delays

### 📬 **Email Delivery**
- `--email`: Send results via Gmail API to configured recipient
- **Gmail API Integration**: Uses `POST https://gmail.googleapis.com/gmail/v1/users/me/messages/send`
- **OAuth 2.0 Authentication**: Secure, no password storage required
- **Professional Reports**: HTML and plain text email formats with attachments
- **Automated Setup**: Guided configuration with `setup_email.py`
- **Target Recipient**: cliqueadmin@helpables.org

### 🎯 **Search Controls**
- `--keywords "charity,food bank"`: Multiple comma-separated keywords
- `--max-results 5`: Limit number of results
- `--radius 3000`: Search radius in meters
- `--quiet`: Condensed output format

### 💾 **Output Formats**
- JSON: Complete structured data with full review details and email addresses
- CSV: Spreadsheet-compatible format with all contact information
- Both formats include enhanced place information (phone, website, email, hours)

## 🛠 **API Integration**

### Google Places API (New)
- **Text Search**: POST requests with JSON body
- **Place Details**: Enhanced information with reviews and contact data
- **Email Extraction**: Web scraping from business websites with regex patterns
- **Advanced Rate Limiting**: Configurable delays between API calls
  - Search API: 1.2 seconds delay
  - Details API: 0.8 seconds delay
  - Email Scraping: 0.6 seconds delay
- **API Usage Tracking**: Real-time monitoring and statistics reporting
- **Field Masking**: Optimized API efficiency

### Review Data Structure
```json
{
  "author_name": "John Smith",
  "rating": 5,
  "text": "Great organization that really helps...",
  "time_description": "3 months ago",
  "publish_time": "2024-06-16T21:56:57Z"
}
```

## 🧹 **Recent Cleanup**

### ✅ **Removed**
- Duplicate import statements
- Unused `save_to_csv` method in donation_finder.py
- Redundant `print_results_table` method
- Old example/demo code
- Outdated summary files (CLEANUP_SUMMARY.md, ZIP_CODE_SUCCESS_SUMMARY.md)
- Python cache (`__pycache__/`)
- Duplicate result files (moved to results/ directory)

### ✅ **Optimized**
- Cleaned import statements
- Removed unused CSV import
- Consolidated all result files in results/ directory
- Streamlined code structure

## 🚀 **Usage Examples**

### Basic Search
```bash
python cli.py --zip 98004 --keywords "food bank,charity"
```

### Advanced Search with Reviews
```bash
python cli.py --zip 98004 --keywords "shelter" --include-reviews --max-reviews 2 --quiet
```

### Batch Search
```bash
python cli.py --zip-batch --keywords "donation center" --max-results 10
```

### Coordinate Search
```bash
python cli.py --lat 47.6101 --lng -122.2015 --keywords "nonprofit" --include-reviews
```

## 📊 **Real Data Validation**
- Successfully tested with actual places and reviews
- **Email extraction working**: Found real emails like `info@sophiaway.org`, `lightitforward@glassybaby.com`
- Fetches authentic user feedback from Google Places
- Enhanced place details include phone, website, **email**, business hours
- Rate limiting ensures API compliance and respectful web scraping

## 🎯 **Status: Complete & Production Ready**
The project is fully functional, tested, and optimized with all unnecessary code removed. Ready for production use with comprehensive donation opportunity discovery capabilities.