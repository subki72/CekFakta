from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "ok"


def test_analyze_empty_text():
    response = client.post("/api/analyze", data={"input_type": "TEXT", "raw_input": ""})
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_analyze_too_short():
    response = client.post("/api/analyze", data={"input_type": "TEXT", "raw_input": "Presiden pemilu"})
    assert response.status_code == 400
    assert response.json()["code"] == "TEXT_TOO_SHORT"


def test_analyze_not_political():
    non_political = "Resep membuat bolu kukus pandan yang lembut dan mengembang sempurna dengan santan segar dan tepung terigu pilihan."
    response = client.post("/api/analyze", data={"input_type": "TEXT", "raw_input": non_political})
    assert response.status_code == 400
    assert response.json()["code"] == "NOT_POLITICAL"


def test_analyze_db_failure_returns_500():
    valid_political_text = (
        "Presiden dan kabinet menteri mengadakan rapat paripurna bersama para ketua partai politik "
        "membahas undang-undang pemilihan umum serentak yang akan disahkan parlemen."
    )
    mock_analysis = {
        "score": 85,
        "label": "OBJEKTIF",
        "reasoning": "Berita objektif.",
        "buzzer_indicators": [],
        "highlighted_issues": [],
    }

    # Mock groq analyze_text to succeed, but supabase insert to fail
    with patch("api.routes.analyze.analyze_text", new_callable=AsyncMock, return_value=mock_analysis), \
         patch("api.routes.analyze.get_supabase_client") as mock_supabase:
        
        mock_table = MagicMock()
        mock_table.insert.return_value.execute.side_effect = Exception("Supabase connection timeout")
        mock_supabase.return_value.table.return_value = mock_table

        response = client.post("/api/analyze", data={"input_type": "TEXT", "raw_input": valid_political_text})
        assert response.status_code == 500
        json_data = response.json()
        assert json_data["success"] is False
        assert json_data["code"] == "DATABASE_ERROR"


def test_cron_crawl_auth_rejection(monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "super-secret-cron-key")
    # Request without header
    response = client.get("/api/cron/crawl")
    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"

    # Request with wrong bearer token
    response = client.get("/api/cron/crawl", headers={"Authorization": "Bearer wrong-key"})
    assert response.status_code == 401


def test_cron_crawl_success_both_methods(monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "valid-secret")
    mock_crawl_result = {
        "total_crawled": 2,
        "total_analyzed": 2,
        "portals_attempted": 2,
        "elapsed_seconds": 1.5,
        "errors": [],
    }

    with patch("api.routes.cron.crawl_and_analyze", new_callable=AsyncMock, return_value=mock_crawl_result):
        # 1. Test GET (Vercel cron method)
        get_res = client.get(
            "/api/cron/crawl",
            headers={"Authorization": "Bearer valid-secret"}
        )
        assert get_res.status_code == 200
        assert get_res.json()["success"] is True
        assert get_res.json()["data"]["total_analyzed"] == 2

        # 2. Test POST
        post_res = client.post(
            "/api/cron/crawl",
            headers={"Authorization": "Bearer valid-secret"}
        )
        assert post_res.status_code == 200
        assert post_res.json()["success"] is True


def test_get_analysis_sanitizes_ip_hash():
    sample_analysis_id = "11111111-2222-3333-4444-555555555555"
    mock_db_row = {
        "id": sample_analysis_id,
        "user_id": None,
        "input_type": "TEXT",
        "raw_input": "Presiden bertemu DPR.",
        "extracted_text": "Presiden bertemu DPR membahas RUU.",
        "detected_language": "id",
        "score": 75,
        "label": "OBJEKTIF",
        "reasoning": "Cukup objektif.",
        "buzzer_indicators": [],
        "created_at": "2026-10-05T12:00:00Z",
        "ip_hash": "sensitive_leaked_hash_12345",  # DB might hold this internally
    }

    with patch("api.routes.analyses.get_supabase_client") as mock_supabase:
        mock_analyses_table = MagicMock()
        # Mock analyses select
        mock_analyses_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[mock_db_row]
        )

        # Mock votes select
        mock_votes_table = MagicMock()
        mock_votes_table.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

        # Mock comments select
        mock_comments_table = MagicMock()
        mock_comments_table.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(data=[])

        def table_router(name):
            if name == "analyses":
                return mock_analyses_table
            if name == "votes":
                return mock_votes_table
            if name == "comments":
                return mock_comments_table
            return MagicMock()

        mock_supabase.return_value.table.side_effect = table_router

        response = client.get(f"/api/analyses/{sample_analysis_id}")
        assert response.status_code == 200
        res_data = response.json()["data"]

        # MUST NOT leak ip_hash
        assert "ip_hash" not in res_data

        # MUST contain both id and analysis_id
        assert res_data["id"] == sample_analysis_id
        assert res_data["analysis_id"] == sample_analysis_id
        assert res_data["score"] == 75


def test_vote_requires_authentication():
    response = client.post(
        "/api/analyses/sample-id/vote",
        json={"is_agree": True}
    )
    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_REQUIRED"


