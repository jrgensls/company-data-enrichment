#!/usr/bin/env python3
"""
Tests for the enrichment service.

Run with: pytest test_enrichment.py -v
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

import config
from enrichment_service import (
    EmailEnricher,
    PhoneEnricher,
    GoogleEmailFinder,
    BrightDataMCP,
    ProgressTracker,
    ProbableEmailGenerator,
)


class TestEmailEnricher:
    """Tests for EmailEnricher class."""

    def setup_method(self):
        self.enricher = EmailEnricher()

    def test_extract_simple_email(self):
        content = "Contact us at info@companyabc.nl for more information."
        result = self.enricher.extract_emails(content)
        assert result == "info@companyabc.nl"

    def test_extract_multiple_emails_prefers_info(self):
        content = "Email john@companyabc.nl or info@companyabc.nl"
        result = self.enricher.extract_emails(content, "companyabc.nl")
        assert result == "info@companyabc.nl"

    def test_extract_multiple_emails_prefers_contact(self):
        content = "Email john@companyabc.nl or contact@companyabc.nl"
        result = self.enricher.extract_emails(content, "companyabc.nl")
        assert result == "contact@companyabc.nl"

    def test_exclude_noreply_emails(self):
        content = "Email noreply@companyabc.nl or info@companyabc.nl"
        result = self.enricher.extract_emails(content)
        assert result == "info@companyabc.nl"

    def test_exclude_image_emails(self):
        content = "icon@image.png info@companyabc.nl"
        result = self.enricher.extract_emails(content)
        assert result == "info@companyabc.nl"

    def test_no_email_found(self):
        content = "No contact information available."
        result = self.enricher.extract_emails(content)
        assert result == ""

    def test_empty_content(self):
        result = self.enricher.extract_emails("")
        assert result == ""

    def test_none_content(self):
        result = self.enricher.extract_emails(None)
        assert result == ""


class TestPhoneEnricher:
    """Tests for PhoneEnricher class."""

    def setup_method(self):
        self.enricher = PhoneEnricher()

    def test_extract_dutch_landline(self):
        content = "Bel ons op 020-123 4567"
        result = self.enricher.extract_phone(content)
        assert result == "020-123 4567"

    def test_extract_dutch_mobile(self):
        content = "Mobiel: 06-1234 5678"
        result = self.enricher.extract_phone(content)
        assert result == "061-234 5678"

    def test_extract_international_format(self):
        content = "Call +31 20 123 4567"
        result = self.enricher.extract_phone(content)
        assert result == "020-123 4567"

    def test_no_phone_found(self):
        content = "No phone number here."
        result = self.enricher.extract_phone(content)
        assert result == ""

    def test_empty_content(self):
        result = self.enricher.extract_phone("")
        assert result == ""


class TestGoogleEmailFinder:
    """Tests for GoogleEmailFinder class."""

    def setup_method(self):
        mock_mcp = Mock()
        mock_mcp.search_engine = Mock(return_value=[])
        self.finder = GoogleEmailFinder(mock_mcp)

    def test_extract_email_from_results(self):
        results = [
            {"title": "Company ABC", "description": "Contact: info@companyabc.nl"},
            {"title": "Other", "description": "No email here"},
        ]
        email = self.finder._extract_email_from_results(results, "Company ABC")
        assert email == "info@companyabc.nl"

    def test_prefer_company_domain_email(self):
        results = [
            {"title": "Company", "description": "general@other.com info@company.nl"},
        ]
        email = self.finder._extract_email_from_results(results, "Company")
        assert email == "info@company.nl"

    def test_exclude_generic_emails(self):
        results = [
            {"title": "Test", "description": "noreply@example.com info@real.nl"},
        ]
        email = self.finder._extract_email_from_results(results, "Test")
        assert email == "info@real.nl"

    def test_no_email_in_results(self):
        results = [
            {"title": "Company", "description": "No email here"},
        ]
        email = self.finder._extract_email_from_results(results, "Company")
        assert email == ""


class TestBrightDataMCP:
    """Tests for BrightDataMCP class."""

    def test_init_without_token(self):
        with patch.dict(os.environ, {"BRIGHT_DATA_API_KEY": ""}):
            mcp = BrightDataMCP(api_token="")
            assert mcp.api_token == ""

    def test_init_with_token(self):
        mcp = BrightDataMCP(api_token="test-token")
        assert mcp.api_token == "test-token"

    def test_parse_google_results(self):
        mcp = BrightDataMCP(api_token="test")
        html = '''
        <a href="/url?q=https://example.com&amp;sa=U">Example</a>
        <a href="/url?q=https://test.nl&amp;sa=U">Test</a>
        '''
        results = mcp._parse_google_results(html)
        assert len(results) >= 1
        assert any("example.com" in r["link"] for r in results)


class TestProgressTracker:
    """Tests for ProgressTracker class."""

    def setup_method(self):
        self.test_file = Path("/tmp/test_progress.json")
        self.tracker = ProgressTracker(progress_file=self.test_file)

    def teardown_method(self):
        if self.test_file.exists():
            self.test_file.unlink()

    def test_mark_email_processed(self):
        self.tracker.mark_email_processed("Test Company", "test@example.com")
        assert self.tracker.is_email_processed("Test Company")
        assert self.tracker.get_email("Test Company") == "test@example.com"

    def test_mark_website_processed(self):
        self.tracker.mark_website_processed("Test Company", "https://example.com")
        assert self.tracker.is_website_processed("Test Company")
        assert self.tracker.get_website("Test Company") == "https://example.com"

    def test_mark_phone_processed(self):
        self.tracker.mark_phone_processed("Test Company", "020-123 4567")
        assert self.tracker.is_phone_processed("Test Company")

    def test_reset(self):
        self.tracker.mark_email_processed("Test Company", "test@example.com")
        self.tracker.reset()
        assert not self.tracker.is_email_processed("Test Company")


class TestProbableEmailGenerator:
    """Tests for ProbableEmailGenerator class."""

    def setup_method(self):
        self.generator = ProbableEmailGenerator()

    def test_generate_from_https_url(self):
        result = self.generator.generate("https://www.example.nl")
        assert result == "info@example.nl"

    def test_generate_from_http_url(self):
        result = self.generator.generate("http://test.com/contact")
        assert result == "info@test.com"

    def test_generate_from_www_url(self):
        result = self.generator.generate("www.company.nl")
        assert result == "info@company.nl"

    def test_generate_from_plain_domain(self):
        result = self.generator.generate("mycompany.nl")
        assert result == "info@mycompany.nl"

    def test_generate_with_custom_prefix(self):
        result = self.generator.generate("https://example.nl", prefix="contact")
        assert result == "contact@example.nl"

    def test_generate_empty_input(self):
        result = self.generator.generate("")
        assert result == ""

    def test_generate_not_found(self):
        result = self.generator.generate("Not found")
        assert result == ""

    def test_generate_none_input(self):
        result = self.generator.generate(None)
        assert result == ""

    def test_extract_domain_with_port(self):
        result = self.generator.generate("https://example.nl:8080/page")
        assert result == "info@example.nl"


class TestConfig:
    """Tests for config module."""

    def test_output_filename_format(self):
        filename = config.get_output_filename()
        assert "Companies Enriched.csv" in str(filename)

    def test_bright_data_zones_defined(self):
        assert hasattr(config, 'BRIGHT_DATA_ZONE')
        assert hasattr(config, 'BRIGHT_DATA_SERP_ZONE')
        assert config.BRIGHT_DATA_ZONE == "mcp_unlocker"
        assert config.BRIGHT_DATA_SERP_ZONE == "serp_api2_searchengine"


class TestIntegration:
    """Integration tests (require API keys)."""

    @pytest.mark.skipif(
        not os.getenv("BRIGHT_DATA_API_KEY"),
        reason="BRIGHT_DATA_API_KEY not set"
    )
    def test_serp_api_connection(self):
        """Test that SERP API is accessible."""
        import requests

        api_key = os.getenv("BRIGHT_DATA_API_KEY")
        response = requests.post(
            "https://api.brightdata.com/request",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "zone": "serp_api2_searchengine",
                "url": "https://www.google.com/search?q=test",
                "format": "raw"
            },
            timeout=30
        )
        assert response.status_code == 200
        assert "Google" in response.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
