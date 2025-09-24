# Donation Opportunities Finder

A Python tool that uses the Google Maps Places API to discover nearby donation opportunities including NGOs, food banks, shelters, charities, and blood banks.

## 🎯 Features

- **ZIP Code Search**: Find donation opportunities by ZIP code
- **Batch Search**: Search multiple ZIP codes at once
- **Coordinate Search**: Search by exact latitude/longitude
- **Multiple Output Formats**: Results in JSON and CSV
- **Distance Sorting**: Results sorted by proximity
- **Comprehensive Data**: Includes ratings, addresses, and contact info
- **Email Reports**: Professional email reports with Gmail API
- **GitHub Actions**: Automated scheduled searches
- **Review Enhancement**: Detailed reviews and contact information

## 🚀 Quick Start

### Installation

1. Clone or download this repository
2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your Google Maps API key:
   - Copy your API key into `.env.example` 
   - Or set `GOOGLE_MAPS_API_KEY` environment variable

### Usage Examples

```bash
# Search by ZIP code
python cli.py --zip 98004 --keywords "food bank,charity,shelter" --max-results 10

# Search multiple ZIP codes
python cli.py --zip-batch --keywords "food bank,charity" --max-results 15

# Search by coordinates  
python cli.py --lat 47.6101 --lng -122.2015 --keywords "food bank,shelter" --max-results 10

# Quiet output (compact format)
python cli.py --zip 98004 --keywords "food bank" --max-results 5 --quiet

# Save only JSON format
python cli.py --zip 98004 --keywords "charity" --format json --output my_results

# Send results via email (requires email setup)
python cli.py --zip 98004 --keywords "charity" --max-results 5 --email

# Get detailed reviews and send via email
python cli.py --zip 98004 --keywords "charity" --include-reviews --email
```

## 📧 Gmail API Configuration

The system uses Gmail API v1 to send professional email reports with search results.

### Quick Setup

1. **Run the Gmail API setup script:**
   ```bash
   python setup_email.py
   ```

2. **Follow the automated setup:**
   - Downloads OAuth credentials from Google Cloud Console
   - Configures recipient email
   - Authenticates your Gmail account
   - Tests the complete setup

### Manual Setup

1. **Install Gmail API dependencies:**
   ```bash
   pip install google-auth google-auth-oauthlib google-api-python-client
   ```

2. **Create Google Cloud Project:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing
   - Enable Gmail API
   - Create OAuth 2.0 credentials (Desktop Application)
   - Download `credentials.json` to project directory

3. **Update `config.json`:**
   ```json
   {
     "email_settings": {
       "enabled": true,
       "recipient": "cliqueadmin@helpables.org",
       "api_type": "gmail_api"
     }
   }
   ```

4. **First-time authentication:**
   ```bash
   python cli.py --zip 98004 --keywords charity --email
   ```

### Gmail API Features

- **OAuth 2.0 Authentication**: Secure, no passwords needed
- **Professional Emails**: HTML and plain text formats
- **File Attachments**: Automatically includes JSON/CSV results
- **Rich Content**: Organization details, ratings, reviews, contact info
- **API Endpoint**: Uses `POST https://gmail.googleapis.com/gmail/v1/users/me/messages/send`
- **Token Management**: Automatic refresh of authentication tokens

### Authentication Flow

1. First run opens browser for Google OAuth
2. Grant permission to send emails
3. Token saved locally for future use
4. Automatic token refresh when expired
```

## 📁 Project Structure

```
donations/
├── cli.py                 # Main command-line interface
├── donation_finder.py     # Core Google Places API integration
├── zip_finder.py          # ZIP code to coordinate mapping
├── zip_coordinates.json   # ZIP code coordinate database
├── config.json           # Configuration settings
├── requirements.txt      # Python dependencies
├── .env.example         # API key template
└── results/             # Output files (JSON/CSV)
```

## 🔧 Configuration

### API Key Setup

Add your Google Maps API key to `.env.example`:
```bash
GOOGLE_MAPS_API_KEY=your_api_key_here
```

### ZIP Codes

Edit `config.json` to add your local ZIP codes:
```json
{
  "zip_codes": {
    "enabled_zip_codes": [
      "98004",
      "98074", 
      "90210"
    ]
  }
}
```

### Search Keywords

Default keywords include: `food bank`, `charity`, `shelter`, `blood bank`

Customize by using `--keywords` parameter:
```bash
python cli.py --zip 98004 --keywords "animal rescue,homeless shelter,food pantry"
```

## 📊 Sample Results

### ZIP Code 98004 (Bellevue, WA)
```
1. glassybaby bellevue (0.2km) ⭐4.2
   📍 10700 NE 4th St, Bellevue, WA 98004
   🏷️ Gift shop supporting charity