def test_comment_requires_authentication():
    response = client.post(
        "/api/analyses/sample-id/comment",
        json={"content": "Pendapat saya sangat berbeda dengan analisis ini."}
    )
    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_REQUIRED"


def test_feedback_requires_authentication():
    response = client.post(
        "/api/feedback/submit",
        json={"subject": "Saran UI", "message": "Tambahkan grafik perbandingan narasi."}
    )
    assert response.status_code == 401


def test_analyze_text_success_returns_id_and_analysis_id():
    valid_political_text = (
        "Presiden Republik Indonesia melantik menteri koordinator politik dan keamanan "
        "dalam sidang kabinet paripurna perdana di istana negara hari ini."
    )
    mock_analysis = {
        "score": 90,
        "label": "OBJEKTIF",
        "reasoning": "Pemberitaan faktual dan terverifikasi.",
        "buzzer_indicators": [],
        "highlighted_issues": [],
    }

    with patch("api.routes.analyze.analyze_text", new_callable=AsyncMock, return_value=mock_analysis), \
         patch("api.routes.analyze.get_supabase_client") as mock_supabase:

        mock_table = MagicMock()
        mock_table.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "test-uuid-9999"}]
        )
        mock_supabase.return_value.table.return_value = mock_table

        response = client.post("/api/analyze", data={"input_type": "TEXT", "raw_input": valid_political_text})
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == "test-uuid-9999"
        assert data["analysis_id"] == "test-uuid-9999"
        assert data["score"] == 90


def test_get_analysis_authenticated_returns_user_vote():
    sample_analysis_id = "test-uuid-1111"
    mock_db_row = {
        "id": sample_analysis_id,
        "user_id": None,
        "input_type": "TEXT",
        "raw_input": "Presiden bertemu menteri.",
        "extracted_text": "Presiden bertemu menteri membahas RUU.",
        "detected_language": "id",
        "score": 80,
        "label": "OBJEKTIF",
        "reasoning": "Objektif.",
        "buzzer_indicators": [],
        "created_at": "2026-10-05T12:00:00Z",
    }

    with patch("api.routes.analyses.get_supabase_client") as mock_supabase, \
         patch("api.routes.analyses.get_current_user_optional", new_callable=AsyncMock, return_value="user-uuid-123"):

        mock_analyses = MagicMock()
        mock_analyses.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[mock_db_row])

        mock_votes = MagicMock()
        # all votes count
        mock_votes.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"is_agree": True}, {"is_agree": False}]
        )
        # user vote specific query
        mock_votes.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"is_agree": True}]
        )

        mock_comments = MagicMock()
        mock_comments.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(data=[])

        def table_router(name):
            if name == "analyses":
                return mock_analyses
            if name == "votes":
                return mock_votes
            if name == "comments":
                return mock_comments
            return MagicMock()

        mock_supabase.return_value.table.side_effect = table_router

        response = client.get(
            f"/api/analyses/{sample_analysis_id}",
            headers={"Authorization": "Bearer fake-token"}
        )
        assert response.status_code == 200
        res_data = response.json()["data"]
        assert res_data["user_vote"] is True


def test_cron_lowercase_bearer_and_query_key(monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "super-secret-123")
    mock_crawl_result = {
        "total_crawled": 1,
        "total_analyzed": 1,
        "portals_attempted": 1,
        "elapsed_seconds": 0.5,
        "errors": [],
    }

    with patch("api.routes.cron.crawl_and_analyze", new_callable=AsyncMock, return_value=mock_crawl_result):
        # 1. Lowercase "bearer <token>"
        res1 = client.get(
            "/api/cron/crawl",
            headers={"Authorization": "bearer super-secret-123"}
        )
        assert res1.status_code == 200
        assert res1.json()["success"] is True

        # 2. Query param key
        res2 = client.get("/api/cron/crawl?key=super-secret-123")
        assert res2.status_code == 200
        assert res2.json()["success"] is True


def test_analyze_rejects_over_100k_characters():
    huge_text = "presiden " * 12000  # > 100,000 characters
    response = client.post("/api/analyze", data={"input_type": "TEXT", "raw_input": huge_text})
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_require_auth_guard_raises_401():
    from fastapi import HTTPException

    from api.utils.auth import require_auth
    req = MagicMock()
    req.headers = {}
    with pytest.raises(HTTPException) as exc_info:
        await require_auth(req)
    assert exc_info.value.status_code == 401


def test_get_vote_counts_exact_and_fallback():
    from api.routes.analyses import get_vote_counts

    mock_supabase = MagicMock()
    # 1. Test exact count path
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = [
        MagicMock(count=15),
        MagicMock(count=3),
    ]
    agree, disagree = get_vote_counts(mock_supabase, "test-id")
    assert agree == 15
    assert disagree == 3

    # 2. Test fallback path (count is None)
    mock_supabase_fallback = MagicMock()
    mock_supabase_fallback.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = [
        MagicMock(count=None),
        MagicMock(count=None),
    ]
    mock_supabase_fallback.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"is_agree": True}, {"is_agree": True}, {"is_agree": False}]
    )
    agree_fb, disagree_fb = get_vote_counts(mock_supabase_fallback, "test-id")
    assert agree_fb == 2
    assert disagree_fb == 1


