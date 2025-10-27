#!/usr/bin/env python3
"""
Download Ontario CRSA Data from AGCO Website
============================================

This script downloads the latest Cannabis Retail Store Authorization data
from the AGCO website and saves it as a CSV file.

AGCO provides this data on their website at:
https://www.agco.ca/status-current-cannabis-retail-store-applications

The data is available in an HTML table format. This script:
1. Scrapes the webpage
2. Extracts the table data
3. Converts to CSV format
4. Saves to data/crsa/ directory

Usage:
    python download_agco_crsa.py
    python download_agco_crsa.py --output /path/to/output.csv
    python download_agco_crsa.py --import  # Also run import after download
"""

import argparse
import asyncio
import csv
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import aiohttp
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# AGCO URLs
AGCO_BASE_URL = "https://www.agco.ca"
AGCO_CSV_URL = "https://www.agco.ca/en/cannabis-license-applications-download?_format=csv"
AGCO_HTML_URL = "https://www.agco.ca/status-current-cannabis-retail-store-applications"

# Default output directory
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "data" / "crsa"


async def download_agco_page(url: str, session: Optional[aiohttp.ClientSession] = None) -> str:
    """
    Download the AGCO webpage containing CRSA data

    Args:
        url: URL to download
        session: Optional aiohttp session to reuse

    Returns:
        HTML content as string

    Raises:
        aiohttp.ClientError: If download fails
    """
    logger.info(f"Downloading AGCO webpage from: {url}")

    async def _download(session):
        async with session.get(url, timeout=30) as response:
            if response.status != 200:
                raise aiohttp.ClientError(f"HTTP {response.status}: {response.reason}")

            html = await response.text()
            logger.info(f"Downloaded {len(html)} bytes")
            return html

    if session:
        return await _download(session)
    else:
        async with aiohttp.ClientSession() as new_session:
            return await _download(new_session)


def extract_crsa_table(html: str) -> Tuple[List[Dict[str, str]], Optional[int]]:
    """
    Extract CRSA data from HTML table and detect pagination

    Args:
        html: HTML content

    Returns:
        Tuple of (records, max_page_number)
        - records: List of dictionaries, one per store record
        - max_page_number: Highest page number found in pagination, or None

    The AGCO page contains a table with these columns:
    - License Number
    - Municipality or First Nation
    - Store Name
    - Address
    - Store Application Status
    - Website (sometimes optional)
    """
    logger.info("Parsing HTML and extracting table data...")

    soup = BeautifulSoup(html, 'html.parser')

    # Find the table containing CRSA data
    table = None

    # Try finding by common table patterns
    for selector in [
        'table.views-table',
        'table.cannabis-retail-stores',
        'table',  # Fallback to first table
        'div.view-content table',
        'div.cannabis-status table'
    ]:
        table = soup.select_one(selector)
        if table:
            logger.info(f"Found table using selector: {selector}")
            break

    if not table:
        logger.error("Could not find CRSA data table on page")
        logger.info("Page may have changed structure. Manual inspection required.")
        # Save HTML for debugging
        debug_path = Path("debug_agco_page.html")
        debug_path.write_text(html)
        logger.info(f"Saved page HTML to {debug_path} for debugging")
        raise ValueError("CRSA table not found on AGCO page")

    # Extract headers and clean sort indicators
    headers = []
    header_row = table.find('thead')
    if header_row:
        for th in header_row.find_all('th'):
            header_text = th.get_text(strip=True)
            # Remove sort indicators like "Sort descending"
            header_text = header_text.replace('Sort descending', '').replace('Sort ascending', '').strip()
            headers.append(header_text)
    else:
        # Try first row if no thead
        first_row = table.find('tr')
        if first_row:
            headers = [th.get_text(strip=True) for th in first_row.find_all(['th', 'td'])]

    logger.info(f"Found {len(headers)} columns: {headers}")

    # Extract rows
    records = []
    tbody = table.find('tbody') or table
    rows = tbody.find_all('tr')

    for row in rows:
        cells = row.find_all('td')
        if len(cells) < len(headers):
            continue  # Skip header rows or incomplete rows

        record = {}
        for idx, cell in enumerate(cells):
            if idx < len(headers):
                header = headers[idx]
                value = cell.get_text(strip=True)
                
                # Normalize status values to remove date suffixes
                if header == 'Store Application Status':
                    if value.startswith('Public Notice'):
                        # Normalize all "Public Notice Period: Ended [DATE]" or "Public Notice: Ends on [DATE]" to "Public Notice"
                        value = 'Public Notice'
                    # "In Progress" and other statuses remain as-is
                
                record[header] = value

        # Add record if it has required fields
        # Note: "In Progress" and "Public Notice" records may not have license numbers yet
        has_required_fields = (
            record.get('Store Name') and 
            record.get('Address') and
            (record.get('License Number') or 
             record.get('Store Application Status') in ['In Progress', 'Public Notice'])
        )
        
        if has_required_fields:
            records.append(record)

    # Detect pagination
    max_page = None
    pager = soup.find('nav', {'class': 'pager'})
    if pager:
        # Find all page links
        page_links = pager.find_all('a', href=True)
        page_numbers = []
        for link in page_links:
            href = link['href']
            if 'page=' in href:
                try:
                    page_num = int(href.split('page=')[1].split('&')[0])
                    page_numbers.append(page_num)
                except (ValueError, IndexError):
                    pass
        
        if page_numbers:
            max_page = max(page_numbers)
            logger.info(f"Detected pagination: pages 0 to {max_page}")

    logger.info(f"Extracted {len(records)} store records from this page")

    return records, max_page