2. The Sophia Way (0.7km) ⭐3.6  
   📍 Bellevue, WA
   🏷️ Women's homeless shelter

3. Seattle Humane (4.3km) ⭐4.7
   📍 13212 SE Eastgate Way, Bellevue, WA 98005
   🏷️ Animal rescue and shelter
```

## 🛠️ Command Line Options

### Location Options (choose one):
- `--zip ZIP_CODE` - Search by ZIP code
- `--zip-batch` - Search multiple ZIP codes from config  
- `--lat LATITUDE --lng LONGITUDE` - Search by coordinates

### Search Parameters:
- `--keywords "keyword1,keyword2"` - Search terms (default: "food bank,charity,shelter,blood bank")
- `--radius METERS` - Search radius in meters (default: 5000)
- `--max-results NUMBER` - Maximum results (default: 20)

### Output Options:
- `--output FILENAME` - Output file base name (default: "donation_opportunities")
- `--format {json,csv,both}` - Output format (default: both)
- `--quiet` - Compact console output

## 🤖 GitHub Actions Automation

This project includes automated workflows for scheduled searches:

### Available Workflows

1. **Daily Batch Search**
   - Runs daily at 8 AM UTC
   - Searches all configured ZIP codes
   - Sends email reports automatically
   - Results archived as GitHub artifacts

2. **Weekly Comprehensive Search**
   - Runs every Sunday at 9 AM UTC  
   - Extended keyword search with reviews
   - Long-term result retention (90 days)

### Setup for GitHub Actions

1. **Configure Repository Secrets:**
   - `GOOGLE_MAPS_API_KEY`: Your Google Maps API key
   - `GMAIL_CREDENTIALS`: Contents of `credentials.json`
   - `GMAIL_TOKEN`: Contents of `token.json`

2. **Manual Triggers:**
   - Go to Actions tab in GitHub
   - Select workflow and click "Run workflow"
   - Customize parameters as needed

📖 **Detailed setup guide:** See [`GITHUB_SETUP.md`](GITHUB_SETUP.md)

## 🗺️ Supported Areas

The ZIP code database includes coordinates for:
- **Seattle/Bellevue Area**: 98004, 98005, 98006, 98007, 98008, 98074, 98075
- **New York City**: 10001, 10002, 10003
- **Los Angeles**: 90210, 90211  
- **Chicago**: 60601, 60602
- **Houston**: 77001, 77002
- **Philadelphia**: 19101, 19102

For unlisted ZIP codes, the system falls back to text-based search.

## 🔍 How It Works

1. **ZIP Code Lookup**: Converts ZIP code to lat/lng coordinates
2. **API Query**: Searches Google Places API with location bias
3. **Result Processing**: Deduplicates, calculates distances, sorts by proximity
4. **Output Generation**: Saves results to JSON/CSV and displays in console

## 📋 Requirements

- Python 3.7+
- Google Maps API key with Places API enabled
- Internet connection
- Dependencies: `requests`, `python-dotenv`

## 🆘 Troubleshooting

### Common Issues:

**API Key Error**: 
- Verify your API key in `.env.example`
- Ensure Places API is enabled in Google Cloud Console

**No Results Found**:
- Try broader keywords: "charity" instead of "food bank"
- Increase search radius: `--radius 10000`
- Check if ZIP code is in database: `zip_coordinates.json`

**Rate Limiting**:
- The tool includes automatic rate limiting (1 second between requests)
- For large batch searches, consider smaller result limits

## 📄 License

This project is for educational and charitable purposes. Please respect Google's API terms of service.

---

**Built with ❤️ to help connect people with local donation opportunities**