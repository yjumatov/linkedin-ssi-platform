"""Unit tests for the LinkedIn scraper (mocked — no live browser)."""
from __future__ import annotations

import pytest

from app.services.linkedin_scraper import LinkedInSSIScraper, SSIData


class TestSSIDataValidation:
    def test_valid_data(self):
        scraper = LinkedInSSIScraper("user", "pass")
        data = SSIData(
            total_score=72.0,
            professional_brand_score=19.0,
            find_right_people_score=18.0,
            engage_with_insights_score=17.0,
            build_relationships_score=18.0,
        )
        # sum = 72, total = 72 → valid
        assert scraper._is_valid(data) is True

    def test_invalid_total_too_high(self):
        scraper = LinkedInSSIScraper("user", "pass")
        data = SSIData(
            total_score=150.0,
            professional_brand_score=25.0,
            find_right_people_score=25.0,
            engage_with_insights_score=25.0,
            build_relationships_score=25.0,
        )
        assert scraper._is_valid(data) is False

    def test_invalid_component_too_high(self):
        scraper = LinkedInSSIScraper("user", "pass")
        data = SSIData(
            total_score=80.0,
            professional_brand_score=30.0,  # > 25
            find_right_people_score=20.0,
            engage_with_insights_score=15.0,
            build_relationships_score=15.0,
        )
        assert scraper._is_valid(data) is False

    def test_component_sum_mismatch(self):
        scraper = LinkedInSSIScraper("user", "pass")
        data = SSIData(
            total_score=50.0,
            professional_brand_score=24.0,
            find_right_people_score=24.0,
            engage_with_insights_score=24.0,
            build_relationships_score=24.0,
        )
        # sum = 96, total = 50 → invalid
        assert scraper._is_valid(data) is False


class TestLoginPageDetection:
    @pytest.mark.parametrize(
        "url,expected",
        [
            ("https://www.linkedin.com/login", True),
            ("https://www.linkedin.com/uas/login", True),
            ("https://www.linkedin.com/authwall?trk=...", True),
            ("https://www.linkedin.com/sales/ssi", False),
            ("https://www.linkedin.com/feed/", False),
        ],
    )
    def test_detection(self, url: str, expected: bool):
        assert LinkedInSSIScraper._is_login_page(url) == expected


class TestCookieHandling:
    def test_load_missing_cookies_returns_none(self, tmp_path):
        scraper = LinkedInSSIScraper("user@example.com", "pass")
        scraper._cookies_path = tmp_path / "nonexistent.json"
        result = scraper._load_cookies()
        assert result is None

    def test_save_and_load_cookies(self, tmp_path):
        scraper = LinkedInSSIScraper("user@example.com", "pass")
        scraper._cookies_path = tmp_path / "cookies.json"
        import time
        cookies = [
            {"name": "li_at", "value": "token123", "domain": ".linkedin.com", "expires": time.time() + 86400}
        ]
        scraper._save_cookies(cookies)
        loaded = scraper._load_cookies()
        assert loaded is not None
        assert loaded[0]["name"] == "li_at"

    def test_expired_cookies_filtered(self, tmp_path):
        scraper = LinkedInSSIScraper("user@example.com", "pass")
        scraper._cookies_path = tmp_path / "cookies.json"
        import time
        cookies = [
            {"name": "expired", "value": "x", "expires": time.time() - 100},
            {"name": "valid", "value": "y", "expires": time.time() + 86400},
        ]
        scraper._save_cookies(cookies)
        loaded = scraper._load_cookies()
        assert loaded is not None
        assert len(loaded) == 1
        assert loaded[0]["name"] == "valid"
