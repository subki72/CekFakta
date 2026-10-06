from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.services.scraper import is_safe_url, scrape_url


def test_is_safe_url_valid_domains():
    assert is_safe_url("https://www.kompas.com/nasional") is True
    assert is_safe_url("https://news.detik.com/berita") is True
    assert is_safe_url("https://tirto.id/politik") is True
    assert is_safe_url("https://google.com") is True


def test_is_safe_url_blocks_internal_and_ssrf():
    assert is_safe_url("http://localhost:8000") is False
    assert is_safe_url("http://127.0.0.1:8000") is False
    assert is_safe_url("http://0.0.0.0") is False
    assert is_safe_url("http://169.254.169.254/latest/meta-data") is False
    assert is_safe_url("http://10.0.0.1") is False
    assert is_safe_url("http://192.168.1.1") is False
    assert is_safe_url("http://172.16.0.1") is False
    assert is_safe_url("http://[::1]") is False


def test_is_safe_url_invalid_schemes():
    assert is_safe_url("ftp://example.com/file.txt") is False
    assert is_safe_url("file:///etc/passwd") is False
    assert is_safe_url("javascript:alert(1)") is False
    assert is_safe_url("not-a-url") is False
    assert is_safe_url("") is False


@pytest.mark.asyncio
async def test_scrape_url_blocks_unsafe_target():
    with pytest.raises(ValueError, match="potensi SSRF"):
        await scrape_url("http://127.0.0.1:8080/admin")


@pytest.mark.asyncio
async def test_scrape_url_parses_content():
    html_content = """
    <html>
      <head><title>Judul Berita Politik</title></head>
      <body>
        <article>
          <h1>Judul Berita Politik Terkini</h1>
          <p>Ini adalah paragraf pertama tentang kebijakan politik pemerintah dan anggota DPR yang sedang dibahas secara intensif.</p>
          <p>Paragraf kedua menjelaskan dampak rancangan undang-undang terhadap masyarakat luas di berbagai daerah pemilihan.</p>
        </article>
      </body>
    </html>
    """
    mock_resp = MagicMock()
    mock_resp.is_redirect = False
    mock_resp.status_code = 200
    mock_resp.text = html_content
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await scrape_url("https://nasional.kompas.com/read/2026/berita-politik")
        assert "Judul Berita Politik" in result["title"]
        assert "kebijakan politik pemerintah" in result["text"]


def test_is_safe_url_blocks_non_standard_ports():
    assert is_safe_url("http://example.com:22") is False
    assert is_safe_url("http://example.com:6379") is False
    assert is_safe_url("http://example.com:5432") is False
    assert is_safe_url("https://example.com:443") is True
    assert is_safe_url("http://example.com:80") is True


def test_is_safe_url_blocks_cgnat_and_benchmark():
    assert is_safe_url("http://100.64.0.1") is False
    assert is_safe_url("http://198.18.0.1") is False


@pytest.mark.asyncio
async def test_scrape_url_blocks_redirect_ssrf():
    # Initial request to safe public domain redirects to internal cloud metadata
    redirect_resp = MagicMock()
    redirect_resp.is_redirect = True
    redirect_resp.status_code = 302
    redirect_resp.headers = {"Location": "http://169.254.169.254/latest/meta-data"}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = redirect_resp
        with pytest.raises(ValueError, match="potensi SSRF"):
            await scrape_url("https://safe-domain.com/news-article")

