"""
API Dependencies

Dependency injection functions for FastAPI routes.
Provides Supabase client and other shared resources.
"""

from typing import AsyncGenerator
from fastapi import HTTPException, status
from supabase import AsyncClient, create_async_client

from api.config import get_settings
from api.validation import sanitize_error_message


async def get_supabase_client() -> AsyncGenerator[AsyncClient, None]:
    """Get Supabase async client for database operations.

    Yields an initialized Supabase client that can be used
    for database queries. Client is automatically cleaned up
    after request completion.

    Yields:
        AsyncClient: Initialized Supabase client

    Example:
        @router.get("/diseases")
        async def list_diseases(client: AsyncClient = Depends(get_supabase_client)):
            response = await client.table("diseases").select("*").execute()
            return response.data
    """
    settings = get_settings()

    try:
        client = await create_async_client(settings.supabase_url, settings.supabase_key)
        yield client
    except Exception as e:
        # Sanitize error to prevent leaking sensitive connection details
        safe_message = sanitize_error_message(str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {safe_message}",
        )
    finally:
        # Cleanup is handled automatically by Supabase client
        pass