def normalize_headers(records: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Normalize column headers to match expected CSV format

    Args:
        records: Records with original headers

    Returns:
        Records with normalized headers
    """
    # Expected header mappings
    header_mapping = {
        'License Number': 'License Number',
        'Licence Number': 'License Number',
        'License #': 'License Number',
        'Municipality or First Nation': 'Municipality or First Nation',
        'Municipality/First Nation': 'Municipality or First Nation',
        'Municipality': 'Municipality or First Nation',
        'Store Name': 'Store Name',
        'Name': 'Store Name',
        'Address': 'Address',
        'Store Address': 'Address',
        'Store Application Status': 'Store Application Status',
        'Status': 'Store Application Status',
        'Application Status': 'Store Application Status',
        'Website': 'Website',
        'Website URL': 'Website',
        'Web Site': 'Website',
    }

    normalized = []
    for record in records:
        normalized_record = {}
        for key, value in record.items():
            normalized_key = header_mapping.get(key, key)
            normalized_record[normalized_key] = value
        normalized.append(normalized_record)

    return normalized


def save_to_csv(records: List[Dict[str, str]], output_path: Path):
    """
    Save records to CSV file

    Args:
        records: List of store records
        output_path: Path to save CSV
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Define expected columns
    columns = [
        'License Number',
        'Municipality or First Nation',
        'Store Name',
        'Address',
        'Store Application Status',
        'Website'
    ]

    logger.info(f"Saving {len(records)} records to {output_path}")

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)

    logger.info(f"✅ CSV saved successfully: {output_path}")


async def download_csv_direct(csv_url: str) -> List[Dict[str, str]]:
    """
    Download CRSA data directly from CSV export URL
    
    This is much faster and more reliable than scraping HTML pages.
    
    Args:
        csv_url: Direct CSV export URL
        
    Returns:
        List of all store records
    """
    logger.info(f"Downloading CRSA data from CSV export: {csv_url}")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(csv_url, timeout=60) as response:
            if response.status != 200:
                raise aiohttp.ClientError(f"HTTP {response.status}: {response.reason}")
            
            csv_content = await response.text()
            logger.info(f"Downloaded {len(csv_content)} bytes of CSV data")
    
    # Parse CSV content
    records = []
    csv_reader = csv.DictReader(csv_content.splitlines())
    
    for row in csv_reader:
        # CSV columns might be slightly different, normalize them
        record = {
            'License Number': row.get('License Number', ''),
            'Municipality or First Nation': row.get('Municipality or First Nation', ''),
            'Store Name': row.get('Store Name', ''),
            'Address': row.get('Address', ''),
            'Store Application Status': row.get('Store Application Status', ''),
            'Website': row.get('Website', '')
        }
        
        # Only add if we have required fields
        if record['License Number'] and record['Store Name']:
            records.append(record)
    
    logger.info(f"Parsed {len(records)} store records from CSV")
    return records


