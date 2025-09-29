#!/usr/bin/env python3
"""
Complete Villa.az Web Scraper
Scrapes all 66 pages and extracts detailed listing information including contact details.
Uses asyncio and aiohttp for high-performance concurrent scraping.

Usage:
    python villa_scraper_complete.py

Requirements:
    pip install aiohttp beautifulsoup4 pandas openpyxl lxml
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from urllib.parse import urljoin
import logging
import sys
from typing import List, Dict, Optional
from aiohttp import ClientSession, ClientTimeout, TCPConnector

class VillaScraper:
    def __init__(self, base_url: str = "https://villa.az", max_concurrent: int = 15, delay: float = 0.1):
        """
        Initialize the villa.az scraper

        Args:
            base_url: Base URL of the website
            max_concurrent: Maximum number of concurrent requests
            delay: Delay between requests in seconds
        """
        self.base_url = base_url
        self.max_concurrent = max_concurrent
        self.delay = delay
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('villa_scraper.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Session headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    async def get_page(self, session: ClientSession, url: str) -> Optional[BeautifulSoup]:
        """Get a page and return BeautifulSoup object with rate limiting"""
        async with self.semaphore:
            try:
                self.logger.debug(f"Fetching: {url}")
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        await asyncio.sleep(self.delay)
                        return BeautifulSoup(content, 'html.parser')
                    else:
                        self.logger.warning(f"HTTP {response.status} for {url}")
                        return None
            except Exception as e:
                self.logger.error(f"Error fetching {url}: {e}")
                return None

    async def extract_listing_urls_from_page(self, session: ClientSession, page_url: str, page_num: int) -> List[str]:
        """Extract listing URLs from a single search page"""
        soup = await self.get_page(session, page_url)
        if not soup:
            return []

        # Find all listing links
        ads_links = soup.find_all('a', href=True)
        page_listings = []

        for link in ads_links:
            href = link.get('href')
            if href and href.startswith('/') and not href.startswith('/search'):
                # Convert relative URL to absolute
                full_url = urljoin(self.base_url, href)
                # Skip if it's not a listing page
                if 'satilir-' in href or 'kiraye-' in href:
                    page_listings.append(full_url)

        # Remove duplicates from this page
        page_listings = list(set(page_listings))
        self.logger.info(f"Page {page_num}: Found {len(page_listings)} listings")
        return page_listings

    async def extract_all_listing_urls(self, search_url: str, max_pages: int = 66) -> List[str]:
        """Extract all listing URLs from search pages concurrently"""
        timeout = ClientTimeout(total=30, connect=10)
        connector = TCPConnector(limit=100, limit_per_host=20)

        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            # Create tasks for all pages
            tasks = []
            for page in range(1, max_pages + 1):
                page_url = f"{search_url}&page={page}"
                task = self.extract_listing_urls_from_page(session, page_url, page)
                tasks.append(task)

            self.logger.info(f"Starting to extract URLs from {max_pages} pages...")
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Flatten results and handle exceptions
            all_listings = []
            for i, result in enumerate(results, 1):
                if isinstance(result, Exception):
                    self.logger.error(f"Error processing page {i}: {result}")
                elif isinstance(result, list):
                    all_listings.extend(result)

            # Remove duplicates
            unique_listings = list(set(all_listings))
            self.logger.info(f"Total unique listings found: {len(unique_listings)}")
            return unique_listings

    def extract_listing_details(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract detailed information from a listing page soup"""
        details = {'url': url}

        try:
            # Extract title
            title_elem = soup.find('h1', class_='elan-single-wrapper-top--title')
            details['title'] = title_elem.get_text(strip=True) if title_elem else ''

            # Extract price
            price_elem = soup.find('div', class_='elan-single-wrapper-top--price')
            details['price'] = price_elem.get_text(strip=True) if price_elem else ''

            # Extract listing ID
            id_match = re.search(r'ID # (\d+)', details['title'])
            details['listing_id'] = id_match.group(1) if id_match else ''

            # Extract property details from table
            table = soup.find('table', class_='table-info-1')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) == 2:
                        key = cells[0].get_text(strip=True).replace(':', '')
                        value = cells[1].get_text(strip=True)
                        details[key] = value

            # Extract address
            address_elem = soup.find('div', class_='elan-single-content--address')
            if address_elem:
                address_spans = address_elem.find_all('span')
                if len(address_spans) > 1:
                    details['address'] = address_spans[1].get_text(strip=True)

            # Extract description
            desc_elem = soup.find('div', class_='elan-single-description')
            details['description'] = desc_elem.get_text(strip=True) if desc_elem else ''

            # Extract contact information
            phone_list = soup.find('ul', class_='elan-single-owner-phon-list')
            if phone_list:
                phones = []
                for li in phone_list.find_all('li'):
                    phone_link = li.find('a')
                    if phone_link:
                        phone = phone_link.get_text(strip=True)
                        # Clean phone number
                        phone = re.sub(r'tel:', '', phone)
                        phones.append(phone)
                details['phones'] = ', '.join(phones)

            # Extract owner information
            owner_info = soup.find('ul', class_='elan-single-owner-info')
            if owner_info:
                owner_items = owner_info.find_all('li')
                if owner_items:
                    # First li usually contains the name
                    name_link = owner_items[0].find('a')
                    details['owner_name'] = name_link.get_text(strip=True) if name_link else ''

                    # Second li usually contains the type (agent/owner)
                    if len(owner_items) > 1:
                        details['owner_type'] = owner_items[1].get_text(strip=True)

            # Extract view count and date
            view_date_table = soup.find('table', class_='table-info-2')
            if view_date_table:
                view_date_text = view_date_table.get_text(strip=True)
                date_match = re.search(r'Tarix: (\d{2}-\d{2}-\d{2})', view_date_text)
                view_match = re.search(r'Baxış sayı: (\d+)', view_date_text)

                details['date'] = date_match.group(1) if date_match else ''
                details['view_count'] = view_match.group(1) if view_match else ''

        except Exception as e:
            self.logger.error(f"Error extracting details from {url}: {e}")
            details['error'] = str(e)

        return details

    async def extract_single_listing_details(self, session: ClientSession, url: str, index: int, total: int) -> Dict:
        """Extract detailed information from a single listing page"""
        soup = await self.get_page(session, url)
        if not soup:
            return {'url': url, 'error': 'Failed to fetch page'}

        if index % 50 == 0:
            self.logger.info(f"Processing listing {index}/{total}: {url}")

        return self.extract_listing_details(soup, url)

    async def scrape_all_listings_details(self, listing_urls: List[str]) -> List[Dict]:
        """Scrape details from all listing URLs concurrently"""
        timeout = ClientTimeout(total=30, connect=10)
        connector = TCPConnector(limit=100, limit_per_host=20)

        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            # Create tasks for all listings
            tasks = []
            for i, url in enumerate(listing_urls, 1):
                task = self.extract_single_listing_details(session, url, i, len(listing_urls))
                tasks.append(task)

            self.logger.info(f"Starting to extract details for {len(listing_urls)} listings...")

            # Process in batches to avoid overwhelming the server
            batch_size = 50
            all_listings = []

            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                self.logger.info(f"Processing batch {i//batch_size + 1}/{(len(tasks) + batch_size - 1)//batch_size}")

                try:
                    results = await asyncio.gather(*batch, return_exceptions=True)

                    # Handle results and exceptions
                    for result in results:
                        if isinstance(result, Exception):
                            self.logger.error(f"Error in batch: {result}")
                            all_listings.append({'error': str(result)})
                        elif isinstance(result, dict):
                            all_listings.append(result)

                    # Save progress
                    if len(all_listings) % 100 == 0:
                        self.save_to_files(all_listings, f"villa_listings_progress_{len(all_listings)}")

                except Exception as e:
                    self.logger.error(f"Error processing batch: {e}")

                # Small delay between batches
                await asyncio.sleep(1)

            return all_listings

    async def scrape_all_listings(self, search_url: str, max_pages: int = 66) -> List[Dict]:
        """Main method to scrape all listings"""
        # Step 1: Extract all listing URLs
        listing_urls = await self.extract_all_listing_urls(search_url, max_pages)

        if not listing_urls:
            self.logger.error("No listing URLs found")
            return []

        # Step 2: Extract details from all listings
        all_listings = await self.scrape_all_listings_details(listing_urls)

        return all_listings

    def save_to_files(self, listings: List[Dict], filename: str = "villa_listings"):
        """Save listings to CSV and XLSX files"""
        if not listings:
            self.logger.warning("No listings to save")
            return

        df = pd.DataFrame(listings)

        # Save to CSV
        csv_filename = f"{filename}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        self.logger.info(f"Saved {len(listings)} listings to {csv_filename}")

        # Save to XLSX
        xlsx_filename = f"{filename}.xlsx"
        df.to_excel(xlsx_filename, index=False, engine='openpyxl')
        self.logger.info(f"Saved {len(listings)} listings to {xlsx_filename}")

        # Print summary
        self.logger.info(f"Summary: {len(listings)} listings saved")
        if 'phones' in df.columns:
            phones_count = df['phones'].notna().sum()
            self.logger.info(f"Listings with phone numbers: {phones_count}")

    def print_summary(self, listings: List[Dict], duration: float):
        """Print comprehensive summary of scraping results"""
        print("\n" + "=" * 60)
        print("🎉 VILLA.AZ SCRAPING COMPLETED SUCCESSFULLY!")
        print("=" * 60)

        print(f"📊 Total listings processed: {len(listings)}")

        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        print(f"⏱️  Total time taken: {hours:02d}:{minutes:02d}:{seconds:02d}")

        if listings:
            print(f"⚡ Average time per listing: {duration/len(listings):.3f} seconds")

            # Count listings with phone numbers
            listings_with_phones = sum(1 for listing in listings if listing.get('phones'))
            print(f"📞 Listings with phone numbers: {listings_with_phones}/{len(listings)} ({listings_with_phones/len(listings)*100:.1f}%)")

            # Count different property types
            categories = {}
            for listing in listings:
                category = listing.get('Kateqoriya', 'Unknown')
                categories[category] = categories.get(category, 0) + 1

            print(f"\n📈 Property types breakdown:")
            for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                print(f"   {category}: {count}")

        print(f"\n💾 Files saved:")
        print(f"   📄 CSV: villa_az_complete_dataset.csv")
        print(f"   📊 Excel: villa_az_complete_dataset.xlsx")
        print(f"   📋 Log: villa_scraper.log")


