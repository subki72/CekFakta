"""
GET /api/analyses/:id — Get detailed analysis result.

Returns the full analysis data including community votes and comments.
Public endpoint — no auth required.
"""

import logging

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from api.services.supabase_client import get_supabase_client
from api.utils.auth import get_current_user_optional

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/analyses/history")
async def get_analysis_history(
    request: Request,
    page: int = Query(1, ge=1, description="Nomor halaman"),
    limit: int = Query(20, ge=1, le=100, description="Jumlah item per halaman"),
):
    """Get history of analyses for the currently authenticated user with pagination."""
    user_id = await get_current_user_optional(request)
    
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "error": "Silakan login terlebih dahulu untuk melihat riwayat.",
                "code": "AUTH_REQUIRED",
            },
        )
        
    try:
        supabase = get_supabase_client()
        start = (page - 1) * limit
        end = start + limit - 1
        result = (
            supabase.table("analyses")
            .select("id, input_type, extracted_text, detected_language, score, label, reasoning, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(start, end)
            .execute()
        )
        
        history = []
        for row in result.data or []:
            history.append({
                "analysis_id": row["id"],
                "id": row["id"],
                "input_type": row["input_type"],
                "extracted_text": row["extracted_text"],
                "detected_language": row["detected_language"],
                "score": row["score"],
                "label": row["label"],
                "reasoning": row["reasoning"],
                "timestamp": row["created_at"]
            })
            
        return {
            "success": True,
            "data": history
        }
    except Exception as e:
        logger.exception("Error fetching history: %s", e)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Gagal mengambil riwayat analisis.",
                "code": "FETCH_ERROR",
            },
        )


def get_vote_counts(supabase, analysis_id: str) -> tuple[int, int]:
    """
    Fetch agree and disagree vote counts efficiently.
    Uses PostgREST exact count with head=True (0 rows transferred).
    Falls back gracefully to row counting if exact count is unavailable (e.g. unit test mocks).
    """
    try:
        agree_res = (
            supabase.table("votes")
            .select("id", count="exact", head=True)
            .eq("analysis_id", analysis_id)
            .eq("is_agree", True)
            .execute()
        )
        disagree_res = (
            supabase.table("votes")
            .select("id", count="exact", head=True)
            .eq("analysis_id", analysis_id)
            .eq("is_agree", False)
            .execute()
        )
        if agree_res.count is not None and disagree_res.count is not None:
            return agree_res.count, disagree_res.count
    except Exception as count_err:
        logger.debug("PostgREST count aggregation fallback: %s", count_err)

    # Fallback to row counting for mocked tests or legacy providers
    try:
        votes_result = (
            supabase.table("votes")
            .select("is_agree")
            .eq("analysis_id", analysis_id)
            .execute()
        )
        votes = votes_result.data or []
        vote_agree = sum(1 for v in votes if v.get("is_agree"))
        vote_disagree = sum(1 for v in votes if not v.get("is_agree"))
        return vote_agree, vote_disagree
    except Exception:
        return 0, 0


