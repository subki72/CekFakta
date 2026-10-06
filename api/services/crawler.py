"""
News Crawler Service — Scrape political articles from Indonesian news portals.

Runs daily at 08:00 WIB (BR11). Only scrapes political category (BR12).
Analyzes each article via Groq and saves to crawled_articles table.

Portal list from Glossary Domain document (02-Glossary-Domain.md).
"""

import logging
import time

import httpx
from bs4 import BeautifulSoup

from api.services import scraper as scraper_service
from api.services.groq_analyzer import analyze_text
from api.services.supabase_client import get_supabase_client
from api.utils.language_detector import detect_language

logger = logging.getLogger(__name__)

# News portal configs — URL to their politics/national section RSS or page
# Each portal has different structure, so we define scraping targets per portal
PORTAL_CONFIGS = [
    {
        "name": "detik.com",
        "politics_url": "https://news.detik.com/berita",
        "article_selector": "article a[href]",
        "base_url": "https://news.detik.com",
    },
    {
        "name": "kompas.com",
        "politics_url": "https://nasional.kompas.com",
        "article_selector": ".articleList a.article__link, .articleItem a, .latestContent a, a.article__link",
        "base_url": "https://nasional.kompas.com",
    },
    {
        "name": "antaranews.com",
        "politics_url": "https://www.antaranews.com/politik",
        "article_selector": ".card__post a, article a[href]",
        "base_url": "https://www.antaranews.com",
    },
    {
        "name": "cnnindonesia.com",
        "politics_url": "https://www.cnnindonesia.com/nasional",
        "article_selector": "article a[href]",
        "base_url": "https://www.cnnindonesia.com",
    },
    {
        "name": "tempo.co",
        "politics_url": "https://www.tempo.co/politik",
        "article_selector": "article a[href], .card-box a",
        "base_url": "https://www.tempo.co",
    },
]

# Default max articles to crawl per portal in serverless environment
DEFAULT_MAX_ARTICLES = 1
# Maximum execution time threshold (seconds) before stopping loop to prevent Vercel timeout
MAX_EXECUTION_SECONDS = 12.0


async def crawl_and_analyze(
    portal_name: str | None = None,
    max_articles: int = DEFAULT_MAX_ARTICLES,
) -> dict:
    """
    Crawl political articles from portals and analyze them.

    Args:
        portal_name: Optional specific portal to scrape (e.g. 'detik.com').
        max_articles: Max articles to scrape per portal.

    Returns:
        Summary dict with counts of articles crawled and analyzed.
    """
    # Filter portals if a specific portal is requested
    portals_to_crawl = PORTAL_CONFIGS
    if portal_name:
        portals_to_crawl = [
            p for p in PORTAL_CONFIGS
            if portal_name.lower() in p["name"].lower()
        ]
        if not portals_to_crawl:
            raise ValueError(f"Portal '{portal_name}' tidak ditemukan dalam daftar konfigurasi.")

    supabase = get_supabase_client()
    total_crawled = 0
    total_analyzed = 0
    errors = []
    start_time = time.time()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    for portal in portals_to_crawl:
        # Check execution time threshold to prevent serverless timeout
        if time.time() - start_time > MAX_EXECUTION_SECONDS:
            logger.warning(
                f"Approaching serverless timeout ({time.time() - start_time:.1f}s). "
                "Halting further portal crawling."
            )
            break

        try:
            # Step 1: Fetch the politics index page
            async with httpx.AsyncClient(
                follow_redirects=True, timeout=8.0
            ) as client:
                response = await client.get(portal["politics_url"], headers=headers)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Step 2: Extract article links
            links = soup.select(portal["article_selector"])
            article_urls = []

            for link in links[:max_articles * 3]:
                href = link.get("href", "")
                if href.startswith("/"):
                    href = portal["base_url"] + href
                if href.startswith("http") and href not in article_urls:
                    article_urls.append(href)

            # Step 3: Check existing URLs in batch (resolves N+1 query pattern)
            target_urls = article_urls[:max_articles]
            existing_urls = set()
            batch_checked = False
            if target_urls:
                try:
                    batch_res = (
                        supabase.table("crawled_articles")
                        .select("url")
                        .in_("url", target_urls)
                        .execute()
                    )
                    if batch_res and isinstance(batch_res.data, list):
                        existing_urls = {
                            item["url"] for item in batch_res.data if isinstance(item, dict) and "url" in item
                        }
                        batch_checked = True
                except Exception as batch_err:
                    logger.debug(f"Batch URL existence check skipped: {batch_err}")

            for url in target_urls:
                if time.time() - start_time > MAX_EXECUTION_SECONDS:
                    break

                if batch_checked:
                    if url in existing_urls:
                        continue  # Skip already crawled articles
                else:
                    # Fallback check for single queries only if batch check was not performed
                    try:
                        existing = (
                            supabase.table("crawled_articles")
                            .select("id")
                            .eq("url", url)
                            .execute()
                        )
                        if existing.data:
                            continue
                    except Exception as e:
                        logger.debug("Check existing article failed: %s", e)

                total_crawled += 1

                try:
                    # Scrape article content
                    article_data = await scraper_service.scrape_url(url)
                    article_text = article_data.get("text", "").strip()

                    # Skip empty or non-article content
                    if len(article_text.split()) < 5:
                        continue

                    # Detect language and analyze
                    lang = detect_language(article_text)
                    analysis = await analyze_text(article_text, lang)

                    # Save to database
                    supabase.table("crawled_articles").insert({
                        "source_portal": portal["name"],
                        "url": url,
                        "title": article_data["title"],
                        "content_text": article_text[:50000],
                        "score": analysis["score"],
                        "label": analysis["label"],
                        "reasoning": analysis["reasoning"],
                    }).execute()

                    total_analyzed += 1

                except Exception as e:
                    err_msg = f"{portal['name']}: {url} — {str(e)[:100]}"
                    logger.warning(err_msg)
                    errors.append(err_msg)

        except Exception as e:
            err_msg = f"{portal['name']}: Failed to fetch index — {str(e)[:100]}"
            logger.warning(err_msg)
            errors.append(err_msg)

    # Log to audit_logs
    try:
        supabase.table("audit_logs").insert({
            "action_type": "CRON_CRAWL_COMPLETED",
            "details": {
                "total_crawled": total_crawled,
                "total_analyzed": total_analyzed,
                "portal_filter": portal_name,
                "elapsed_seconds": round(time.time() - start_time, 2),
            },
        }).execute()
    except Exception as log_err:
        logger.warning(f"Could not write audit log for cron: {log_err}")

    return {
        "total_crawled": total_crawled,
        "total_analyzed": total_analyzed,
        "portals_attempted": len(portals_to_crawl),
        "elapsed_seconds": round(time.time() - start_time, 2),
        "errors": errors[:10],
    }
