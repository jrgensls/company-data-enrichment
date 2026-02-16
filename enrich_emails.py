#!/usr/bin/env python3
"""
Email enrichment script - scrapes company websites to find email addresses.
Continues from where the previous run left off.
"""

import csv
import re
import time
import requests
from typing import Optional

# Bright Data API configuration
BRIGHT_DATA_API_URL = "https://api.brightdata.com/request"

def extract_emails_from_text(text: str) -> list[str]:
    """Extract email addresses from text using regex."""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    # Filter out common false positives
    filtered = []
    for email in emails:
        email_lower = email.lower()
        # Skip image files, example emails, etc.
        if any(x in email_lower for x in ['.png', '.jpg', '.gif', '.svg', 'example.', 'your@', 'email@']):
            continue
        filtered.append(email)
    return list(set(filtered))

def get_best_email(emails: list[str], domain: str) -> str:
    """Select the best email from a list, preferring info@ and matching domain."""
    if not emails:
        return ""

    domain_base = domain.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]

    # Priority: info@ with matching domain > other@ with matching domain > info@ any > first email
    matching_domain = [e for e in emails if domain_base in e.lower()]

    for email in matching_domain:
        if email.lower().startswith('info@'):
            return email

    if matching_domain:
        return matching_domain[0]

    for email in emails:
        if email.lower().startswith('info@'):
            return email

    return emails[0]

def load_source_data(filepath: str) -> list[dict]:
    """Load companies from source CSV."""
    companies = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            companies.append(row)
    return companies

def load_existing_emails(filepath: str) -> dict[str, str]:
    """Load already processed companies from emails CSV."""
    processed = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                processed[row['Name']] = row.get('Email', '')
    except FileNotFoundError:
        pass
    return processed

def save_emails_csv(filepath: str, companies: list[dict]):
    """Save companies with emails to CSV."""
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Name', 'City', 'Website', 'Email'])
        writer.writeheader()
        for company in companies:
            writer.writerow(company)

def main():
    source_file = '/Users/jurgensuls/Projects/company-data-enrichment/companies_NOAB_websites_final.csv'
    output_file = '/Users/jurgensuls/Projects/company-data-enrichment/companies_NOAB_emails.csv'

    # Load data
    all_companies = load_source_data(source_file)
    existing = load_existing_emails(output_file)

    print(f"Total companies in source: {len(all_companies)}")
    print(f"Already processed: {len(existing)}")

    # Filter to companies with valid websites that haven't been processed
    to_process = []
    for company in all_companies:
        website = company.get('Website', '')
        if website and website != 'Not found' and company['Name'] not in existing:
            to_process.append(company)

    print(f"Remaining to process: {len(to_process)}")

    # Build result list with existing data first
    results = []
    for company in all_companies:
        website = company.get('Website', '')
        if website == 'Not found' or not website:
            continue  # Skip companies without websites

        email = existing.get(company['Name'], '')
        results.append({
            'Name': company['Name'],
            'City': company['City'],
            'Website': website,
            'Email': email
        })

    # Save initial state
    save_emails_csv(output_file, results)
    print(f"Saved initial state with {len(results)} companies")

    print(f"\nTo continue processing, run the scraping batches manually or use the Streamlit app.")
    print(f"Companies still needing email enrichment: {len(to_process)}")

    # Print first 20 to process
    print("\nNext companies to process:")
    for company in to_process[:20]:
        print(f"  - {company['Name']}: {company['Website']}")

if __name__ == '__main__':
    main()
