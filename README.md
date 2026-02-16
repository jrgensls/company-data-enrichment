# EnrichIQ - Company Data Enrichment Tool

Enrich company lists with emails, websites, and phone numbers using web scraping. Upload a CSV, click enrich, and get results — powered by [Bright Data](https://brightdata.com/) APIs and [Streamlit](https://streamlit.io/).

<div align="center">
  <img src="https://img.shields.io/badge/python-3.9+-blue"/>
  <img src="https://img.shields.io/badge/License-MIT-blue"/>
</div>

---

## Features

- **Email Enrichment** — Find contact emails by scraping company websites and Google search
- **Website Enrichment** — Find company websites via Google SERP API
- **Phone Enrichment** — Extract Dutch phone numbers from company websites
- **Background Processing** — Enrichment runs as a background service with real-time progress tracking
- **Crash Recovery** — Progress is saved to JSON, so you can resume where you left off
- **Batch Processing** — Companies processed in configurable batch sizes with rate limiting

## How It Works

1. **Upload** a CSV with a `Name` column (optionally include `City`, `Street`, `ZipCode`)
2. **Click** an enrichment button (Emails, Websites, or Phones)
3. **Monitor** progress in the Streamlit dashboard
4. **Download** results from the date-based output CSV

### Email Enrichment Flow

```
Google Search ("{company} email")
    → Parse snippets for emails
    → If not found: scrape company website (homepage, /contact, /about)
    → Extract emails from HTML
```

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/jrgensls/company-data-enrichment.git
cd company-data-enrichment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file:

```bash
BRIGHT_DATA_API_KEY=your_bright_data_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

You'll need a [Bright Data API key](https://docs.brightdata.com/api-reference/authentication) and optionally a [Google Gemini API key](https://aistudio.google.com/apikey).

### 3. Run the app

```bash
streamlit run app.py --server.headless true
```

Open http://localhost:8501 in your browser.

### CLI Usage

You can also run the enrichment service directly:

```bash
python enrichment_service.py --emails-only    # Only enrich emails
python enrichment_service.py --websites-only  # Only enrich websites
python enrichment_service.py --phones-only    # Only enrich phones
python enrichment_service.py --dry-run        # Preview what would be processed
python enrichment_service.py --reset          # Clear progress and start fresh
```

## Project Structure

```
├── app.py                  # Streamlit UI and service management
├── enrichment_service.py   # Background enrichment service
├── config.py               # Configuration and file paths
├── enrich_emails.py        # Email enrichment utilities
├── update_emails.py        # Email update helpers
├── test_enrichment.py      # Tests
├── requirements.txt        # Python dependencies
└── .env                    # API keys (not committed)
```

## License

MIT
