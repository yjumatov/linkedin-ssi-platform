"""LinkedIn SSI scraper using Playwright with session persistence and retry logic."""
from __future__ import annotations

import asyncio
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeout,
    async_playwright,
)

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SSIData:
    total_score: float
    professional_brand_score: float
    find_right_people_score: float
    engage_with_insights_score: float
    build_relationships_score: float
    industry_avg_score: Optional[float] = None
    network_avg_score: Optional[float] = None
    screenshot_path: Optional[str] = None
    raw_html_path: Optional[str] = None
    scraped_at: datetime = None

    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.now(timezone.utc)


# Multiple selector strategies for resilience against LinkedIn UI changes
_SSI_SELECTORS = {
    "total_score": [
        ".social-selling-index__score",
        "[data-test-id='ssi-score']",
        ".ssi-overall-score",
        ".ssi-index__score-value",
        "text=/Your SSI score is/",
    ],
    "component_container": [
        ".social-selling-index__category",
        ".ssi-category",
        "[data-test-id='ssi-category']",
        ".ssi-component",
    ],
}

_COMPONENT_LABEL_MAP = {
    "establish": "professional_brand",
    "brand": "professional_brand",
    "professional brand": "professional_brand",
    "find": "find_right_people",
    "right people": "find_right_people",
    "engage": "engage_with_insights",
    "insights": "engage_with_insights",
    "build": "build_relationships",
    "relationships": "build_relationships",
}


