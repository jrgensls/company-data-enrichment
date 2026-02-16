# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Codebase Overview

**Project Name**: EnrichIQ - Company Data Enrichment Tool
**Purpose**: Enrich company lists with emails, websites, and phone numbers using web scraping
**Tech Stack**:
- Frontend: Streamlit
- Backend: Python (multi-file architecture)
- APIs: Bright Data Web Scraper API, Google Gemini AI (optional)
- No database (CSV-based with JSON progress tracking)

**Repository URL**: https://github.com/jrgensls/company-data-enrichment

---

## Product Features

### Core Features
1. **CSV Upload**: Upload company list with Name column (+ optional City, Street, ZipCode)
2. **Three Enrichment Types**:
   - **Enrich Emails** - Find contact emails by scraping company websites
   - **Enrich Websites** - Find company websites via Google search
   - **Enrich Phones** - Find Dutch phone numbers from company websites
3. **Background Processing**: Enrichment runs as background service with progress tracking
4. **Date-Based Output**: Results saved to `YYYY-MM-DD - Companies Enriched.csv`

### Key User Flows
1. **Upload Flow**: User uploads CSV → File saved to `uploaded_companies.csv` → Data displayed in table
2. **Enrichment Flow**: User clicks enrichment button → Background service starts → Progress displayed → Results in date-based CSV

---

## Folder Structure

```
company-data-enrichment/
├── app.py                  # Streamlit UI and service management
├── enrichment_service.py   # Background enrichment service
├── config.py               # Configuration and file paths
├── requirements.txt        # Python dependencies
├── .env                    # API keys (not committed)
├── uploaded_companies.csv  # Current uploaded data (generated)
├── progress.json           # Enrichment progress state (generated)
├── enrichment.log          # Service logs (generated)
├── README.md               # Project documentation
├── CLAUDE.md               # This file
├── DESIGN.md               # UI/UX design guidelines
└── CODE_REVIEW.md          # Code review guidelines
```

---

## Building the App

### Prerequisites
```bash
python --version  # Python 3.9+ required
```

### Installation
```bash
# 1. Clone the repository
git clone https://github.com/jrgensls/company-data-enrichment.git
cd company-data-enrichment

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment variables
# Create .env file with:
BRIGHT_DATA_API_KEY=your_bright_data_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### Running the App
```bash
streamlit run app.py --server.headless true
# Access at: http://localhost:8501
```

### Running Enrichment Service Directly
```bash
python enrichment_service.py --help
python enrichment_service.py --emails-only    # Only enrich emails
python enrichment_service.py --websites-only  # Only enrich websites
python enrichment_service.py --phones-only    # Only enrich phones
python enrichment_service.py --dry-run        # Preview what would be processed
python enrichment_service.py --reset          # Clear progress and start fresh
```

---

## Architecture

### config.py

Configuration constants and utility functions:

| Item | Purpose |
|------|---------|
| `UPLOADED_CSV` | Path to uploaded companies file |
| `PROGRESS_FILE` | JSON file for tracking enrichment progress |
| `LOG_FILE` | Service log file path |
| `BATCH_SIZE` | Companies per batch (default: 15) |
| `BRIGHT_DATA_ZONE` | Web Unlocker zone: `mcp_unlocker` |
| `BRIGHT_DATA_SERP_ZONE` | SERP API zone: `serp_api2_searchengine` |
| `get_output_filename()` | Returns date-based output path: `YYYY-MM-DD - Companies Enriched.csv` |
| `get_input_file()` | Returns uploaded file path if exists |

### enrichment_service.py

Background service for batch enrichment:

| Class | Purpose |
|-------|---------|
| `ProgressTracker` | Persists state to JSON for crash recovery and resume |
| `BrightDataMCP` | Handles web scraping via Bright Data APIs (SERP + Web Unlocker) |
| `EmailEnricher` | Extracts emails from HTML using regex patterns |
| `GoogleEmailFinder` | Searches Google for emails (fallback method) |
| `PhoneEnricher` | Extracts Dutch phone numbers (0XX-XXX XXXX format) |
| `WebsiteEnricher` | Finds company websites via Google SERP API |
| `EnrichmentService` | Main orchestrator - loads CSV, runs enrichment phases, exports results |

### app.py

Streamlit UI with service management:

| Function | Purpose |
|----------|---------|
| `is_service_running()` | Checks if background service is active via PID file |
| `start_service(options)` | Starts enrichment_service.py with CLI flags |
| `stop_service()` | Terminates running service |
| `get_progress()` | Reads progress.json for UI display |
| `get_recent_logs()` | Returns last N lines from enrichment.log |

### Data Flow

```
Upload CSV → uploaded_companies.csv
                    ↓
        Click "Enrich Emails/Websites/Phones"
                    ↓
        enrichment_service.py starts (background)
                    ↓
        progress.json updated in real-time
                    ↓
        YYYY-MM-DD - Companies Enriched.csv
