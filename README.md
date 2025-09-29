# Villa.az Web Scraper

A high-performance async web scraper for villa.az built with Python, asyncio, and aiohttp. Scrapes property listings from all pages and extracts detailed information including contact details, property specifications, and pricing.

## 🚀 Features

- **Async/Concurrent**: Uses asyncio and aiohttp for maximum performance
- **Complete Data Extraction**: Extracts all available data from listings
- **Contact Information**: Captures phone numbers and owner details
- **Export Formats**: Saves data to both CSV and Excel formats
- **Rate Limiting**: Respectful scraping with configurable delays
- **Progress Tracking**: Real-time progress updates and logging
- **Error Handling**: Robust error handling and recovery
- **Batch Processing**: Processes listings in batches to avoid overwhelming the server

## 📋 Requirements

- Python 3.7+
- Required packages (install with `pip install -r requirements.txt`):
  - aiohttp>=3.8.0
  - beautifulsoup4>=4.11.0
  - pandas>=1.5.0
  - openpyxl>=3.0.0
  - lxml>=4.9.0
  - requests>=2.28.0

## 🛠️ Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🎯 Usage

### Quick Start

To scrape all 66 pages (approximately 2000+ listings):
```bash
python run_full_scrape.py
```

### Test with Sample Data

To test with a smaller sample (first 3 pages):
```bash
python test_async_scraper.py
```

### Custom Usage

```python
import asyncio
from villa_scraper_async import AsyncVillaScraper

async def custom_scrape():
    scraper = AsyncVillaScraper(max_concurrent=15, delay=0.1)
    search_url = "https://villa.az/search?countries=19&window_width=1470"

    # Scrape specific number of pages
    listings = await scraper.scrape_all_listings(search_url, max_pages=10)

    # Save results
    scraper.save_to_files(listings, "custom_results")

# Run
asyncio.run(custom_scrape())
```

## 📊 Data Extracted

For each listing, the scraper extracts:

### Basic Information
- Title
- Price
- Listing ID
- URL
- Date posted
- View count

### Property Details
- Country
- City/Region
- Category (Villa, Apartment, Land, etc.)
- Area (m² and/or sot)
- Number of rooms
- Floor information
- Property document type

### Location & Description
- Address
- Full description

### Contact Information
- Phone numbers
- Owner name
- Owner type (Agent/Owner)

## 📁 Output Files

The scraper generates several output files:

1. **CSV File**: `villa_az_complete_dataset.csv` - Excel-compatible CSV
2. **Excel File**: `villa_az_complete_dataset.xlsx` - Full Excel workbook
3. **Log File**: `villa_scraper.log` - Detailed execution logs
4. **Progress Files**: Periodic saves during long scraping sessions

## ⚙️ Configuration

### Scraper Parameters

```python
AsyncVillaScraper(
    base_url="https://villa.az",     # Base website URL
    max_concurrent=20,               # Max concurrent requests
    delay=0.1                        # Delay between requests (seconds)
)
```

### Performance Tuning

- **max_concurrent**: Higher values = faster scraping, but may overwhelm server
- **delay**: Lower values = faster scraping, but should remain > 0.05 to be respectful
- **batch_size**: Internal batching (50 by default) for processing listings

## 📈 Performance

Based on testing:
- **~2000 listings in approximately 5-10 minutes** (depends on network and server response)
- **Average ~0.15 seconds per listing** with default settings
- **Memory efficient**: Processes in batches and saves progress periodically

## 🔧 Troubleshooting

### Common Issues

1. **Connection Errors**: Reduce `max_concurrent` and increase `delay`
2. **Missing Data**: Some listings may have incomplete information
3. **Rate Limiting**: If you get blocked, increase the `delay` parameter

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📋 File Structure

```
villa_az/
├── villa_scraper_async.py      # Main async scraper class
├── run_full_scrape.py          # Full scraping script
├── test_async_scraper.py       # Test script
├── villa_scraper.py            # Original synchronous version
├── test_scraper.py             # Test for sync version
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── output files/               # Generated CSV, Excel, and log files
```

## 🚨 Important Notes

### Responsible Scraping
- The scraper includes built-in delays to avoid overwhelming the server
- Uses respectful headers and follows robots.txt guidelines
- Processes in batches to distribute load

### Legal Considerations
- Ensure you comply with villa.az's terms of service
- This tool is for educational and research purposes
- Respect the website's resources and bandwidth

### Data Accuracy
- Data is extracted as-is from the website
- Some listings may have incomplete or missing information
- Phone numbers and contact details depend on what owners provide

## 🤝 Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## 📄 License

This project is for educational purposes. Please respect the website's terms of service and use responsibly.

---

**Happy Scraping! 🏡**