class LinkedInSSIScraper:
    """Stateful scraper that maintains browser sessions across runs."""

    def __init__(self, username: str, password: str):
        self._username = username
        self._password = password
        self._cookies_path = Path(settings.cookies_dir) / f"{self._safe_username}_cookies.json"
        Path(settings.cookies_dir).mkdir(parents=True, exist_ok=True)
        Path(settings.screenshots_dir).mkdir(parents=True, exist_ok=True)
        Path(settings.html_dir).mkdir(parents=True, exist_ok=True)

    @property
    def _safe_username(self) -> str:
        return re.sub(r"[^a-zA-Z0-9_.-]", "_", self._username)

    # ── Public API ────────────────────────────────────────────────────────────

    async def scrape(self, run_id: str | None = None) -> SSIData:
        """
        Scrape SSI data with automatic re-login and retry.

        Tries up to MAX_RETRY_ATTEMPTS times before raising.
        """
        last_exc: Exception | None = None
        for attempt in range(1, settings.MAX_RETRY_ATTEMPTS + 1):
            try:
                logger.info("scrape_attempt", attempt=attempt, max=settings.MAX_RETRY_ATTEMPTS)
                result = await self._scrape_once(run_id=run_id)
                logger.info(
                    "scrape_success",
                    total_score=result.total_score,
                    attempt=attempt,
                )
                return result
            except Exception as exc:
                last_exc = exc
                logger.warning("scrape_failed", attempt=attempt, error=str(exc))
                if attempt < settings.MAX_RETRY_ATTEMPTS:
                    await asyncio.sleep(settings.RETRY_DELAY_SECONDS * attempt)
        raise RuntimeError(f"Scraping failed after {settings.MAX_RETRY_ATTEMPTS} attempts") from last_exc

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _scrape_once(self, run_id: str | None = None) -> SSIData:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=settings.BROWSER_HEADLESS,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            try:
                context = await self._build_context(browser)
                page = await context.new_page()

                # Stealth: hide navigator.webdriver
                await page.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )

                data = await self._navigate_and_extract(page, run_id=run_id)

                # Persist cookies after successful scrape
                cookies = await context.cookies()
                self._save_cookies(cookies)

                return data
            finally:
                await browser.close()

    async def _build_context(self, browser: Browser) -> BrowserContext:
        """Create browser context, loading stored cookies if available."""
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )

        cookies = self._load_cookies()
        if cookies:
            try:
                await context.add_cookies(cookies)
                logger.debug("cookies_loaded", count=len(cookies))
            except Exception as exc:
                logger.warning("cookies_load_failed", error=str(exc))

        return context

    async def _navigate_and_extract(self, page: Page, run_id: str | None = None) -> SSIData:
        """Navigate to SSI page, logging in if required."""
        await page.goto(settings.LINKEDIN_SSI_URL, wait_until="domcontentloaded", timeout=settings.PAGE_TIMEOUT_MS)

        # Wait a beat for JS redirects
        await page.wait_for_timeout(2000)

        if self._is_login_page(page.url):
            logger.info("session_expired_logging_in")
            await self._login(page)
            await page.goto(settings.LINKEDIN_SSI_URL, wait_until="domcontentloaded", timeout=settings.PAGE_TIMEOUT_MS)
            await page.wait_for_timeout(3000)

        if self._is_login_page(page.url):
            raise RuntimeError("Still on login page after login attempt — check credentials")

        # Wait for SSI content to render
        await self._wait_for_ssi_content(page)

        # Capture raw HTML
        html_path = await self._save_html(page, run_id)

        # Take screenshot
        screenshot_path = await self._take_screenshot(page, run_id)

        # Extract scores
        data = await self._extract_scores(page)
        data.screenshot_path = screenshot_path
        data.raw_html_path = html_path

        return data

    async def _login(self, page: Page) -> None:
        """Perform LinkedIn email/password login."""
        logger.info("performing_login")

        # Navigate to login page if not there already
        if "login" not in page.url and "signin" not in page.url:
            await page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")

        await page.wait_for_selector("#username", timeout=10_000)

        # Fill credentials with human-like delays
        await page.fill("#username", self._username)
        await page.wait_for_timeout(500)
        await page.fill("#password", self._password)
        await page.wait_for_timeout(500)
        await page.click('[type="submit"]')

        # Wait for either dashboard or challenge page
        await page.wait_for_url(
            re.compile(r"linkedin\.com/(feed|checkpoint|sales|home)"),
            timeout=20_000,
        )

        if "checkpoint" in page.url:
            logger.warning("login_checkpoint_detected", url=page.url)
            raise RuntimeError(
                "LinkedIn security checkpoint encountered — manual intervention required"
            )

        logger.info("login_success")

    async def _wait_for_ssi_content(self, page: Page) -> None:
        """Wait for SSI score content to appear on the page."""
        # Try each selector strategy
        for selector in _SSI_SELECTORS["component_container"]:
            try:
                await page.wait_for_selector(selector, timeout=8_000)
                return
            except PlaywrightTimeout:
                continue

        # Fallback: wait for any large number that looks like a score
        try:
            await page.wait_for_function(
                "() => document.body.innerText.match(/\\b(\\d{1,2}|100)\\b/) !== null",
                timeout=10_000,
            )
        except PlaywrightTimeout:
            logger.warning("ssi_content_wait_timeout_proceeding_anyway")

    async def _extract_scores(self, page: Page) -> SSIData:
        """Extract SSI scores from the rendered page."""
        # Try structured JS extraction first
        data = await self._extract_via_js(page)
        if data and self._is_valid(data):
            return data

        # Fallback: regex over full page text
        data = await self._extract_via_text(page)
        if data and self._is_valid(data):
            return data

        raise RuntimeError("Could not extract SSI scores from page — selectors may need updating")

    async def _extract_via_js(self, page: Page) -> Optional[SSIData]:
        """Try to extract scores via evaluated JavaScript."""
        try:
            result = await page.evaluate(
                """() => {
                    const getScore = (selectors) => {
                        for (const sel of selectors) {
                            try {
                                const el = document.querySelector(sel);
                                if (el) {
                                    const txt = el.innerText || el.textContent || '';
                                    const num = parseFloat(txt.match(/[\\d.]+/)?.[0]);
                                    if (!isNaN(num)) return num;
                                }
                            } catch(e) {}
                        }
                        return null;
                    };

                    // Find all score elements containing numbers 0-100
                    const allNumbers = [];
                    document.querySelectorAll('span, div, p, h1, h2, h3, strong').forEach(el => {
                        const txt = (el.innerText || '').trim();
                        const m = txt.match(/^(\\d{1,2}|100)$/);
                        if (m && el.children.length === 0) {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) {
                                allNumbers.push({
                                    value: parseFloat(m[1]),
                                    top: rect.top,
                                    left: rect.left,
                                    size: Math.max(rect.width, rect.height),
                                    text: el.parentElement?.innerText?.substring(0, 100) || ''
                                });
                            }
                        }
                    });

                    return { numbers: allNumbers };
                }"""
            )

            numbers = result.get("numbers", [])
            if not numbers:
                return None

            # Largest number is likely the total score
            numbers.sort(key=lambda x: (-x["size"], x["top"]))

            # Heuristic: total score ≤ 100, component scores ≤ 25
            total_candidates = [n for n in numbers if n["value"] <= 100]
            component_candidates = [n for n in numbers if n["value"] <= 25]

            if not total_candidates:
                return None

            total = total_candidates[0]["value"]

            # Components: sort top-to-bottom, pick 4
            components = sorted(component_candidates[:8], key=lambda x: x["top"])
            if len(components) >= 4:
                return SSIData(
                    total_score=total,
                    professional_brand_score=components[0]["value"],
                    find_right_people_score=components[1]["value"],
                    engage_with_insights_score=components[2]["value"],
                    build_relationships_score=components[3]["value"],
                )

        except Exception as exc:
            logger.debug("js_extraction_failed", error=str(exc))

        return None

    async def _extract_via_text(self, page: Page) -> Optional[SSIData]:
        """Regex-based extraction from full page text as a last resort."""
        try:
            text = await page.inner_text("body")
        except Exception:
            return None

        # Find sequences of numbers that could be scores
        all_nums = [float(m) for m in re.findall(r"\b(\d{1,2}|100)\b", text)]
        if len(all_nums) < 5:
            return None

        # Deduplicate while preserving order
        seen: set[float] = set()
        unique: list[float] = []
        for n in all_nums:
            if n not in seen:
                seen.add(n)
                unique.append(n)

        if len(unique) < 5:
            return None

        # Largest is total, next 4 are components (SSI scores are typically the first large numbers)
        total = max(unique[:10])
        components = [n for n in unique if n != total and n <= 25][:4]
        if len(components) < 4:
            return None

        return SSIData(
            total_score=total,
            professional_brand_score=components[0],
            find_right_people_score=components[1],
            engage_with_insights_score=components[2],
            build_relationships_score=components[3],
        )

    def _is_valid(self, data: SSIData) -> bool:
        component_sum = (
            data.professional_brand_score
            + data.find_right_people_score
            + data.engage_with_insights_score
            + data.build_relationships_score
        )
        return (
            0 <= data.total_score <= 100
            and all(0 <= s <= 25 for s in [
                data.professional_brand_score,
                data.find_right_people_score,
                data.engage_with_insights_score,
                data.build_relationships_score,
            ])
            and abs(component_sum - data.total_score) <= 5  # small tolerance
        )

    @staticmethod
    def _is_login_page(url: str) -> bool:
        return any(kw in url for kw in ("login", "signin", "authwall", "uas/authenticate"))

    async def _take_screenshot(self, page: Page, run_id: str | None) -> Optional[str]:
        try:
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            suffix = f"_{run_id}" if run_id else ""
            filename = f"ssi_{ts}{suffix}.png"
            path = os.path.join(settings.screenshots_dir, filename)
            await page.screenshot(path=path, full_page=True)
            logger.debug("screenshot_saved", path=path)
            return path
        except Exception as exc:
            logger.warning("screenshot_failed", error=str(exc))
            return None

    async def _save_html(self, page: Page, run_id: str | None) -> Optional[str]:
        try:
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            suffix = f"_{run_id}" if run_id else ""
            filename = f"ssi_{ts}{suffix}.html"
            path = os.path.join(settings.html_dir, filename)
            content = await page.content()
            Path(path).write_text(content, encoding="utf-8")
            logger.debug("html_saved", path=path)
            return path
        except Exception as exc:
            logger.warning("html_save_failed", error=str(exc))
            return None

    # ── Cookie persistence ────────────────────────────────────────────────────

    def _load_cookies(self) -> list[dict] | None:
        if not self._cookies_path.exists():
            return None
        try:
            data = json.loads(self._cookies_path.read_text())
            # Filter out clearly expired cookies
            now = time.time()
            valid = [c for c in data if c.get("expires", now + 1) > now]
            return valid or None
        except Exception as exc:
            logger.warning("cookie_load_error", error=str(exc))
            return None

    def _save_cookies(self, cookies: list[dict]) -> None:
        try:
            self._cookies_path.write_text(json.dumps(cookies, indent=2), encoding="utf-8")
            logger.debug("cookies_saved", count=len(cookies))
        except Exception as exc:
            logger.warning("cookie_save_error", error=str(exc))

    def clear_session(self) -> None:
        """Delete stored cookies to force re-login on next run."""
        if self._cookies_path.exists():
            self._cookies_path.unlink()
            logger.info("session_cleared")
