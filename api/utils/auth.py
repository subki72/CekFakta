import logging

from fastapi import HTTPException, Request

from api.services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


async def get_current_user_optional(request: Request) -> str | None:
    """
    Extract and validate user_id from Bearer token.
    Syncs the user profile from auth.users to public.users on first login atomically.
    Returns user_id (UUID string from public.users) or None if not authenticated.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header.replace("Bearer ", "")

    try:
        supabase = get_supabase_client()
        user_response = supabase.auth.get_user(token)

        if user_response and user_response.user:
            auth_user = user_response.user

            # Atomic upsert eliminates check-then-act race conditions
            upsert_data = {
                "auth_id": auth_user.id,
                "email": auth_user.email,
                "name": auth_user.user_metadata.get("name") if auth_user.user_metadata else None,
            }

            upsert_result = (
                supabase.table("users")
                .upsert(upsert_data, on_conflict="auth_id")
                .execute()
            )
            if upsert_result.data:
                return upsert_result.data[0]["id"]
    except Exception as e:
        logger.warning(f"Auth error during token verification: {e}")

async def require_auth(request: Request) -> str:
    """
    Extract and validate user_id from Bearer token, enforcing authentication.
    Raises HTTPException 401 if unauthenticated.
    """
    user_id = await get_current_user_optional(request)
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Silakan login terlebih dahulu untuk melanjutkan.",
        )
    return user_id

