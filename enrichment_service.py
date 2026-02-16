#!/usr/bin/env python3
"""
Automated Company Enrichment Service

Uses Bright Data MCP-style APIs for web scraping:
- search_engine: Google search for finding company websites
- scrape_as_markdown: Clean content extraction for emails/phones

Usage:
    python enrichment_service.py              # Run full enrichment
    python enrichment_service.py --emails-only    # Only enrich emails
    python enrichment_service.py --websites-only  # Only enrich websites
    python enrichment_service.py --phones-only    # Only enrich phones
    python enrichment_service.py --reset          # Reset progress and start fresh
    python enrichment_service.py --dry-run        # Show what would be processed
"""

import argparse
import csv
import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import requests
from dotenv import load_dotenv

# Load environment variables BEFORE importing config
load_dotenv()

import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ProgressTracker:
    """Manages state persistence for crash recovery and resume capability."""

    def __init__(self, progress_file: Path = config.PROGRESS_FILE):
        self.progress_file = progress_file
        self.state = self._load_state()

    def _load_state(self) -> dict:
        """Load progress from JSON file or return default state."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load progress file: {e}. Starting fresh.")

        return {
            "current_phase": "website",
            "processed_emails": {},
            "processed_phones": {},
            "processed_websites": {},
            "failures": [],
            "started_at": None,
            "last_updated": None,
            "stats": {
                "emails_found": 0,
                "emails_not_found": 0,
                "phones_found": 0,
                "phones_not_found": 0,
                "websites_found": 0,
                "websites_not_found": 0
            }
        }

    def save(self):
        """Save current state to JSON file."""
        self.state["last_updated"] = datetime.now().isoformat()
        with open(self.progress_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def mark_email_processed(self, company_name: str, email: str):
        self.state["processed_emails"][company_name] = email
        if email and email != "Not found":
            self.state["stats"]["emails_found"] += 1
        else:
            self.state["stats"]["emails_not_found"] += 1
        self.save()

    def mark_phone_processed(self, company_name: str, phone: str):
        self.state["processed_phones"][company_name] = phone
        if phone and phone != "Not found":
            self.state["stats"]["phones_found"] += 1
        else:
            self.state["stats"]["phones_not_found"] += 1
        self.save()

    def mark_website_processed(self, company_name: str, website: str):
        self.state["processed_websites"][company_name] = website
        if website and website != "Not found":
            self.state["stats"]["websites_found"] += 1
        else:
            self.state["stats"]["websites_not_found"] += 1
        self.save()

    def mark_failure(self, company_name: str, error: str):
        self.state["failures"].append({
            "company": company_name,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        self.save()

    def is_email_processed(self, company_name: str) -> bool:
        return company_name in self.state["processed_emails"]

    def is_phone_processed(self, company_name: str) -> bool:
        return company_name in self.state["processed_phones"]

    def is_website_processed(self, company_name: str) -> bool:
        return company_name in self.state.get("processed_websites", {})

    def get_email(self, company_name: str) -> Optional[str]:
        return self.state["processed_emails"].get(company_name)

    def get_phone(self, company_name: str) -> Optional[str]:
        return self.state["processed_phones"].get(company_name)

    def get_website(self, company_name: str) -> Optional[str]:
        return self.state.get("processed_websites", {}).get(company_name)

    def reset(self):
        self.state = {
            "current_phase": "website",
            "processed_emails": {},
            "processed_phones": {},
            "processed_websites": {},
            "failures": [],
            "started_at": None,
            "last_updated": None,
            "stats": {
                "emails_found": 0,
                "emails_not_found": 0,
                "phones_found": 0,
                "phones_not_found": 0,
                "websites_found": 0,
                "websites_not_found": 0
            }
        }
        if self.progress_file.exists():
            self.progress_file.unlink()

    def start_session(self):
        if not self.state["started_at"]:
            self.state["started_at"] = datetime.now().isoformat()
        self.save()


class BrightDataMCP:
    """
    Bright Data MCP-style API client.

    Uses the same endpoints as the MCP server:
    - search_engine: Google/Bing search with structured results
    - scrape_as_markdown: Clean markdown extraction from any URL
    """

    # MCP Server endpoint
    MCP_BASE_URL = "https://mcp.brightdata.com"

    def __init__(self, api_token: str = None):
        import os
        self.api_token = api_token or os.getenv("BRIGHT_DATA_API_KEY", "")

        if not self.api_token:
            logger.warning("Bright Data API token not configured.")

    def search_engine(self, query: str, engine: str = "google") -> list[dict]:
        """
        Search Google/Bing and return structured results.

        Returns list of: {"link": url, "title": title, "description": desc}
        """
        if not self.api_token:
            # Fallback to direct Google scrape
            return self._direct_google_search(query)

        try:
            # Use SERP API for Google search (optimized for search engines)
            search_url = f"https://www.google.com/search?q={quote(query)}"

            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            payload = {
                "zone": config.BRIGHT_DATA_SERP_ZONE,  # Use SERP zone for search
                "url": search_url,
                "format": "raw"
            }

            response = requests.post(
                config.BRIGHT_DATA_API_URL,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()

            html = response.text
            return self._parse_google_results(html)

        except requests.RequestException as e:
            logger.debug(f"SERP API search failed for '{query}': {e}")
            # Fallback to direct search if SERP fails
            return self._direct_google_search(query)

    def _parse_google_results(self, html: str) -> list[dict]:
        """Parse Google search results HTML into structured data."""
        results = []

        # Find URLs in search results (simplified parsing)
        # Look for patterns like href="/url?q=https://example.com
        url_pattern = re.compile(r'href="/url\?q=(https?://[^&"]+)')
        urls = url_pattern.findall(html)

        # Also try direct URL patterns in result divs
        direct_pattern = re.compile(r'<a[^>]+href="(https?://(?!google|gstatic|youtube|schema)[^"]+)"[^>]*>')
        direct_urls = direct_pattern.findall(html)

        all_urls = urls + direct_urls

        # Deduplicate and filter
        seen = set()
        for url in all_urls:
            # Clean URL
            url = url.split('&')[0]  # Remove tracking params

            if url in seen:
                continue
            seen.add(url)

            # Skip Google/social media URLs
            skip_domains = ['google.', 'gstatic.', 'youtube.', 'facebook.',
                           'twitter.', 'linkedin.', 'instagram.', 'wikipedia.']
            if any(d in url.lower() for d in skip_domains):
                continue

            results.append({
                "link": url,
                "title": "",
                "description": ""
            })

            if len(results) >= 10:
                break

        return results

    def _direct_google_search(self, query: str) -> list[dict]:
        """Fallback: Direct Google search without API."""
        try:
            search_url = f"https://www.google.com/search?q={quote(query)}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }

            response = requests.get(search_url, headers=headers, timeout=30)
            response.raise_for_status()

            return self._parse_google_results(response.text)

        except requests.RequestException as e:
            logger.debug(f"Direct Google search failed: {e}")
            return []

    def scrape_as_markdown(self, url: str) -> Optional[str]:
        """
        Scrape a URL and return clean markdown content.

        Handles bot protection, CAPTCHAs, etc. via Bright Data.
        """
        if not self.api_token:
            return self._direct_scrape(url)

        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            payload = {
                "zone": config.BRIGHT_DATA_ZONE,
                "url": url,
                "format": "raw"
            }

            response = requests.post(
                config.BRIGHT_DATA_API_URL,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()

            html = response.text

            # Convert HTML to simple text (pseudo-markdown)
            return self._html_to_text(html)

        except requests.RequestException as e:
            logger.debug(f"Scrape failed for {url}: {e}")
            return self._direct_scrape(url)

    def _direct_scrape(self, url: str) -> Optional[str]:
        """Fallback: Direct HTTP request."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return self._html_to_text(response.text)
        except requests.RequestException as e:
            logger.debug(f"Direct scrape failed for {url}: {e}")
            return None

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text, preserving useful content."""
        if not html:
            return ""

        # Remove script and style elements
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

        # Remove HTML comments
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)

        # Replace common elements with text equivalents
        html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
        html = re.sub(r'<p[^>]*>', '\n', html, flags=re.IGNORECASE)
        html = re.sub(r'</p>', '\n', html, flags=re.IGNORECASE)
        html = re.sub(r'<div[^>]*>', '\n', html, flags=re.IGNORECASE)
        html = re.sub(r'</div>', '\n', html, flags=re.IGNORECASE)

        # Keep href content visible for URL extraction
        html = re.sub(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>', r'\2 (\1)', html, flags=re.IGNORECASE)

        # Remove remaining HTML tags
        html = re.sub(r'<[^>]+>', ' ', html)

        # Decode HTML entities
        html = html.replace('&nbsp;', ' ')
        html = html.replace('&amp;', '&')
        html = html.replace('&lt;', '<')
        html = html.replace('&gt;', '>')
        html = html.replace('&quot;', '"')

        # Clean up whitespace
        html = re.sub(r'\s+', ' ', html)
        html = re.sub(r'\n\s*\n', '\n\n', html)

        return html.strip()

    def scrape_batch(self, urls: list[str]) -> dict[str, Optional[str]]:
        """Scrape multiple URLs."""
        results = {}
        for url in urls:
            logger.debug(f"Scraping: {url}")
            results[url] = self.scrape_as_markdown(url)
            time.sleep(0.5)
        return results


class EmailEnricher:
    """Extracts email addresses from text/markdown content."""

    EMAIL_PATTERN = re.compile(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    )

    EXCLUDE_PATTERNS = [
        '.png', '.jpg', '.gif', '.svg', '.jpeg', '.webp',
        'example.', 'your@', 'email@', 'name@', 'user@',
        'test@', 'sample@', 'demo@', '@example', '@test',
        'wixpress.com', 'sentry.io', 'wordpress.com',
        'noreply@', 'no-reply@', 'donotreply@'
    ]

    PRIORITY_PREFIXES = ['info@', 'contact@', 'hello@', 'office@', 'admin@', 'sales@']

    def extract_emails(self, content: str, domain: str = "") -> str:
        """Extract the best email from content."""
        if not content:
            return ""

        emails = self.EMAIL_PATTERN.findall(content)

        valid_emails = []
        for email in emails:
            email_lower = email.lower()
            if not any(excl in email_lower for excl in self.EXCLUDE_PATTERNS):
                valid_emails.append(email.lower())

        valid_emails = list(set(valid_emails))

        if not valid_emails:
            return ""

        domain_base = self._get_domain_base(domain) if domain else ""
        return self._select_best_email(valid_emails, domain_base)

    def _get_domain_base(self, url: str) -> str:
        domain = url.replace('https://', '').replace('http://', '').replace('www.', '')
        return domain.split('/')[0].lower()

    def _select_best_email(self, emails: list[str], domain_base: str) -> str:
        if domain_base:
            matching_domain = [e for e in emails if domain_base in e]

            for prefix in self.PRIORITY_PREFIXES:
                for email in matching_domain:
                    if email.startswith(prefix):
                        return email

            if matching_domain:
                return matching_domain[0]

        for prefix in self.PRIORITY_PREFIXES:
            for email in emails:
                if email.startswith(prefix):
                    return email

        return emails[0]


class GoogleEmailFinder:
    """Finds company emails by searching Google directly."""

    EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

    EXCLUDE_PATTERNS = [
        'example.com', 'test.com', 'email.com', 'domain.com',
        'yourcompany.', 'company.com', 'website.com',
        'wixpress.com', 'wordpress.com', 'squarespace.com',
        'noreply@', 'no-reply@', 'support@google', 'support@facebook'
    ]

    def __init__(self, mcp_client):
        self.mcp = mcp_client

    def find_email(self, company_name: str, city: str = "") -> str:
        """Search Google for company email."""
        queries = [
            f'"{company_name}" email contact',
            f'"{company_name}" {city} email' if city else f'"{company_name}" email',
        ]

        for query in queries:
            try:
                results = self.mcp.search_engine(query)
                email = self._extract_email_from_results(results, company_name)
                if email:
                    logger.debug(f"Found email via Google for {company_name}: {email}")
                    return email
            except Exception as e:
                logger.debug(f"Google email search failed for {company_name}: {e}")

        return ""

    def _extract_email_from_results(self, results: list, company_name: str) -> str:
        """Extract email from Google search result snippets."""
        all_emails = []

        for result in results:
            text = f"{result.get('title', '')} {result.get('description', '')}"
            emails = self.EMAIL_PATTERN.findall(text)

            for email in emails:
                if not any(excl in email.lower() for excl in self.EXCLUDE_PATTERNS):
                    all_emails.append(email.lower())

        if not all_emails:
            return ""

        all_emails = list(set(all_emails))

        # Prefer emails matching company name
        company_words = company_name.lower().split()
        for email in all_emails:
            domain = email.split('@')[1] if '@' in email else ''
            if any(word in domain for word in company_words if len(word) > 3):
                return email

        return all_emails[0] if all_emails else ""


class ProbableEmailGenerator:
    """Generates probable email addresses from website domains."""

    def generate(self, website: str, prefix: str = 'info') -> str:
        """Generate probable email from website URL.

        Args:
            website: Company website URL (e.g., https://www.example.nl)
            prefix: Email prefix to use (default: 'info')

        Returns:
            Probable email (e.g., info@example.nl) or empty string
        """
        if not website or website == 'Not found':
            return ""

        domain = self._extract_domain(website)
        if not domain:
            return ""

        return f"{prefix}@{domain}"

    def _extract_domain(self, url: str) -> str:
        """Extract clean domain from URL."""
        domain = url.lower()
        domain = domain.replace('https://', '').replace('http://', '')
        domain = domain.replace('www.', '')
        domain = domain.split('/')[0]
        domain = domain.split(':')[0]
        return domain if '.' in domain else ""


class PhoneEnricher:
    """Extracts Dutch phone numbers from text content."""

    DUTCH_PATTERNS = [
        re.compile(r'\+31[\s.-]?(?:\(0\))?[\s.-]?\d{1,2}[\s.-]?\d{3}[\s.-]?\d{4}'),
        re.compile(r'0\d{2}[\s.-]?\d{3}[\s.-]?\d{4}'),
        re.compile(r'06[\s.-]?\d{4}[\s.-]?\d{4}'),
        re.compile(r'\(0\d{2}\)[\s.-]?\d{3}[\s.-]?\d{4}'),
        re.compile(r'0\d{9}'),
    ]

    def extract_phone(self, content: str) -> str:
        """Extract the best phone number from content."""
        if not content:
            return ""

        all_phones = []
        for pattern in self.DUTCH_PATTERNS:
            matches = pattern.findall(content)
            all_phones.extend(matches)

        if not all_phones:
            return ""

        valid_phones = []
        for phone in all_phones:
            cleaned = self._clean_phone(phone)
            if self._is_valid_dutch_phone(cleaned):
                valid_phones.append(cleaned)

        if not valid_phones:
            return ""

        valid_phones = list(dict.fromkeys(valid_phones))
        return self._format_phone(valid_phones[0])

    def _clean_phone(self, phone: str) -> str:
        return re.sub(r'[\s.\-()]+', '', phone)

    def _is_valid_dutch_phone(self, phone: str) -> bool:
        if phone.startswith('+31'):
            phone = '0' + phone[3:]

        if not phone.startswith('0'):
            return False

        digits_only = re.sub(r'\D', '', phone)
        return len(digits_only) == 10

    def _format_phone(self, phone: str) -> str:
        digits = re.sub(r'\D', '', phone)

        if phone.startswith('+31'):
            digits = '0' + digits[2:]
        elif digits.startswith('31') and len(digits) == 11:
            digits = '0' + digits[2:]

        if len(digits) == 10:
            return f"{digits[:3]}-{digits[3:6]} {digits[6:]}"

        return phone


class WebsiteEnricher:
    """Finds company websites using Google search via MCP."""

    EXCLUDE_DOMAINS = [
        'facebook.com', 'linkedin.com', 'twitter.com', 'instagram.com',
        'youtube.com', 'tiktok.com', 'pinterest.com', 'x.com',
        'yelp.com', 'yellowpages.com', 'glassdoor.com', 'indeed.com',
        'wikipedia.org', 'crunchbase.com', 'bloomberg.com',
        'kvk.nl', 'openkvk.nl', 'companyweb.be', 'companyinfo.nl',
        'google.com', 'google.nl', 'bing.com'
    ]

    def __init__(self, mcp_client: BrightDataMCP):
        self.mcp = mcp_client

    def find_website(self, company_name: str, city: str = "") -> str:
        """Search Google for company website using MCP search_engine."""

        # Build search query
        query = f"{company_name} official website"
        if city:
            query = f"{company_name} {city} official website"

        logger.debug(f"Searching: {query}")

        try:
            results = self.mcp.search_engine(query)

            if not results:
                # Try simpler query
                query = company_name if not city else f"{company_name} {city}"
                results = self.mcp.search_engine(query)

            if results:
                return self._select_best_website(results, company_name)

        except Exception as e:
            logger.debug(f"Website search failed for {company_name}: {e}")

        return ""

    def _select_best_website(self, results: list[dict], company_name: str) -> str:
        """Select the most likely company website from search results."""

        company_words = set(company_name.lower().split())
        scored_results = []

        for result in results:
            url = result.get("link", "")
            if not url:
                continue

            # Skip excluded domains
            url_lower = url.lower()
            if any(excl in url_lower for excl in self.EXCLUDE_DOMAINS):
                continue

            # Score based on company name in domain
            score = 0
            domain = url_lower.replace('https://', '').replace('http://', '').replace('www.', '')
            domain = domain.split('/')[0]

            for word in company_words:
                if len(word) > 2 and word in domain:
                    score += 10

            # Prefer .nl, .com domains
            if domain.endswith('.nl'):
                score += 5
            elif domain.endswith('.com'):
                score += 3

            scored_results.append((url, score))

        if not scored_results:
            return ""

        # Sort by score
        scored_results.sort(key=lambda x: x[1], reverse=True)

        # Return best match (or first result if no good match)
        best_url = scored_results[0][0]

        # Normalize URL
        if not best_url.startswith('http'):
            best_url = 'https://' + best_url

        return best_url


class EnrichmentService:
    """Main orchestrator using Bright Data MCP APIs."""

    def __init__(self,
                 input_csv: Path = None,
                 output_csv: Path = config.OUTPUT_CSV,
                 batch_size: int = config.BATCH_SIZE):
        self.input_csv = input_csv if input_csv else config.get_input_file()
        self.output_csv = output_csv
        self.batch_size = batch_size

        self.tracker = ProgressTracker()
        self.mcp = BrightDataMCP()
        self.email_enricher = EmailEnricher()
        self.phone_enricher = PhoneEnricher()
        self.website_enricher = WebsiteEnricher(self.mcp)
        self.google_email_finder = GoogleEmailFinder(self.mcp)

        self.companies = []

    def load_companies(self) -> list[dict]:
        """Load companies from input CSV."""
        companies = []
        with open(self.input_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                companies.append(dict(row))

        logger.info(f"Loaded {len(companies)} companies from {self.input_csv}")
        self.companies = companies
        return companies

    def run(self, emails_only: bool = False, phones_only: bool = False,
            websites_only: bool = False, dry_run: bool = False):
        """Run the enrichment process."""
        self.load_companies()
        self.tracker.start_session()

        if dry_run:
            self._show_dry_run(emails_only, phones_only, websites_only)
            return

        if websites_only:
            self.enrich_websites()
        elif emails_only:
            # Emails require websites first - enrich websites if needed
            websites_needed = len(self._get_companies_needing_website())
            if websites_needed > 0:
                logger.info(f"Finding websites first for {websites_needed} companies...")
                self.enrich_websites()
            self.enrich_emails()
        elif phones_only:
            # Phones require websites first - enrich websites if needed
            websites_needed = len(self._get_companies_needing_website())
            if websites_needed > 0:
                logger.info(f"Finding websites first for {websites_needed} companies...")
                self.enrich_websites()
            self.enrich_phones()
        else:
            # Full enrichment: websites first, then emails, then phones
            self.enrich_websites()
            self.enrich_emails()
            self.enrich_phones()

        self.export_final_csv()
        self.print_summary()

    def _show_dry_run(self, emails_only: bool, phones_only: bool, websites_only: bool = False):
        """Show what would be processed."""
        logger.info("=== DRY RUN MODE ===")

        if websites_only:
            pending = self._get_companies_needing_website()
            logger.info(f"Companies needing website enrichment: {len(pending)}")
        elif emails_only:
            pending = self._get_companies_needing_email()
            logger.info(f"Companies needing email enrichment: {len(pending)}")
        elif phones_only:
            pending = self._get_companies_needing_phone()
            logger.info(f"Companies needing phone enrichment: {len(pending)}")
        else:
            logger.info(f"Websites needed: {len(self._get_companies_needing_website())}")
            logger.info(f"Emails needed: {len(self._get_companies_needing_email())}")
            logger.info(f"Phones needed: {len(self._get_companies_needing_phone())}")

        logger.info("=== END DRY RUN ===")

    def _get_companies_needing_email(self) -> list[dict]:
        pending = []
        for company in self.companies:
            name = company.get('Name', '')
            website = company.get('Website', '') or self.tracker.get_website(name) or ''
            existing_email = company.get('Email', '')

            if not website or website == 'Not found':
                continue
            if existing_email and existing_email.strip():
                continue
            if self.tracker.is_email_processed(name):
                continue

            pending.append(company)
        return pending

    def _get_companies_needing_phone(self) -> list[dict]:
        pending = []
        for company in self.companies:
            name = company.get('Name', '')
            website = company.get('Website', '') or self.tracker.get_website(name) or ''

            if not website or website == 'Not found':
                continue
            if self.tracker.is_phone_processed(name):
                continue

            pending.append(company)
        return pending

    def _get_companies_needing_website(self) -> list[dict]:
        pending = []
        for company in self.companies:
            name = company.get('Name', '')
            website = company.get('Website', '')

            if website and website != 'Not found' and website.strip():
                continue
            if self.tracker.is_website_processed(name):
                continue

            pending.append(company)
        return pending

    def enrich_websites(self):
        """Find websites for companies using Google search."""
        logger.info("=" * 50)
        logger.info("PHASE 1: WEBSITE ENRICHMENT (Google Search)")
        logger.info("=" * 50)

        pending = self._get_companies_needing_website()
        total = len(pending)

        if total == 0:
            logger.info("No companies need website enrichment. Skipping.")
            return

        logger.info(f"Companies to process: {total}")
        processed = 0

        for company in pending:
            name = company.get('Name', '')
            city = company.get('City', '')

            try:
                website = self.website_enricher.find_website(name, city)
                self.tracker.mark_website_processed(name, website or "Not found")

                status = website if website else "Not found"
                logger.info(f"  {name}: {status}")

            except Exception as e:
                logger.error(f"  {name}: ERROR - {e}")
                self.tracker.mark_failure(name, str(e))
                self.tracker.mark_website_processed(name, "Not found")

            processed += 1
            if processed % 10 == 0:
                logger.info(f"Progress: {processed}/{total}")
                time.sleep(config.RATE_LIMIT_DELAY)

        logger.info(f"\nWebsite enrichment complete! {processed}/{total}")

    def enrich_emails(self):
        """Extract emails using Google search first, then website scraping as fallback."""
        logger.info("=" * 50)
        logger.info("PHASE 2: EMAIL ENRICHMENT (Google + Website Scraping)")
        logger.info("=" * 50)

        pending = self._get_companies_needing_email()
        total = len(pending)

        if total == 0:
            logger.info("No companies need email enrichment. Skipping.")
            return

        logger.info(f"Companies to process: {total}")
        processed = 0
        google_found = 0
        website_found = 0

        for company in pending:
            name = company.get('Name', '')
            city = company.get('City', '')
            website = company.get('Website', '') or self.tracker.get_website(name) or ''

            try:
                email = ""

                # METHOD 1: Try Google search for email first
                email = self.google_email_finder.find_email(name, city)
                if email:
                    google_found += 1
                    logger.info(f"  {name}: {email} (via Google)")
                else:
                    # METHOD 2: Fall back to website scraping
                    if website and website != 'Not found':
                        content = self.mcp.scrape_as_markdown(website)

                        if content:
                            email = self.email_enricher.extract_emails(content, website)

                        # Try contact pages if no email found
                        if not email:
                            for contact_path in ['/contact', '/kontakt', '/about', '/over-ons']:
                                contact_url = website.rstrip('/') + contact_path
                                contact_content = self.mcp.scrape_as_markdown(contact_url)
                                if contact_content:
                                    email = self.email_enricher.extract_emails(contact_content, website)
                                    if email:
                                        break

                        if email:
                            website_found += 1
                            logger.info(f"  {name}: {email} (via website)")
                        else:
                            logger.info(f"  {name}: Not found")
                    else:
                        logger.info(f"  {name}: Not found (no website)")

                self.tracker.mark_email_processed(name, email or "Not found")

            except Exception as e:
                logger.error(f"  {name}: ERROR - {e}")
                self.tracker.mark_failure(name, str(e))
                self.tracker.mark_email_processed(name, "Not found")

            processed += 1
            if processed % 10 == 0:
                logger.info(f"Progress: {processed}/{total} (Google: {google_found}, Website: {website_found})")
                time.sleep(config.RATE_LIMIT_DELAY)

        logger.info(f"\nEmail enrichment complete! {processed}/{total}")
        logger.info(f"  Found via Google: {google_found}")
        logger.info(f"  Found via Website: {website_found}")

    def enrich_phones(self):
        """Extract phone numbers from company websites."""
        logger.info("=" * 50)
        logger.info("PHASE 3: PHONE ENRICHMENT (Website Scraping)")
        logger.info("=" * 50)

        pending = self._get_companies_needing_phone()
        total = len(pending)

        if total == 0:
            logger.info("No companies need phone enrichment. Skipping.")
            return

        logger.info(f"Companies to process: {total}")
        processed = 0

        for company in pending:
            name = company.get('Name', '')
            website = company.get('Website', '') or self.tracker.get_website(name) or ''

            try:
                content = self.mcp.scrape_as_markdown(website)
                phone = ""

                if content:
                    phone = self.phone_enricher.extract_phone(content)

                if not phone:
                    for contact_path in ['/contact', '/kontakt', '/about', '/over-ons']:
                        contact_url = website.rstrip('/') + contact_path
                        contact_content = self.mcp.scrape_as_markdown(contact_url)
                        if contact_content:
                            phone = self.phone_enricher.extract_phone(contact_content)
                            if phone:
                                break

                self.tracker.mark_phone_processed(name, phone or "Not found")

                status = phone if phone else "Not found"
                logger.info(f"  {name}: {status}")

            except Exception as e:
                logger.error(f"  {name}: ERROR - {e}")
                self.tracker.mark_failure(name, str(e))
                self.tracker.mark_phone_processed(name, "Not found")

            processed += 1
            if processed % 10 == 0:
                logger.info(f"Progress: {processed}/{total}")
                time.sleep(config.RATE_LIMIT_DELAY)

        logger.info(f"\nPhone enrichment complete! {processed}/{total}")

    def export_final_csv(self):
        """Export enriched data to CSV with probable email column."""
        logger.info("\nExporting final CSV...")

        output_path = config.get_output_filename()
        prob_email_gen = ProbableEmailGenerator()

        enriched = []
        for company in self.companies:
            name = company.get('Name', '')

            website = company.get('Website', '')
            if not website or website == 'Not found':
                website = self.tracker.get_website(name) or ''

            email = company.get('Email', '') or self.tracker.get_email(name) or ''

            # Generate probable email from website
            probable_email = prob_email_gen.generate(website)

            row = {
                'Name': name,
                'City': company.get('City', ''),
                'Website': website if website != 'Not found' else '',
                'Email': email,
                'Probable_Email': probable_email,
                'Phone': self.tracker.get_phone(name) or ''
            }

            # Clean "Not found" values
            for key in ['Website', 'Email', 'Phone']:
                if row[key] == 'Not found':
                    row[key] = ''

            enriched.append(row)

        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['Name', 'City', 'Website', 'Email', 'Probable_Email', 'Phone'])
            writer.writeheader()
            writer.writerows(enriched)

        self.output_csv = output_path
        logger.info(f"Exported {len(enriched)} companies to {output_path}")

    def print_summary(self):
        """Print enrichment summary."""
        stats = self.tracker.state["stats"]

        logger.info("\n" + "=" * 50)
        logger.info("ENRICHMENT SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Websites found:   {stats.get('websites_found', 0)}")
        logger.info(f"Websites not found: {stats.get('websites_not_found', 0)}")
        logger.info(f"Emails found:     {stats.get('emails_found', 0)}")
        logger.info(f"Emails not found: {stats.get('emails_not_found', 0)}")
        logger.info(f"Phones found:     {stats.get('phones_found', 0)}")
        logger.info(f"Phones not found: {stats.get('phones_not_found', 0)}")
        logger.info(f"Total failures:   {len(self.tracker.state['failures'])}")
        logger.info(f"Output file:      {self.output_csv}")
        logger.info("=" * 50)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Company Enrichment Service using Bright Data MCP",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--emails-only', action='store_true', help='Only enrich emails')
    parser.add_argument('--phones-only', action='store_true', help='Only enrich phones')
    parser.add_argument('--websites-only', action='store_true', help='Only enrich websites')
    parser.add_argument('--reset', action='store_true', help='Reset progress')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed')
    parser.add_argument('--batch-size', type=int, default=config.BATCH_SIZE)

    args = parser.parse_args()

    only_flags = [args.emails_only, args.phones_only, args.websites_only]
    if sum(only_flags) > 1:
        parser.error("Cannot use multiple --*-only flags together")

    service = EnrichmentService(batch_size=args.batch_size)

    if args.reset:
        logger.info("Resetting all progress...")
        service.tracker.reset()
        logger.info("Progress reset.")
        return

    logger.info("Starting Enrichment Service (Bright Data MCP)...")
    logger.info(f"Input:  {service.input_csv}")
    logger.info(f"Output: {config.get_output_filename()}")

    try:
        service.run(
            emails_only=args.emails_only,
            phones_only=args.phones_only,
            websites_only=args.websites_only,
            dry_run=args.dry_run
        )
    except KeyboardInterrupt:
        logger.info("\nInterrupted. Progress saved.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise


if __name__ == '__main__':
    main()
