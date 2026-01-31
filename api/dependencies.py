"""
API Dependencies

Dependency injection functions for FastAPI routes.
Provides Supabase client connection pooling and other shared resources.

The Supabase client is initialized once at startup and reused across all requests
to avoid creating new connections for each request (which would exhaust connections
under load).
"""

import logging
import os
from typing import AsyncGenerator, Optional
from urllib.parse import urlparse

from fastapi import HTTPException, status
from supabase import AsyncClient, create_async_client

from api.config import get_settings
from api.validation import sanitize_error_message

logger = logging.getLogger(__name__)

# Required indexes for the Disease-Relater database
REQUIRED_INDEXES = {
    "diseases": [
        "idx_diseases_icd_code",
        "idx_diseases_chapter",
        "idx_diseases_granularity",
    ],
    "disease_relationships": [
        "idx_rel_disease1",
        "idx_rel_disease2",
        "idx_rel_odds_ratio",
        "idx_rel_composite",
    ],
    "prevalence_stratified": [
        "idx_prev_disease",
        "idx_prev_sex",
    ],
}

# Global Supabase client instance (singleton pattern)
# Initialized at startup, reused across requests
_supabase_client: Optional[AsyncClient] = None


async def init_supabase_client() -> AsyncClient:
    """Initialize the global Supabase client.

    Called once during application startup to create a shared client instance.
    The Supabase async client uses httpx under the hood, which manages
    connection pooling automatically.

    Returns:
        AsyncClient: Initialized Supabase client

    Raises:
        RuntimeError: If initialization fails
    """
    global _supabase_client

    if _supabase_client is not None:
        logger.warning(
            "Supabase client already initialized, returning existing instance"
        )
        return _supabase_client

    settings = get_settings()

    # Settings validation ensures these are never None after initialization
    if not settings.supabase_url or not settings.supabase_key:
        raise RuntimeError("Supabase URL and key must be configured")

    try:
        logger.info("Initializing Supabase client...")
        _supabase_client = await create_async_client(
            settings.supabase_url,
            settings.supabase_key,
        )
        logger.info("Supabase client initialized successfully")
        return _supabase_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        raise RuntimeError(f"Supabase client initialization failed: {e}")


async def close_supabase_client() -> None:
    """Close the global Supabase client.

    Called during application shutdown to clean up resources.
    """
    global _supabase_client

    if _supabase_client is not None:
        logger.info("Closing Supabase client...")
        # The Supabase AsyncClient doesn't have a close method directly,
        # but we can close the underlying postgrest client if needed
        try:
            if hasattr(_supabase_client, "postgrest") and hasattr(
                _supabase_client.postgrest, "aclose"
            ):
                await _supabase_client.postgrest.aclose()
        except Exception as e:
            logger.warning(f"Error closing Supabase client: {e}")
        finally:
            _supabase_client = None
            logger.info("Supabase client closed")


def get_supabase_client_sync() -> Optional[AsyncClient]:
    """Get the current Supabase client instance (non-async).

    Returns:
        The global Supabase client or None if not initialized
    """
    return _supabase_client


async def get_supabase_client() -> AsyncGenerator[AsyncClient, None]:
    """Get Supabase async client for database operations.

    Uses the shared client instance initialized at startup.
    This avoids creating a new connection for each request,
    which would exhaust database connections under load.

    Yields:
        AsyncClient: Shared Supabase client instance

    Raises:
        HTTPException: If client is not initialized (503)

    Example:
        @router.get("/diseases")
        async def list_diseases(client: AsyncClient = Depends(get_supabase_client)):
            response = await client.table("diseases").select("*").execute()
            return response.data
    """
    global _supabase_client

    if _supabase_client is None:
        # Client should be initialized at startup, but handle edge case
        logger.warning(
            "Supabase client not initialized, attempting late initialization"
        )
        try:
            await init_supabase_client()
        except Exception as e:
            safe_message = sanitize_error_message(str(e))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Database connection not available: {safe_message}",
            )

    # After init, client should be available
    if _supabase_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection not available",
        )

    yield _supabase_client


async def verify_database_indexes() -> tuple[bool, list[str]]:
    """Verify that all required database indexes exist.

    Uses direct PostgreSQL connection to check pg_indexes.
    Requires either SUPABASE_DB_URL or (SUPABASE_URL + DB_PASSWORD).

    Returns:
        Tuple of (all_indexes_exist, list_of_missing_indexes)

    Note:
        This is a non-blocking check that logs warnings for missing indexes
        but does not prevent the application from starting.
    """
    try:
        import psycopg2
    except ImportError:
        logger.warning(
            "psycopg2 not installed, skipping index verification. "
            "Install with: pip install psycopg2-binary"
        )
        return True, []

    # Get database connection info
    db_url = os.getenv("SUPABASE_DB_URL", "")
    db_password = os.getenv("DB_PASSWORD", "")
    settings = get_settings()

    if not db_url and not db_password:
        logger.warning(
            "Index verification requires SUPABASE_DB_URL or DB_PASSWORD. "
            "Skipping verification. Run 'python scripts/verify_indexes.py' manually."
        )
        return True, []

    try:
        # Determine connection parameters
        if db_url:
            parsed = urlparse(db_url)
            if parsed.scheme == "https" and "supabase.co" in (parsed.hostname or ""):
                # Supabase API URL, need to construct DB URL
                project_ref = (parsed.hostname or "").replace(".supabase.co", "")
                db_host = f"db.{project_ref}.supabase.co"
                conn_params = {
                    "host": db_host,
                    "port": 5432,
                    "database": "postgres",
                    "user": "postgres",
                    "password": db_password,
                }
            else:
                # Direct PostgreSQL URL
                conn_params = {
                    "host": parsed.hostname,
                    "port": parsed.port or 5432,
                    "database": parsed.path.lstrip("/") if parsed.path else "postgres",
                    "user": parsed.username or "postgres",
                    "password": parsed.password or db_password,
                }
        elif settings.supabase_url:
            # Use Supabase URL + DB_PASSWORD
            parsed = urlparse(settings.supabase_url)
            project_ref = (parsed.hostname or "").replace(".supabase.co", "")
            db_host = f"db.{project_ref}.supabase.co"
            conn_params = {
                "host": db_host,
                "port": 5432,
                "database": "postgres",
                "user": "postgres",
                "password": db_password,
            }
        else:
            logger.warning(
                "Could not determine database connection for index verification"
            )
            return True, []

        # Connect and verify indexes
        conn = psycopg2.connect(**conn_params)
        missing_indexes = []

        try:
            with conn.cursor() as cursor:
                for table_name, required_indexes in REQUIRED_INDEXES.items():
                    # Get existing indexes for this table
                    cursor.execute(
                        """
                        SELECT indexname FROM pg_indexes WHERE tablename = %s;
                        """,
                        (table_name,),
                    )
                    existing = {row[0] for row in cursor.fetchall()}

                    # Check which required indexes are missing
                    for index_name in required_indexes:
                        if index_name not in existing:
                            missing_indexes.append(f"{table_name}.{index_name}")
        finally:
            conn.close()

        if missing_indexes:
            logger.warning(
                f"Missing database indexes: {', '.join(missing_indexes)}. "
                f"Run 'python scripts/migrations/001_add_composite_index.sql' or "
                f"'python scripts/import_to_database.py' to create indexes."
            )
            return False, missing_indexes
        else:
            logger.info("All required database indexes verified")
            return True, []

    except Exception as e:
        logger.warning(
            f"Index verification failed: {e}. Continuing without verification."
        )
        return True, []