```

### Email Enrichment Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    EMAIL ENRICHMENT                         │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │  METHOD 1: Google Search       │
        │  (SERP API - fallback)         │
        │  Search: "{company} email"     │
        │  → Parse snippets for emails   │
        └────────────────┬───────────────┘
                         │
                    Found? ──No──┐
                         │       │
                        Yes      ▼
                         │  ┌────────────────────────────────┐
                         │  │  METHOD 2: Website Scraping    │
                         │  │  (Web Unlocker API)            │
                         │  │  → Scrape homepage             │
                         │  │  → Scrape /contact, /about     │
                         │  │  → Extract emails from HTML    │
                         │  └────────────────┬───────────────┘
                         │                   │
                         ▼                   ▼
                    ┌─────────────────────────────┐
                    │          RESULT             │
                    │  ✓ Email found (via Google) │
                    │  ✓ Email found (via website)│
                    │  ✗ Not found                │
                    └─────────────────────────────┘
```

---

## Environment Variables

### Required
```bash
BRIGHT_DATA_API_KEY=   # Bright Data API authentication (Bearer token)
GEMINI_API_KEY=        # Google Gemini AI API key (optional)
```

---

## Bright Data API

This project uses two Bright Data API zones:

| Zone | Purpose | Use Case |
|------|---------|----------|
| `serp_api2_searchengine` | SERP API | Google/Bing search (finding websites) |
| `mcp_unlocker` | Web Unlocker | Website scraping (extracting emails/phones) |

### SERP API (Google Search)
Use for searching Google to find company websites:

```bash
curl https://api.brightdata.com/request \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "zone": "serp_api2_searchengine",
    "url": "https://www.google.com/search?q=company+name",
    "format": "raw"
  }'
```

### Web Unlocker API (Website Scraping)
Use to scrape any URL with automatic CAPTCHA solving and anti-bot bypass:

```bash
curl https://api.brightdata.com/request \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "zone": "mcp_unlocker",
    "url": "https://example.com",
    "format": "raw"
  }'
```

### Parameters
| Parameter | Description |
|-----------|-------------|
| `zone` | Bright Data zone: `serp_api2_searchengine` or `mcp_unlocker` |
| `url` | Target URL to scrape |
| `format` | Response format: `raw` (HTML) or `json` |

### Test Connection
```bash
curl https://api.brightdata.com/request \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "zone": "mcp_unlocker",
    "url": "https://geo.brdtest.com/welcome.txt?product=unlocker&method=api",
    "format": "raw"
  }'
```

---

## Code Style

- **Multi-file architecture**: UI in `app.py`, service in `enrichment_service.py`, config in `config.py`
- **Background processing**: Service runs as subprocess, communicates via files
- **Progress persistence**: JSON state file enables crash recovery
- **Batch processing**: Companies processed in configurable batch sizes with rate limiting

---

## Design Guidelines

See `DESIGN.md` for comprehensive UI/UX guidelines. Key principles:

### Design Framework
Follow **Jakob Nielsen's 10 Usability Heuristics**:
1. Visibility of system status (show progress, loading states)
2. Match between system and real world (use familiar terms)
3. User control and freedom (provide stop/cancel options)
4. Consistency and standards (uniform button styles, spacing)
5. Error prevention (validate inputs, confirm destructive actions)
6. Recognition over recall (visible options, clear labels)
7. Flexibility and efficiency (keyboard shortcuts for power users)
8. Aesthetic and minimalist design (remove unnecessary elements)
9. Help users recover from errors (clear error messages)
10. Help and documentation (tooltips, info icons)

### Streamlit UI Patterns
- **Section headers**: Use `st.markdown` with styled `<p>` tags for consistent headers
- **Columns layout**: Use `st.columns()` for button groups and metrics
- **Status indicators**: Green for running/success, gray for stopped/inactive
- **Progress display**: Use `st.metric()` for stats, `st.progress()` for visual bars
- **Feedback**: `st.success()`, `st.warning()`, `st.error()` for user notifications

### Component Styling (CSS in app.py)
- **Primary buttons**: Blue gradient (`#4A90E2` to `#5BA0F2`)
- **Destructive buttons**: Red gradient (`#ef4444` to `#f87171`)
- **Cards/panels**: Light background (`#f8fafc`), subtle border, rounded corners
- **Info boxes**: Light blue background with left border accent

---

## Troubleshooting

### Issue: "Service is already running"
**Solution**: Check for stale PID file at `.enrichment_service.pid`. Delete if service is not actually running.

### Issue: Enrichment not finding data
**Solution**:
- For emails: Ensure companies have valid websites first
- For websites: Company name + city helps Google search accuracy
- Check `enrichment.log` for detailed error messages

### Issue: Service stops unexpectedly
**Solution**: Check `enrichment.log` for errors. Progress is saved - restart service to resume.

---

## Resources

### External Dependencies Documentation
- [Streamlit Docs](https://docs.streamlit.io/)
- [Bright Data API](https://docs.brightdata.com/api-reference)
- [Google Gemini AI](https://ai.google.dev/docs)
- [Pandas Documentation](https://pandas.pydata.org/docs/)

### Design Resources
- [Jakob Nielsen's 10 Usability Heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/)
- [WCAG 2.1 Accessibility Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
