import asyncio
import logging
import os
import re
import smtplib
from email.message import EmailMessage

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from api.services.supabase_client import get_supabase_client
from api.utils.auth import get_current_user_optional
from api.utils.rate_limiter import RateLimitExceeded, check_rate_limit

logger = logging.getLogger(__name__)
router = APIRouter()


class FeedbackRequest(BaseModel):
    subject: str = Field(..., min_length=3, max_length=200)
    message: str = Field(..., min_length=10, max_length=5000)


def _send_email_sync(
    msg: EmailMessage,
    smtp_server: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str,
) -> None:
    """Send email synchronously in a worker thread."""
    if smtp_port == 465:
        with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10.0) as server:
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10.0) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)


@router.post("/submit")
async def submit_feedback(payload: FeedbackRequest, request: Request):
    try:
        check_rate_limit(request)
    except RateLimitExceeded:
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "error": "Terlalu banyak permintaan. Silakan tunggu beberapa saat.",
                "code": "RATE_LIMIT_EXCEEDED",
            },
        )

    user_id = await get_current_user_optional(request)
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "error": "Silakan login terlebih dahulu untuk mengirim kritik dan saran.",
                "code": "AUTH_REQUIRED",
            },
        )

    if not payload.subject.strip() or not payload.message.strip():
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": "Topik dan pesan tidak boleh kosong.",
                "code": "INVALID_INPUT",
            },
        )

    # Get user info from database
    try:
        supabase = get_supabase_client()
        result = supabase.table("users").select("name, email").eq("id", user_id).execute()
        if not result.data:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": "Pengguna tidak ditemukan.",
                    "code": "USER_NOT_FOUND",
                },
            )

        user_name = result.data[0].get("name") or "User"
        user_email = result.data[0].get("email") or "Unknown Email"
    except Exception:
        logger.exception("Database error while fetching user for feedback")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Terjadi kesalahan saat memproses data pengguna.",
                "code": "DATABASE_ERROR",
            },
        )

    # Prepare email
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    recipient_email = os.getenv("FEEDBACK_RECIPIENT_EMAIL") or os.getenv("ADMIN_EMAIL") or smtp_username

    if not smtp_username or not smtp_password or not recipient_email:
        logger.warning("SMTP credentials or FEEDBACK_RECIPIENT_EMAIL not configured in env. Simulating email sending.")
        return {"success": True, "sent": True, "note": "Simulated (No SMTP Config)"}

    # Sanitize subject to prevent SMTP header injection
    clean_subject = re.sub(r"[\r\n]+", " ", payload.subject).strip()[:150]

    msg = EmailMessage()
    msg.set_content(f"Dari: {user_name} ({user_email})\n\nPesan:\n{payload.message}")
    msg["Subject"] = f"[Kritik & Saran FG] {clean_subject}"
    msg["From"] = smtp_username
    msg["To"] = recipient_email

    try:
        # Offload synchronous SMTP I/O to thread pool to avoid blocking the event loop
        await asyncio.to_thread(
            _send_email_sync,
            msg,
            smtp_server,
            smtp_port,
            smtp_username,
            smtp_password,
        )
    except Exception:
        logger.exception("SMTP Error while sending feedback email")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Gagal mengirim email. Pastikan konfigurasi SMTP benar.",
                "code": "EMAIL_SEND_FAILED",
            },
        )

    return {"success": True, "sent": True}