async def download_all_pages(base_url: str) -> List[Dict[str, str]]:
    """
    Download all paginated pages from AGCO website (HTML scraping fallback)

    Args:
        base_url: Base URL without pagination parameters

    Returns:
        List of all store records from all pages
    """
    all_records = []
    
    async with aiohttp.ClientSession() as session:
        # Download first page to detect pagination
        logger.info("Downloading page 0 (first page)...")
        html = await download_agco_page(base_url, session)
        records, max_page = extract_crsa_table(html)
        all_records.extend(records)
        
        if max_page is None:
            logger.info("No pagination detected, single page only")
            return all_records
        
        logger.info(f"Found {max_page + 1} total pages (0-{max_page})")
        logger.info(f"Page 0: {len(records)} records")
        
        # Download remaining pages
        for page_num in range(1, max_page + 1):
            page_url = f"{base_url}?page={page_num}"
            logger.info(f"Downloading page {page_num}/{max_page}...")
            
            try:
                html = await download_agco_page(page_url, session)
                records, _ = extract_crsa_table(html)
                all_records.extend(records)
                logger.info(f"Page {page_num}: {len(records)} records")
                
                # Small delay to be nice to the server
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Failed to download page {page_num}: {e}")
                # Continue with other pages
                continue
    
    logger.info(f"Total records downloaded: {len(all_records)}")
    return all_records


async def download_and_save(output_path: Optional[Path] = None, use_csv: bool = False) -> Path:
    """
    Download AGCO data and save as CSV

    Args:
        output_path: Optional custom output path
        use_csv: If True, try direct CSV download first (experimental). 
                 If False (default), use reliable HTML scraping

    Returns:
        Path to saved CSV file
        
    Note: Direct CSV download from AGCO uses a batch process that may not be reliable.
          HTML scraping with pagination is the recommended method.
    """
    # Generate output path if not provided
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = DEFAULT_OUTPUT_DIR / f"crsa_data_{timestamp}.csv"

    try:
        # Try CSV download first if requested (experimental)
        if use_csv:
            logger.info("Attempting direct CSV download (experimental)...")
            try:
                all_records = await download_csv_direct(AGCO_CSV_URL)
                if len(all_records) < 100:  # Sanity check - should have 1000+ records
                    logger.warning(f"CSV download returned only {len(all_records)} records, falling back to HTML scraping")
                    raise ValueError("CSV download returned insufficient records")
            except Exception as csv_error:
                logger.warning(f"CSV download failed: {csv_error}")
                logger.info("Falling back to HTML scraping...")
                all_records = await download_all_pages(AGCO_HTML_URL)
                all_records = normalize_headers(all_records)
        else:
            # HTML scraping method (recommended - slower but reliable)
            logger.info("Using HTML scraping with pagination (recommended method)...")
            all_records = await download_all_pages(AGCO_HTML_URL)
            all_records = normalize_headers(all_records)

        # Save to CSV
        save_to_csv(all_records, output_path)

        return output_path

    except Exception as e:
        logger.error(f"Failed to download AGCO data: {e}")
        raise


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Download Ontario CRSA data from AGCO')
    parser.add_argument('--output', '-o', help='Output CSV file path')
    parser.add_argument('--import', '-i', dest='run_import', action='store_true',
                        help='Also run import script after download')

    args = parser.parse_args()

    # Determine output path
    output_path = Path(args.output) if args.output else None

    try:
        # Download and save
        csv_path = await download_and_save(output_path)

        logger.info("=" * 60)
        logger.info("✅ Download completed successfully")
        logger.info(f"📄 CSV file: {csv_path}")
        logger.info("=" * 60)

        # Run import if requested
        if args.run_import:
            logger.info("Running import script...")
            sys.path.insert(0, str(Path(__file__).parent))
            from import_crsa_data import import_csv

            success = await import_csv(str(csv_path), is_initial_load=False)

            if success:
                logger.info("✅ Import completed successfully")
            else:
                logger.error("❌ Import failed")
                sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Download failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