@router.get("/analyses/{analysis_id}")
async def get_analysis(
    analysis_id: str,
    request: Request,
    comments_limit: int = Query(50, ge=1, le=100, description="Jumlah maksimal komentar"),
):
    """Get detailed analysis result by ID, including community data and user's vote state."""
    try:
        supabase = get_supabase_client()

        # Explicit projection excluding ip_hash to prevent sensitive data leakage
        result = (
            supabase.table("analyses")
            .select(
                "id, user_id, input_type, raw_input, extracted_text, "
                "detected_language, score, label, reasoning, highlighted_issues, buzzer_indicators, created_at"
            )
            .eq("id", analysis_id)
            .execute()
        )

        if not result.data:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": "Analisis tidak ditemukan.",
                    "code": "NOT_FOUND",
                },
            )

        analysis = result.data[0]

        # Fetch vote counts via efficient O(1) aggregation
        vote_agree, vote_disagree = get_vote_counts(supabase, analysis_id)

        # Check if requesting user has already voted
        user_vote = None
        user_id = await get_current_user_optional(request)
        if user_id:
            try:
                user_vote_res = (
                    supabase.table("votes")
                    .select("is_agree")
                    .eq("analysis_id", analysis_id)
                    .eq("user_id", user_id)
                    .execute()
                )
                if user_vote_res.data:
                    user_vote = user_vote_res.data[0]["is_agree"]
            except Exception as uv_err:
                logger.warning(f"Failed to check user vote: {uv_err}")

        # Fetch comments and author names in a single query or batch (resolves N+1)
        comments = []
        try:
            # Attempt PostgREST relationship join
            comments_result = (
                supabase.table("comments")
                .select("id, content, created_at, user_id, users(name)")
                .eq("analysis_id", analysis_id)
                .order("created_at", desc=False)
                .limit(comments_limit)
                .execute()
            )
            raw_comments = comments_result.data or []
            if raw_comments and "users" in raw_comments[0]:
                for c in raw_comments:
                    user_obj = c.get("users")
                    if isinstance(user_obj, dict):
                        user_name = user_obj.get("name") or "Anonim"
                    elif isinstance(user_obj, list) and user_obj:
                        user_name = user_obj[0].get("name") or "Anonim"
                    else:
                        user_name = "Anonim"
                    comments.append({
                        "id": c["id"],
                        "user_name": user_name,
                        "content": c["content"],
                        "created_at": c["created_at"],
                    })
            else:
                raise ValueError("users relationship not embedded")
        except Exception:
            # Fallback to single batch query for user IDs (O(1) database queries)
            comments_result = (
                supabase.table("comments")
                .select("id, content, created_at, user_id")
                .eq("analysis_id", analysis_id)
                .order("created_at", desc=False)
                .limit(comments_limit)
                .execute()
            )
            raw_comments = comments_result.data or []
            user_ids = list({c["user_id"] for c in raw_comments if c.get("user_id")})
            user_map = {}
            if user_ids:
                try:
                    users_result = (
                        supabase.table("users")
                        .select("id, name")
                        .in_("id", user_ids)
                        .execute()
                    )
                    user_map = {u["id"]: u["name"] for u in users_result.data or []}
                except Exception as user_fetch_err:
                    logger.warning(f"Failed to batch fetch comment authors: {user_fetch_err}")

            for c in raw_comments:
                comments.append({
                    "id": c["id"],
                    "user_name": user_map.get(c["user_id"]) or "Anonim",
                    "content": c["content"],
                    "created_at": c["created_at"],
                })

        return {
            "success": True,
            "data": {
                "id": analysis["id"],
                "analysis_id": analysis["id"],
                "user_id": analysis.get("user_id"),
                "input_type": analysis.get("input_type"),
                "raw_input": analysis.get("raw_input"),
                "extracted_text": analysis.get("extracted_text"),
                "detected_language": analysis.get("detected_language"),
                "score": analysis.get("score"),
                "label": analysis.get("label"),
                "reasoning": analysis.get("reasoning"),
                "highlighted_issues": analysis.get("highlighted_issues") or [],
                "buzzer_indicators": analysis.get("buzzer_indicators") or [],
                "created_at": analysis.get("created_at"),
                "vote_agree": vote_agree,
                "vote_disagree": vote_disagree,
                "user_vote": user_vote,
                "comments": comments,
            },
        }

    except Exception as e:
        logger.exception("Failed to get analysis %s: %s", analysis_id, e)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Gagal mengambil data analisis.",
                "code": "FETCH_ERROR",
            },
        )


@router.delete("/analyses/{analysis_id}")
async def delete_analysis(analysis_id: str, request: Request):
    """SR3.1: Delete an analysis and log the action."""
    user_id = await get_current_user_optional(request)
    
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "error": "Silakan login terlebih dahulu untuk menghapus analisis.",
                "code": "AUTH_REQUIRED",
            },
        )
        
    try:
        supabase = get_supabase_client()
        
        # Verify ownership
        result = supabase.table("analyses").select("user_id").eq("id", analysis_id).execute()
        
        if not result.data:
            return JSONResponse(status_code=404, content={"success": False, "error": "Analisis tidak ditemukan."})
            
        if result.data[0]["user_id"] != user_id:
            return JSONResponse(status_code=403, content={"success": False, "error": "Akses ditolak."})
            
        # Delete analysis
        supabase.table("analyses").delete().eq("id", analysis_id).execute()
        
        # Log to audit_logs
        try:
            from api.utils.rate_limiter import get_client_ip_hash
            ip_hash = get_client_ip_hash(request)
            supabase.table("audit_logs").insert({
                "user_id": user_id,
                "ip_hash": ip_hash,
                "action_type": "ANALYSIS_DELETED",
                "details": {"analysis_id": analysis_id}
            }).execute()
        except Exception as log_err:
            logger.warning(f"Failed to record audit log for deleted analysis: {log_err}")
            
        return {"success": True, "message": "Analisis berhasil dihapus."}
        
    except Exception as e:
        logger.exception("Failed to delete analysis %s: %s", analysis_id, e)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Gagal menghapus analisis.",
                "code": "DELETE_ERROR",
            },
        )
