#!/usr/bin/env python3
"""
Update the emails CSV with scraped email addresses.
"""

import csv
import re

# Emails found from scraping batches
# Format: website_domain -> email
SCRAPED_EMAILS = {
    # Batch 1 (already in CSV)
    # Batch 2
    'administratiekantoorfransens.nl': '',  # Not found on homepage
    'verseput.nl': '',  # Not found on homepage
    'hootsen.nl': 'administratie@hootsen.nl',
    'ak-hss.nl': 'info@ak-hss.nl',
    'kuik-administratie.nl': 'info@kuik-administratie.nl',
    'jdehoon.nl': 'info@jdehoon.nl',
    'administratiejilesen.nl': 'info@administratiejilesen.nl',
    'jonkmanenvos.nl': 'info@jonkmanenvos.nl',
    'joopbolt.nl': 'info@joopbolt.nl',
    'kroezen-sieders.nl': 'info@kroezen-sieders.nl',
    # Batch 3
    'kantoorlaanen.nl': '',  # Not found
    'looijen-im.nl': '',  # Not found
    'administratiekantoor-martens.com': 'akmartens@hotmail.com',
    'nonstopadvies.nl': 'info@nonstopadvies.nl',
    'oosterkampfinance.nl': 'administratie@oosterkampfinance.nl',
    'opsave.nu': 'info@OpSave.nu',
    'oudshoorn.nl': 'info@oudshoorn.nl',
    'akpbv.nl': 'info@akpbv.nl',
    'administratiekantoorpetiet.nl': 'nadmin@petiet.nl',
    'schipperadministratie.nl': 'info@schipperadministratie.nl',
    # Batch 4
    'ba-lans.com': 'info@ba-lans.com',
    'aacbv.nl': 'info@aacbv.nl',
    'kantoorkromhout.nl': '',  # Not found
    'ajbrok.nl': 'arjan@ajbrok.nl',
    'avanrooijen.nl': '',  # Not found
    'a-drie.com': 'info@a-drie.com',
    'administratiekantoorask.nl': 'info@kantoorask.nl',
    'admitrust.nl': 'info@admitrust.nl',
    'admo-administratie.nl': 'Info@admo-administratie.nl',
    'bendersadviesgroep.nl': 'info@bendersadviesgroep.nl',
    # Batch 5
    'cajac.cc': '',  # No email on page
    'accountingcounts.nl': '',  # No email visible
    'schneiderbedrijfsadvies.nl': 'info@kantoorschneider.nl',
    'akslager.nl': 'info@akslager.nl',
    'administratiekantoorsucces.nl': 'info@administratiekantoorsucces.nl',
    'tddelier.nl': 'info@tddelier.nl',
    'htanis.nl': '',  # Empty page
    'schaapvanleeuwen.nl': '',  # Empty page
}

def get_domain(url):
    """Extract domain from URL."""
    if not url or url == 'Not found':
        return ''
    domain = url.replace('https://', '').replace('http://', '').replace('www.', '')
    return domain.split('/')[0]

def main():
    input_file = '/Users/jurgensuls/Projects/company-data-enrichment/companies_NOAB_emails.csv'
    output_file = '/Users/jurgensuls/Projects/company-data-enrichment/companies_NOAB_emails.csv'

    # Read existing data
    rows = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            domain = get_domain(row.get('Website', ''))

            # If no email yet, check if we scraped one
            if not row.get('Email') and domain in SCRAPED_EMAILS:
                row['Email'] = SCRAPED_EMAILS[domain]

            rows.append(row)

    # Write updated data
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Name', 'City', 'Website', 'Email'])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    # Count stats
    with_email = sum(1 for r in rows if r.get('Email'))
    print(f"Total companies: {len(rows)}")
    print(f"With email: {with_email}")
    print(f"Without email: {len(rows) - with_email}")

if __name__ == '__main__':
    main()
