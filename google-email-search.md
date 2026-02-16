# Plan: Add Google Search for Emails

## Overview
Add a second email finding method that searches Google directly for company emails, in addition to the current website scraping approach.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EMAIL ENRICHMENT FLOW                               │
└─────────────────────────────────────────────────────────────────────────────┘

                            ┌──────────────┐
                            │   Company    │
                            │  Name + City │
                            └──────┬───────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │  METHOD 1: Google Search     │
                    │  ┌────────────────────────┐  │
                    │  │ Query: "{company}      │  │
                    │  │  {city} email contact" │  │
                    │  └───────────┬────────────┘  │
                    │              ▼               │
                    │  ┌────────────────────────┐  │
                    │  │ Parse search snippets  │  │
                    │  │ for email patterns     │  │
                    │  └───────────┬────────────┘  │
                    └──────────────┼───────────────┘
                                   │
                          ┌────────┴────────┐
                          ▼                 ▼
                    ┌──────────┐      ┌──────────┐
                    │  FOUND   │      │NOT FOUND │
                    │  Email   │      │          │
                    └────┬─────┘      └────┬─────┘
                         │                 │
                         │                 ▼
                         │   ┌──────────────────────────────┐
                         │   │  METHOD 2: Website Scrape    │
                         │   │  ┌────────────────────────┐  │
                         │   │  │ Find website via       │  │
                         │   │  │ Google search          │  │
                         │   │  └───────────┬────────────┘  │
                         │   │              ▼               │
                         │   │  ┌────────────────────────┐  │
                         │   │  │ Scrape homepage +      │  │
                         │   │  │ /contact /about pages  │  │
                         │   │  └───────────┬────────────┘  │
                         │   │              ▼               │
                         │   │  ┌────────────────────────┐  │
                         │   │  │ Extract emails from    │  │
                         │   │  │ HTML content           │  │
                         │   │  └───────────┬────────────┘  │
                         │   └──────────────┼───────────────┘
                         │                  │
                         │         ┌────────┴────────┐
                         │         ▼                 ▼
                         │   ┌──────────┐      ┌──────────┐
                         │   │  FOUND   │      │NOT FOUND │
                         │   │  Email   │      │          │
                         │   └────┬─────┘      └────┬─────┘
                         │        │                 │
                         ▼        ▼                 ▼
                    ┌─────────────────────────────────────┐
                    │              RESULT                 │
                    ├─────────────────────────────────────┤
                    │  ✓ Email Found  │  ✗ Not Found     │
                    │    info@...     │    (logged)      │
                    └─────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                           BRIGHT DATA MCP API                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐                    ┌──────────────────┐               │
│   │  search_engine  │                    │ scrape_as_markdown│              │
│   │                 │                    │                  │               │
│   │  Google/Bing    │                    │  Any URL         │               │
│   │  search results │                    │  → HTML → Text   │               │
│   └─────────────────┘                    └──────────────────┘               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Current Flow
```
Website Search → Website Scrape → Extract Email from HTML
```

## New Flow (Two Methods)
```
Method 1: Google Email Search (NEW)
  → Search Google: "{company} {city} email contact"
  → Extract emails from search result snippets

Method 2: Website Scrape (existing)
  → Find website → Scrape pages → Extract emails

Combined: Try Google first, fall back to website scraping if not found
```

---

## Implementation Details

### 1. Add `GoogleEmailFinder` class in `enrichment_service.py`

**Location:** After `EmailEnricher` class (around line 430)

```python
class GoogleEmailFinder:
    """Finds company emails by searching Google directly."""

    EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

    EXCLUDE_PATTERNS = [
        'example.com', 'test.com', 'email.com', 'domain.com',
        'yourcompany.', 'company.com', 'website.com',
        'wixpress.com', 'wordpress.com', 'squarespace.com',
        'noreply@', 'no-reply@', 'support@google', 'support@facebook'
    ]

    def __init__(self, mcp_client: BrightDataMCP):
        self.mcp = mcp_client

    def find_email(self, company_name: str, city: str = "") -> str:
        """Search Google for company email."""

        # Try multiple search queries
        queries = [
            f'"{company_name}" email contact',
            f'"{company_name}" {city} email',
            f'{company_name} contact email address',
        ]

        for query in queries:
            results = self.mcp.search_engine(query)
            email = self._extract_email_from_results(results, company_name)
            if email:
                return email

        return ""

    def _extract_email_from_results(self, results: list[dict], company_name: str) -> str:
        """Extract email from Google search result snippets."""
        all_emails = []

        for result in results:
            # Check title, description, and link
            text = f"{result.get('title', '')} {result.get('description', '')}"
            emails = self.EMAIL_PATTERN.findall(text)

            for email in emails:
                if not any(excl in email.lower() for excl in self.EXCLUDE_PATTERNS):
                    all_emails.append(email.lower())

        if not all_emails:
            return ""

        # Deduplicate and select best
        all_emails = list(set(all_emails))

        # Prefer emails matching company name
        company_words = company_name.lower().split()
        for email in all_emails:
            domain = email.split('@')[1]
            if any(word in domain for word in company_words if len(word) > 3):
                return email

        # Return first valid email
        return all_emails[0] if all_emails else ""
```

---

### 2. Update `enrich_emails()` method

**Location:** `enrich_emails()` method (around line 750)

**Current logic:**
```python
content = self.mcp.scrape_as_markdown(website)
email = self.email_enricher.extract_emails(content, website)
```

**New logic:**
```python
# Method 1: Try Google search for email first
email = self.google_email_finder.find_email(name, city)

if not email:
    # Method 2: Fall back to website scraping
    content = self.mcp.scrape_as_markdown(website)
    email = self.email_enricher.extract_emails(content, website)
```

---

### 3. Update `EnrichmentService.__init__()`

Add initialization of the new class:

```python
def __init__(self, ...):
    ...
    self.google_email_finder = GoogleEmailFinder(self.mcp)
```

---

## Benefits

| Approach | Pros | Cons |
|----------|------|------|
| Google Search | Fast, finds emails from directories, doesn't need website | May find outdated emails, less reliable |
| Website Scrape | Most accurate, current | Slower, may not find if hidden |
| **Combined** | Best of both worlds | Slightly more API calls |

---

## Files to Modify

| File | Changes |
|------|---------|
| `enrichment_service.py` | Add `GoogleEmailFinder` class, update `enrich_emails()` |

---

## Testing

1. Run email enrichment on a few companies
2. Check logs for "Found via Google" vs "Found via website"
3. Verify email quality (company domain match)