async def main():
    """Main function to run the scraper"""
    print("🏡 Villa.az Complete Scraper")
    print("=" * 50)

    # Initialize scraper with optimized settings
    scraper = VillaScraper(
        max_concurrent=20,  # Higher concurrency for faster scraping
        delay=0.1          # Short delay to be respectful but fast
    )

    # Search URL for Azerbaijan properties
    search_url = "https://villa.az/search?countries=19&window_width=1470"

    print(f"Starting scraping of all 66 pages...")
    print(f"Search URL: {search_url}")
    print(f"Concurrency: {scraper.max_concurrent} concurrent requests")
    print("-" * 50)

    start_time = time.time()

    try:
        # Run the full scraping operation
        listings = await scraper.scrape_all_listings(search_url, max_pages=66)

        # Calculate duration
        duration = time.time() - start_time

        # Save final results
        scraper.save_to_files(listings, "villa_az_complete_dataset")

        # Print comprehensive summary
        scraper.print_summary(listings, duration)

    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrupted by user")
        duration = time.time() - start_time
        print(f"Time elapsed: {duration:.2f} seconds")

    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
        logging.error(f"Fatal error: {e}", exc_info=True)

    finally:
        print("\n🔄 Cleaning up...")


def test_sample():
    """Test function with just 2 pages"""
    async def test_run():
        scraper = VillaScraper(max_concurrent=10, delay=0.1)
        search_url = "https://villa.az/search?countries=19&window_width=1470"

        print("Testing with first 2 pages...")
        start_time = time.time()

        listings = await scraper.scrape_all_listings(search_url, max_pages=2)
        duration = time.time() - start_time

        scraper.save_to_files(listings, "villa_test_results")
        scraper.print_summary(listings, duration)

    asyncio.run(test_run())


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("Running test mode (2 pages only)...")
        test_sample()
    else:
        print("Running full scrape (all 66 pages)...")
        print("Add 'test' argument to run test mode: python villa_scraper_complete.py test")
        asyncio.run(main())