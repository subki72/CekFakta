"""
GET/POST /api/cron/crawl — Crawler endpoint triggered by Vercel Cron.

Scheduled to run daily at 08:00 WIB (01:00 UTC) via vercel.json.
Protected by CRON_SECRET (Vercel standard) or CRON_SECRET_KEY.

Crawls political articles from Indonesian news portals, analyzes them
via Groq, and saves results to crawled_articles table (FR8, BR11, BR12).
"""

import logging
import os
import secrets

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from api.services.crawler import crawl_and_analyze

logger = logging.getLogger(__name__)
router = APIRouter()


@router.api_route("/crawl", methods=["GET", "POST"])
async def trigger_crawl(
    request: Request,
    portal: str | None = Query(None, description="Optional portal name to crawl (e.g. 'detik.com')"),
    limit: int | None = Query(None, ge=1, le=5, description="Max articles per portal (default 1)"),
):
    """
    Trigger the news crawler.

    Security: Accessible with valid CRON_SECRET or CRON_SECRET_KEY.
    Vercel Cron automatically sends:
      Authorization: Bearer <CRON_SECRET>
    """
    expected_secret = os.getenv("CRON_SECRET") or os.getenv("CRON_SECRET_KEY", "")
    auth_header = request.headers.get("Authorization", "").strip()
    query_key = request.query_params.get("key", "").strip()

    if not expected_secret:
        logger.error("CRON_SECRET is not configured on the server.")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Secret cron belum dikonfigurasi pada server.",
                "code": "CONFIG_ERROR",
            },
        )

    token = ""
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()

    valid_bearer = bool(token and secrets.compare_digest(token, expected_secret))
    valid_query = bool(query_key and secrets.compare_digest(query_key, expected_secret))
    if not (valid_bearer or valid_query):
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "error": "Akses ditolak. Token otorisasi tidak valid.",
                "code": "UNAUTHORIZED",
            },
        )


    try:
        max_articles = limit if limit is not None else 1
        result = await crawl_and_analyze(portal_name=portal, max_articles=max_articles)
        return {
            "success": True,
            "data": result,
            "message": "Crawling selesai.",
        }
    except ValueError as ve:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": str(ve),
                "code": "INVALID_PORTAL",
            },
        )
    except Exception as e:
        logger.exception("Crawling failed: %s", e)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Crawling gagal: {e!s}",
                "code": "CRAWL_ERROR",
            },
        )
