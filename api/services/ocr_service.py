"""
OCR Service — Extract text from screenshots using OCR.space API.

Uses the free OCR.space API (25,000 requests/month free tier).
Handles Indonesian and English text extraction from screenshots
of TikTok, Instagram, X/Twitter, etc.

Why external OCR instead of Tesseract? ADR-002: Vercel serverless has
a 250MB bundle size limit, making local OCR libraries impossible.
"""

import os

import httpx

OCR_API_URL = "https://api.ocr.space/parse/image"


async def extract_text_from_image(image_base64: str) -> str:
    """
    Extract text from a base64-encoded image using OCR.space API.

    Args:
        image_base64: Base64-encoded image string (with or without data URI prefix).

    Returns:
        Extracted text string.

    Raises:
        ValueError: If OCR fails or no text is found (BR2).
    """
    api_key = os.getenv("OCR_SPACE_API_KEY")
    if not api_key:
        raise RuntimeError("OCR_SPACE_API_KEY belum diset di environment variables.")

    # Ensure proper base64 data URI format
    if not image_base64.startswith("data:"):
        image_base64 = f"data:image/png;base64,{image_base64}"

    payload = {
        "apikey": api_key,
        "base64Image": image_base64,
        "language": "eng",  # English alphabet works perfectly for Indonesian text on Engine 2
        "isOverlayRequired": "false",
        "OCREngine": "2",  # Engine 2 is better for screenshots/social media
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(OCR_API_URL, data=payload)
            response.raise_for_status()
    except (httpx.RequestError, httpx.TimeoutException) as e:
        raise ValueError(
            "Gambar tidak dapat diproses. Layanan OCR tidak tersedia saat ini. "
            "Silakan coba lagi nanti atau paste teks secara manual."
        ) from e

    result = response.json()

    # Check for API-level errors
    if result.get("IsErroredOnProcessing", False):
        error_msg = result.get("ErrorMessage", ["Unknown error"])
        raise ValueError(
            f"Gagal memproses gambar (OCR Error): {error_msg}. "
            f"Silakan upload ulang atau paste teks secara manual."
        )

    # Extract parsed text
    parsed_results = result.get("ParsedResults", [])
    if not parsed_results:
        raise ValueError(
            "Gambar tidak dapat diproses. Pastikan gambar berisi teks yang jelas "
            "dan tidak blur. Silakan upload ulang atau paste teks secara manual."
        )

    extracted_text = parsed_results[0].get("ParsedText", "").strip()

    if not extracted_text or len(extracted_text.split()) < 5:
        words = len(extracted_text.split())
        raise ValueError(
            f"Teks yang terdeteksi terlalu pendek ({words} kata). "
            f"Teks yang terbaca: '{extracted_text}'. "
            f"Minimal butuh 5 kata. Silakan paste teks secara manual."
        )

    return extracted_text
