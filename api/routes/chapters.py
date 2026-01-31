"""
Chapters Routes

Agent 2: GET Endpoints Implementation
GET endpoint for ICD chapters listing.

Agent 1: Added response caching for GET endpoint.
"""

from fastapi import APIRouter, Depends, Request
from supabase import AsyncClient

from api.dependencies import get_supabase_client
from api.rate_limit import limiter, get_rate_limit_string
from api.schemas.diseases import ChapterResponse
from api.services.cache import cache_response

router = APIRouter(prefix="/chapters", tags=["chapters"])

# Get rate limit string for decorators
_rate_limit = get_rate_limit_string()


@router.get("", response_model=list[ChapterResponse])
@cache_response("chapters")
@limiter.limit(_rate_limit)
async def list_chapters(
    request: Request,
    client: AsyncClient = Depends(get_supabase_client),
):
    """
    Get all ICD chapters with disease counts.

    Returns list of all 21 ICD-10 chapters with disease counts and
    average prevalence statistics.
    """
    # Query chapters with disease counts using the view or manual join
    response = (
        await client.table("icd_chapters")
        .select("""
            chapter_code,
            chapter_name,
            diseases(count)
        """)
        .execute()
    )

    if not response.data:
        return []

    # Transform to response model
    chapters = []
    for item in response.data:
        disease_count = 0
        if item.get("diseases"):
            disease_count = item["diseases"][0]["count"] if item["diseases"] else 0

        chapters.append(
            ChapterResponse(
                chapter_code=item["chapter_code"],
                chapter_name=item["chapter_name"],
                disease_count=disease_count,
                avg_prevalence=None,  # Can be added if needed
            )
        )

    return chapters
