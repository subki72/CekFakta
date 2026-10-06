"""
GET /api/trending — Dashboard trending topics.

Aggregates analysis data to show trending political topics,
average objectivity scores, and label distributions (FR7).
"""

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api.services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/trending")
async def get_trending():
    """
    Get trending topics from recent analyses and crawled articles.

    Returns aggregated data for the dashboard: topics with average scores,
    total analyses, and label distributions.
    """
    try:
        supabase = get_supabase_client()

        # Fetch recent analyses (last 7 days) ONLY from authenticated users (SR1.2)
        recent_analyses = (
            supabase.table("analyses")
            .select("score, label, created_at")
            .not_.is_("user_id", "null")
            .order("created_at", desc=True)
            .limit(100)
            .execute()
        )

        # Fetch recent crawled articles (last 7 days)
        recent_crawled = (
            supabase.table("crawled_articles")
            .select("score, label, title, source_portal, created_at")
            .order("created_at", desc=True)
            .limit(100)
            .execute()
        )

        # Calculate aggregate statistics
        all_items = (recent_analyses.data or []) + (recent_crawled.data or [])

        if not all_items:
            return {
                "success": True,
                "data": {
                    "total_analyses": 0,
                    "average_score": 0,
                    "label_distribution": {
                        "OBJEKTIF": 0,
                        "CENDERUNG_BIAS": 0,
                        "SANGAT_MANIPULATIF": 0,
                    },
                    "recent_articles": [],
                },
            }

        total = len(all_items)
        avg_score = sum(item["score"] for item in all_items) / total

        label_dist = {"OBJEKTIF": 0, "CENDERUNG_BIAS": 0, "SANGAT_MANIPULATIF": 0}
        for item in all_items:
            label = item.get("label", "")
            if label in label_dist:
                label_dist[label] += 1

        # Recent crawled articles for display
        recent_articles = [
            {
                "title": article.get("title", ""),
                "source": article.get("source_portal", ""),
                "score": article.get("score", 0),
                "label": article.get("label", ""),
                "created_at": article.get("created_at", ""),
            }
            for article in (recent_crawled.data or [])[:20]
        ]

        return {
            "success": True,
            "data": {
                "total_analyses": total,
                "average_score": round(avg_score, 1),
                "label_distribution": label_dist,
                "recent_articles": recent_articles,
            },
        }

    except Exception as e:
        logger.exception("Failed to get trending data: %s", e)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Gagal mengambil data trending.",
                "code": "TRENDING_ERROR",
            },
        )
