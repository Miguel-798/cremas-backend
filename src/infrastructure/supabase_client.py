"""
Supabase Client Factory - Infrastructure Layer

Creates Supabase client instances for use in route handlers.
"""
from typing import Optional

from supabase import create_client, Client

from src.infrastructure.config import settings


def get_supabase_client() -> Client:
    """
    Create a Supabase client instance.
    
    Uses the anon key for client-side operations.
    For server-side operations requiring elevated privileges,
    use get_supabase_admin_client() instead.
    """
    return create_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_anon_key,
    )


def get_supabase_admin_client() -> Client:
    """
    Create a Supabase client with service role key.
    
    WARNING: This bypasses RLS policies. Only use for:
    - Admin operations that legitimately need elevated access
    - Server-to-server communication
    - Operations that are already protected at the application layer
    """
    if not settings.supabase_service_role_key:
        raise ValueError(
            "SUPABASE_SERVICE_ROLE_KEY is not configured. "
            "Set it in your .env file."
        )
    
    return create_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_role_key,
    )
