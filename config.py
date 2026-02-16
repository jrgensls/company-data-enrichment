"""
Configuration settings for the automated enrichment service.
"""
import os
from datetime import datetime
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Batch processing settings
BATCH_SIZE = 15  # Companies per batch
RATE_LIMIT_DELAY = 2  # Seconds between batches
API_TIMEOUT = 300  # Seconds to wait for Bright Data API

# File paths
UPLOADED_CSV = BASE_DIR / "uploaded_companies.csv"  # Uploaded file from Streamlit
INPUT_CSV = UPLOADED_CSV  # Default input is the uploaded file
OUTPUT_CSV = BASE_DIR / "companies_NOAB_enriched_full.csv"
PROGRESS_FILE = BASE_DIR / "progress.json"
LOG_FILE = BASE_DIR / "enrichment.log"


def get_output_filename():
    """Generate output filename with current date."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    return BASE_DIR / f"{date_str} - Companies Enriched.csv"


def get_input_file():
    """Get the input file path. Returns uploaded file if exists, otherwise default."""
    if UPLOADED_CSV.exists():
        return UPLOADED_CSV
    return INPUT_CSV

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 5  # Base delay in seconds (exponential backoff applied)

# Bright Data API settings
BRIGHT_DATA_API_URL = "https://api.brightdata.com/request"
BRIGHT_DATA_ZONE = "mcp_unlocker"  # For website scraping
BRIGHT_DATA_SERP_ZONE = "serp_api2_searchengine"  # For Google/Bing search

# Load API keys from environment
BRIGHT_DATA_API_KEY = os.getenv("BRIGHT_DATA_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Scraping settings
SCRAPE_TIMEOUT = 30  # Timeout for individual page scrapes
CONTACT_PAGE_PATTERNS = [
    "/contact",
    "/kontakt", 
    "/over-ons",
    "/about",
    "/about-us",
]
