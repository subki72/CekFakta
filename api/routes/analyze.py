"""
POST /api/analyze — Main analysis endpoint.

Accepts TEXT, URL, or IMAGE input, processes it through the pipeline:
1. Rate limit check (BR13)
2. Input extraction (scrape URL / OCR image / use raw text)
3. Text length validation (BR1: 30-5000 words)
4. Political content check (BR4)
5. Language detection (FR3.3)
6. Groq AI analysis (FR2)
7. Save to database
8. Return result
"""

import base64
import logging
import re

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse

from api.models.schemas import InputType
from api.services.groq_analyzer import analyze_text
from api.services.ocr_service import extract_text_from_image
from api.services.scraper import scrape_url
from api.services.supabase_client import get_supabase_client
from api.utils.auth import get_current_user_optional
from api.utils.content_classifier import is_political_content
from api.utils.language_detector import detect_language
from api.utils.rate_limiter import check_rate_limit, get_client_ip_hash

logger = logging.getLogger(__name__)
router = APIRouter()

def sterilize_input(text: str) -> str:
    """SR2.1: Sterilize input by removing control characters that might confuse LLM."""
    if not text:
        return ""
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)

@router.post("/analyze")
async def analyze(
    request: Request,
    input_type: str = Form("TEXT"),
    raw_input: str = Form(None),
    image: UploadFile = File(None),
):
    """
    Analyze text, URL, or image for political objectivity.

    Supports both JSON body (for TEXT/URL) and multipart form (for IMAGE upload).
    """
    # Step 1: Rate limit check
    check_rate_limit(request)

    # Step 2: Extract text based on input type
    extracted_text = ""
    raw_input_stored = sterilize_input(raw_input)

    if raw_input_stored and len(raw_input_stored) > 100000:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": "Panjang input teks melebihi batas maksimum 100.000 karakter.",
                "code": "VALIDATION_ERROR",
            },
        )

    try:
        if input_type == InputType.URL:
            if not raw_input_stored:
                return JSONResponse(
                    status_code=422,
                    content={
                        "success": False,
                        "error": "URL tidak boleh kosong.",
                        "code": "VALIDATION_ERROR",
                    },
                )
            result = await scrape_url(raw_input_stored)
            extracted_text = result["text"]

        elif input_type == InputType.IMAGE:
            if image is None and not raw_input_stored:
                return JSONResponse(
                    status_code=422,
                    content={
                        "success": False,
                        "error": "Gambar tidak boleh kosong.",
                        "code": "VALIDATION_ERROR",
                    },
                )

            if image:
                # SR2.2: Basic file size check (~5MB limit)
                # Note: FastAPI UploadFile buffers into memory/disk. We read the content length.
                image_bytes = await image.read()
                if len(image_bytes) > 5 * 1024 * 1024:
                    raise ValueError("Ukuran gambar melebihi batas 5MB.")
                
                image_b64 = base64.b64encode(image_bytes).decode("utf-8")
                content_type = image.content_type or "image/png"
                image_data = f"data:{content_type};base64,{image_b64}"
                raw_input_stored = f"[IMAGE:{image.filename}]"
            else:
                # Handle base64 string from form
                if raw_input_stored and len(raw_input_stored) > 7 * 1024 * 1024:
                    raise ValueError("Ukuran data gambar base64 melebihi batas 5MB.")
                image_data = raw_input_stored
                raw_input_stored = "[IMAGE:base64]"

            extracted_text = await extract_text_from_image(image_data)

        else:  # TEXT
            if not raw_input_stored:
                return JSONResponse(
                    status_code=422,
                    content={
                        "success": False,
                        "error": "Teks tidak boleh kosong.",
                        "code": "VALIDATION_ERROR",
                    },
                )
            extracted_text = raw_input_stored

    except ValueError as e:
        # SR3.2: Log failed OCR attempts
        try:
            supabase = get_supabase_client()
            user_id = await get_current_user_optional(request)
            ip_hash = get_client_ip_hash(request)
            supabase.table("audit_logs").insert({
                "user_id": user_id,
                "ip_hash": ip_hash,
                "action_type": "ANALYSIS_FAILED",
                "details": {"error": str(e), "input_type": input_type}
            }).execute()
        except Exception as log_err:
            logger.warning(f"Failed to record audit log for failed analysis: {log_err}")

        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": str(e),
                "code": "EXTRACTION_ERROR",
            },
        )

    # Step 3: Validate text length (BR1 updated: 5-5000 words to allow thumbnails/memes)
    word_count = len(extracted_text.split())
    if word_count < 5:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": "Teks terlalu pendek untuk dianalisis. Masukkan narasi minimal 5 kata.",
                "code": "TEXT_TOO_SHORT",
            },
        )
    if word_count > 5000:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": "Teks terlalu panjang untuk dianalisis. Masukkan narasi maksimal 5.000 kata.",
                "code": "TEXT_TOO_LONG",
            },
        )

    # Step 4: Check if text is political content (BR4)
    if not is_political_content(extracted_text):
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": (
                    "Teks yang Anda masukkan tidak terdeteksi sebagai narasi berita "
                    "atau opini politik. Sistem ini khusus untuk menganalisis "
                    "objektivitas narasi politik."
                ),
                "code": "NOT_POLITICAL",
            },
        )

    # Step 5: Detect language (FR3.3)
    detected_language = detect_language(extracted_text)

    # Step 6: AI Analysis via Groq
    try:
        analysis_result = await analyze_text(extracted_text, detected_language)
    except (ValueError, RuntimeError) as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Gagal menganalisis teks: {e!s}",
                "code": "ANALYSIS_ERROR",
            },
        )

    # Step 7: Save to database
    ip_hash = get_client_ip_hash(request)

    # Get user_id from auth header if present
    user_id = await get_current_user_optional(request)

    try:
        supabase = get_supabase_client()
        insert_data = {
            "user_id": user_id,
            "input_type": input_type,
            "raw_input": raw_input_stored[:10000],  # Limit stored input size
            "extracted_text": extracted_text[:50000],  # Limit stored text size
            "detected_language": detected_language,
            "score": analysis_result["score"],
            "label": analysis_result["label"],
            "reasoning": analysis_result["reasoning"],
            "highlighted_issues": analysis_result.get("highlighted_issues", []),
            "buzzer_indicators": analysis_result["buzzer_indicators"],
            "ip_hash": ip_hash,
        }
        db_result = supabase.table("analyses").insert(insert_data).execute()
        if not db_result.data or not db_result.data[0].get("id"):
            raise RuntimeError("Database tidak mengembalikan record ID setelah penyimpanan.")
        analysis_id = db_result.data[0]["id"]
    except Exception as e:
        logger.exception("Gagal menyimpan hasil analisis ke database: %s", e)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Gagal menyimpan hasil analisis ke database. Silakan coba lagi.",
                "code": "DATABASE_ERROR",
            },
        )

    # Step 8: Return result
    return {
        "success": True,
        "data": {
            "id": analysis_id,
            "analysis_id": analysis_id,
            "input_type": input_type,
            "extracted_text": extracted_text[:500] + ("..." if len(extracted_text) > 500 else ""),
            "detected_language": detected_language,
            "score": analysis_result["score"],
            "label": analysis_result["label"],
            "reasoning": analysis_result["reasoning"],
            "highlighted_issues": analysis_result.get("highlighted_issues", []),
            "buzzer_indicators": analysis_result["buzzer_indicators"],
        },
    }
