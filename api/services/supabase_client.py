"""
Supabase client initialization.

Provides a singleton Supabase client for the entire backend.
Uses SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY from environment variables.
Service role key is used (instead of anon key) because the backend needs
full database access without row-level security restrictions.
"""

import os
from functools import lru_cache

from supabase import Client, create_client


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Create and return a singleton Supabase client instance."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL dan SUPABASE_SERVICE_ROLE_KEY harus diset di environment variables. "
            "Lihat .env.example untuk contoh."
        )

    return create_client(url, key)
