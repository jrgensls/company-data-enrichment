# Plan: Generate Probable Email from Website

## Overview
Add a new feature that generates a "probable email" based on the company's website domain. When a website is known but no email was found, suggest `info@domain.nl` as the most likely contact email.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PROBABLE EMAIL GENERATION                              │
└─────────────────────────────────────────────────────────────────────────────┘

     ┌───────────────────┐
     │  Company Website  │
     │  www.example.nl   │
     └─────────┬─────────┘
               │
               ▼
     ┌───────────────────┐
     │  Extract Domain   │
     │  example.nl       │
     └─────────┬─────────┘
               │
               ▼
     ┌───────────────────┐
     │ Generate Probable │
     │ info@example.nl   │
     └─────────┬─────────┘
               │
               ▼
     ┌───────────────────────────────────────┐
     │           OUTPUT CSV                  │
     ├───────────────────────────────────────┤
     │  Email         │  Probable_Email      │
     │  (scraped)     │  (generated)         │
     ├────────────────┼──────────────────────┤
     │  info@abc.nl   │  info@abc.nl         │  ← Same (verified)
     │  Not found     │  info@xyz.nl         │  ← Suggested
     │  hello@test.nl │  info@test.nl        │  ← Different prefix
     └────────────────┴──────────────────────┘
```

## Implementation Details

### 1. Add `ProbableEmailGenerator` class in `enrichment_service.py`

**Location:** After `GoogleEmailFinder` class

```python
class ProbableEmailGenerator:
    """Generates probable email addresses from website domains."""

    # Common email prefixes in order of probability
    COMMON_PREFIXES = ['info', 'contact', 'hello', 'office', 'admin', 'mail']

    def __init__(self):
        pass

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
        """Extract clean domain from URL.

        Examples:
            https://www.example.nl → example.nl
            http://example.nl/contact → example.nl
            www.example.nl → example.nl
        """
        # Remove protocol
        domain = url.lower()
        domain = domain.replace('https://', '').replace('http://', '')

        # Remove www.
        domain = domain.replace('www.', '')

        # Remove path
        domain = domain.split('/')[0]

        # Remove port
        domain = domain.split(':')[0]

        return domain if '.' in domain else ""
```

---

### 2. Add `Probable_Email` column to output CSV

**Update `export_final_csv()` method in `EnrichmentService`:**

```python
def export_final_csv(self):
    """Export enriched data to CSV with probable email column."""

    prob_email_gen = ProbableEmailGenerator()

    for company in self.companies:
        website = company.get('Website', '') or self.tracker.get_website(company['Name'])

        # Generate probable email from website
        probable_email = prob_email_gen.generate(website)
        company['Probable_Email'] = probable_email

    # ... rest of export logic
```

---

### 3. Update CSV column order

**New column order:**
```
Name, City, Website, Email, Probable_Email, Phone
```

---

### 4. Add UI indicator in Streamlit

**In `app.py` results preview:**

Show probable email with visual indicator when it differs from scraped email:

```python
# In results table
if row['Email'] == 'Not found' and row['Probable_Email']:
    st.markdown(f"📧 {row['Probable_Email']} *(suggested)*")
elif row['Email'] != row['Probable_Email']:
    st.markdown(f"✓ {row['Email']}")
```

---

## Output Example

### CSV Output (Two Columns)
| Name | Website | Email | Probable_Email |
|------|---------|-------|----------------|
| ABC BV | https://www.abc.nl | info@abc.nl | info@abc.nl |
| XYZ Corp | https://xyz.nl | Not found | info@xyz.nl |
| Test Co | https://test.com | hello@test.com | info@test.com |

### UI Preview (Combined View)
```
┌──────────────────────┬─────────────┬────────────────────────────────────────┐
│  Name                │  Website    │  Email                                 │
├──────────────────────┼─────────────┼────────────────────────────────────────┤
│  ABC BV              │  abc.nl     │  ✓ info@abc.nl                         │
│  XYZ Corp            │  xyz.nl     │  📧 info@xyz.nl (suggested)            │
│  Test Co             │  test.com   │  ✓ hello@test.com                      │
└──────────────────────┴─────────────┴────────────────────────────────────────┘

Legend:  ✓ = Verified (scraped)    📧 = Suggested (probable)
```

### Stats Banner
```
┌────────────────┐  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│     Found      │  │   Suggested    │  │   Not Found    │  │    Coverage    │
│      485       │  │      312       │  │      131       │  │      86%       │
│   (verified)   │  │   (probable)   │  │  (no website)  │  │                │
└────────────────┘  └────────────────┘  └────────────────┘  └────────────────┘
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `enrichment_service.py` | Add `ProbableEmailGenerator` class |
| `enrichment_service.py` | Update `export_final_csv()` to add column |
| `app.py` | Update results preview to show probable emails |
| `test_enrichment.py` | Add tests for `ProbableEmailGenerator` |

---

## Benefits

1. **Always have a contact option** - Even when scraping fails
2. **High accuracy** - `info@` is correct ~70% of the time
3. **No extra API calls** - Generated locally from website
4. **Clear distinction** - Separate column shows it's a suggestion

---

## Testing

```python
def test_generate_probable_email():
    gen = ProbableEmailGenerator()

    assert gen.generate("https://www.example.nl") == "info@example.nl"
    assert gen.generate("http://test.com/contact") == "info@test.com"
    assert gen.generate("www.company.nl") == "info@company.nl"
    assert gen.generate("") == ""
    assert gen.generate("Not found") == ""
```

---

## Future Enhancements

1. **Validate probable email** - Check if email actually exists (SMTP check)
2. **Multiple suggestions** - Generate list: info@, contact@, hello@
3. **Learn from data** - Analyze found emails to improve prefix prediction
