"""
URL Scraper — Extract text content from news article URLs.

Uses httpx (async) + BeautifulSoup to fetch and parse HTML content.
Handles common news portal structures and gracefully fails for
paywalled or blocked content (BR3).
"""

import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup


def is_safe_url(url: str) -> bool:
    """
    Validate that the given URL does not resolve to private, local, link-local,
    carrier-grade NAT, or internal cloud metadata IP ranges, and only uses standard
    web ports (anti-SSRF protection).
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        
        hostname = parsed.hostname
        if not hostname:
            return False

        # Restrict to standard web ports to prevent SSRF port scanning
        if parsed.port and parsed.port not in (80, 443, 8080, 8443):
            return False

        # Block literal localhost names
        if hostname.lower() in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
            return False

        # Resolve all addresses (handles IPv4, IPv6, and dual-stack)
        addr_info = socket.getaddrinfo(hostname, None)
        if not addr_info:
            return False

        # Extra restricted networks (RFC 6598 CGNAT, RFC 2544 Benchmarking)
        cgnat_net = ipaddress.ip_network("100.64.0.0/10")
        bench_net = ipaddress.ip_network("198.18.0.0/15")

        for family, socktype, proto, canonname, sockaddr in addr_info:
            ip_str = sockaddr[0]
            ip_obj = ipaddress.ip_address(ip_str)

            # If IPv4-mapped IPv6 (e.g. ::ffff:127.0.0.1), unwrap to IPv4
            if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped:
                ip_obj = ip_obj.ipv4_mapped

            # Block private, loopback, multicast, link-local (e.g. 169.254.169.254), reserved
            if (
                ip_obj.is_private
                or ip_obj.is_loopback
                or ip_obj.is_multicast
                or ip_obj.is_reserved
                or ip_obj.is_link_local
                or ip_obj.is_unspecified
                or ip_obj in cgnat_net
                or ip_obj in bench_net
            ):
                return False

        return True
    except Exception:
        return False


class SSRFSafeTransport(httpx.AsyncHTTPTransport):
    """
    Custom AsyncHTTPTransport that validates the destination host/IP right before
    sending the request, mitigating Time-of-Check to Time-of-Use (TOCTOU) DNS rebinding attacks.
    """

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        if not is_safe_url(url_str):
            raise ValueError(
                "URL ditolak. Terdeteksi resolusi IP internal atau tidak aman (potensi DNS rebinding SSRF)."
            )
        return await super().handle_async_request(request)



# Common HTML tags that typically contain article body text
ARTICLE_SELECTORS = [
    "article",
    '[class*="article-body"]',
    '[class*="content-body"]',
    '[class*="detail-content"]',
    '[class*="read__content"]',
    '[class*="post-content"]',
    '[itemprop="articleBody"]',
    ".detail__body-text",
    ".content__body",
]

# Tags to remove (noise)
NOISE_TAGS = ["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]


async def scrape_url(url: str) -> dict:
    """
    Scrape text content from a news article URL.

    Args:
        url: The URL of the news article.

    Returns:
        Dict with 'title' and 'text' keys.

    Raises:
        ValueError: If the URL cannot be scraped or no text is found.
    """
    if not is_safe_url(url):
        raise ValueError("URL ditolak. URL tidak valid atau merujuk pada IP internal (potensi SSRF).")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    try:
        # Prevent redirect-based SSRF by manually validating each redirect hop
        # and using SSRFSafeTransport to prevent DNS rebinding
        async with httpx.AsyncClient(
            transport=SSRFSafeTransport(),
            follow_redirects=False,
            timeout=10.0,
        ) as client:
            current_url = url
            response = None
            max_redirects = 5

            for _ in range(max_redirects + 1):
                if not is_safe_url(current_url):
                    raise ValueError(
                        "URL ditolak. Tujuan redirect merujuk pada IP internal/tidak aman (potensi SSRF)."
                    )
                response = await client.get(current_url, headers=headers)
                if response.is_redirect:
                    location = response.headers.get("Location")
                    if not location:
                        break
                    current_url = urljoin(current_url, location)
                else:
                    break

            if response is None:
                raise ValueError("Tidak dapat mengambil konten dari URL.")

            if response.is_redirect:
                raise ValueError("Terlalu banyak pengalihan (redirect loop).")

            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise ValueError(
            f"Konten dari URL ini tidak dapat diakses (HTTP {e.response.status_code}). "
            "Silakan copy-paste teks artikelnya secara manual."
        ) from e
    except (httpx.RequestError, httpx.TimeoutException) as e:
        raise ValueError(
            "Konten dari URL ini tidak dapat diakses "
            "(kemungkinan dilindungi paywall atau anti-bot). "
            "Silakan copy-paste teks artikelnya secara manual."
        ) from e

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove noise elements
    for tag in NOISE_TAGS:
        for element in soup.find_all(tag):
            element.decompose()

    # Extract title
    title = ""
    title_tag = soup.find("h1")
    if title_tag:
        title = title_tag.get_text(strip=True)
    elif soup.title:
        title = soup.title.get_text(strip=True)

    # Try to find article body using common selectors
    article_text = ""
    for selector in ARTICLE_SELECTORS:
        element = soup.select_one(selector)
        if element:
            # Get all paragraph text within the article body
            paragraphs = element.find_all("p")
            if paragraphs:
                article_text = "\n\n".join(
                    p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)
                )
                break

    # Fallback: get all paragraphs from body
    if not article_text:
        body = soup.find("body")
        if body:
            paragraphs = body.find_all("p")
            article_text = "\n\n".join(
                p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)
            )

    if not article_text or len(article_text.split()) < 10:
        raise ValueError(
            "Konten dari URL ini tidak dapat diakses "
            "(kemungkinan dilindungi paywall atau anti-bot). "
            "Silakan copy-paste teks artikelnya secara manual."
        )

    # Combine title + body for analysis
    full_text = f"{title}\n\n{article_text}" if title else article_text

    return {"title": title, "text": full_text}
