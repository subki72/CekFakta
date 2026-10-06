from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.services.crawler import crawl_and_analyze


@pytest.mark.asyncio
async def test_crawl_and_analyze_invalid_portal():
    with pytest.raises(ValueError, match="tidak ditemukan"):
        await crawl_and_analyze(portal_name="nonexistent-portal.xyz")


@pytest.mark.asyncio
async def test_crawl_and_analyze_portal_filter_and_success():
    index_html = """
    <html>
      <body>
        <article>
          <a href="https://news.detik.com/berita/d-12345/uji-coba-pemilu">Judul Berita 1</a>
        </article>
      </body>
    </html>
    """

    mock_scraped_data = {
        "title": "Judul Berita Detik Politik",
        "text": "Presiden dan pimpinan partai politik mengadakan pertemuan silaturahmi nasional menjelang pemilu.",
    }

    mock_ai_analysis = {
        "score": 85,
        "label": "OBJEKTIF",
        "reasoning": "Berita berimbang.",
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = index_html
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp), \
         patch("api.services.scraper.scrape_url", new_callable=AsyncMock, return_value=mock_scraped_data), \
         patch("api.services.crawler.analyze_text", new_callable=AsyncMock, return_value=mock_ai_analysis), \
         patch("api.services.crawler.get_supabase_client") as mock_supabase:

        # Mock Supabase table calls
        mock_crawled_table = MagicMock()
        # Batch check returns empty list (not yet crawled)
        mock_crawled_table.select.return_value.in_.return_value.execute.return_value = MagicMock(data=[])
        mock_crawled_table.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_crawled_table.insert.return_value.execute.return_value = MagicMock(data=[{"id": "crawled-1"}])

        mock_audit_table = MagicMock()
        mock_audit_table.insert.return_value.execute.return_value = MagicMock(data=[{"id": "audit-1"}])

        def table_router(name):
            if name == "crawled_articles":
                return mock_crawled_table
            if name == "audit_logs":
                return mock_audit_table
            return MagicMock()

        mock_supabase.return_value.table.side_effect = table_router

        result = await crawl_and_analyze(portal_name="detik.com", max_articles=1)
        assert result["total_crawled"] == 1
        assert result["total_analyzed"] == 1
        assert result["portals_attempted"] == 1
        assert len(result["errors"]) == 0


@pytest.mark.asyncio
async def test_crawl_and_analyze_skips_existing_batch():
    index_html = """
    <html>
      <body>
        <article>
          <a href="https://news.detik.com/berita/d-12345/uji-coba-pemilu">Judul Berita 1</a>
        </article>
      </body>
    </html>
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = index_html
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp), \
         patch("api.services.crawler.get_supabase_client") as mock_supabase:

        mock_crawled_table = MagicMock()
        # Batch check returns that URL is already crawled
        mock_crawled_table.select.return_value.in_.return_value.execute.return_value = MagicMock(
            data=[{"url": "https://news.detik.com/berita/d-12345/uji-coba-pemilu"}]
        )

        mock_audit_table = MagicMock()
        mock_audit_table.insert.return_value.execute.return_value = MagicMock(data=[{"id": "audit-1"}])

        def table_router(name):
            if name == "crawled_articles":
                return mock_crawled_table
            if name == "audit_logs":
                return mock_audit_table
            return MagicMock()

        mock_supabase.return_value.table.side_effect = table_router

        result = await crawl_and_analyze(portal_name="detik.com", max_articles=1)
        # Should be skipped without analyzing
        assert result["total_crawled"] == 0
        assert result["total_analyzed"] == 0
