"""
Diseases Routes

Agent 2: GET Endpoints Implementation
GET endpoints for disease listing, search, and detail.

Agent 1: Added response caching for GET endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from supabase import AsyncClient

from api.dependencies import get_supabase_client
from api.rate_limit import limiter, get_rate_limit_string
from api.schemas.diseases import (
    DiseaseListResponse,
    DiseaseResponse,
    RelatedDiseaseResponse,
    SearchResultResponse,
)
from api.services.cache import cache_response
from api.validation import validate_search_term

router = APIRouter(prefix="/diseases", tags=["diseases"])

# Get rate limit string for decorators
_rate_limit = get_rate_limit_string()


@router.get("", response_model=DiseaseListResponse)
@limiter.limit(_rate_limit)
@cache_response("diseases_list")
async def list_diseases(
    request: Request,
    chapter: Optional[str] = Query(
        None, description="Filter by ICD chapter code (e.g., IX, X)"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    client: AsyncClient = Depends(get_supabase_client),
):
    """
    Get list of diseases with optional chapter filter.

    Returns paginated list of diseases with chapter and limit filters.
    """
    # Build query
    query = client.table("diseases").select("*, icd_chapters(chapter_name)")

    if chapter:
        query = query.eq("chapter_code", chapter)

    # Execute query with pagination
    response = await query.range(offset, offset + limit - 1).execute()

    if not response.data:
        return DiseaseListResponse(diseases=[], total=0)

    # Get total count
    count_query = client.table("diseases").select("id", count="exact")
    if chapter:
        count_query = count_query.eq("chapter_code", chapter)
    count_result = await count_query.execute()
    total = count_result.count if hasattr(count_result, "count") else len(response.data)

    # Transform to response model
    diseases = []
    for item in response.data:
        chapter_name = None
        if item.get("icd_chapters"):
            chapter_name = item["icd_chapters"].get("chapter_name")

        diseases.append(
            DiseaseResponse(
                id=item["id"],
                icd_code=item["icd_code"],
                name_english=item.get("name_english"),
                name_german=item.get("name_german"),
                chapter_code=item.get("chapter_code"),
                chapter_name=chapter_name,
                prevalence_male=item.get("prevalence_male"),
                prevalence_female=item.get("prevalence_female"),
                prevalence_total=item.get("prevalence_total"),
                vector_x=item.get("vector_x"),
                vector_y=item.get("vector_y"),
                vector_z=item.get("vector_z"),
            )
        )

    return DiseaseListResponse(diseases=diseases, total=total or 0)


@router.get("/{disease_id}", response_model=DiseaseResponse)
@limiter.limit(_rate_limit)
@cache_response("disease_detail")
async def get_disease(
    request: Request,
    disease_id: str,
    client: AsyncClient = Depends(get_supabase_client),
):
    """
    Get single disease by ID or ICD code.

    Args:
        disease_id: Numeric ID or ICD code (e.g., 'E11', 'I10')
    """
    # Try to query by ID if numeric, otherwise by ICD code
    query = client.table("diseases").select("*, icd_chapters(chapter_name)")

    if disease_id.isdigit():
        query = query.eq("id", int(disease_id))
    else:
        query = query.eq("icd_code", disease_id)

    response = await query.execute()

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disease not found: {disease_id}",
        )

    item = response.data[0]
    chapter_name = None
    if item.get("icd_chapters"):
        chapter_name = item["icd_chapters"].get("chapter_name")

    return DiseaseResponse(
        id=item["id"],
        icd_code=item["icd_code"],
        name_english=item.get("name_english"),
        name_german=item.get("name_german"),
        chapter_code=item.get("chapter_code"),
        chapter_name=chapter_name,
        prevalence_male=item.get("prevalence_male"),
        prevalence_female=item.get("prevalence_female"),
        prevalence_total=item.get("prevalence_total"),
        vector_x=item.get("vector_x"),
        vector_y=item.get("vector_y"),
        vector_z=item.get("vector_z"),
    )


@router.get("/{disease_id}/related", response_model=list[RelatedDiseaseResponse])
@limiter.limit(_rate_limit)
async def get_related_diseases(
    request: Request,
    disease_id: str,
    limit: int = Query(50, ge=1, le=1000, description="Maximum results"),
    min_odds_ratio: float = Query(1.5, gt=0, description="Minimum odds ratio"),
    client: AsyncClient = Depends(get_supabase_client),
):
    """
    Get diseases related to specified disease, ordered by odds ratio.

    Args:
        disease_id: Numeric ID or ICD code
        limit: Maximum number of results
        min_odds_ratio: Minimum odds ratio threshold
    """
    # First get the disease ID if ICD code provided
    if not disease_id.isdigit():
        disease_response = await (
            client.table("diseases").select("id").eq("icd_code", disease_id).execute()
        )
        if not disease_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Disease not found: {disease_id}",
            )
        disease_id_int = disease_response.data[0]["id"]
    else:
        disease_id_int = int(disease_id)

    # Query relationships
    response = await (
        client.table("disease_relationships")
        .select("""
            *,
            disease_1:disease_1_id(
                id, icd_code, name_english, name_german, chapter_code
            ),
            disease_2:disease_2_id(
                id, icd_code, name_english, name_german, chapter_code
            )
        """)
        .or_(f"disease_1_id.eq.{disease_id_int},disease_2_id.eq.{disease_id_int}")
        .gte("odds_ratio", min_odds_ratio)
        .order("odds_ratio", desc=True)
        .limit(limit)
        .execute()
    )

    if not response.data:
        return []

    # Transform to response model
    related = []
    for item in response.data:
        # Determine which disease is the related one
        if item["disease_1_id"] == disease_id_int:
            related_disease = item["disease_2"]
        else:
            related_disease = item["disease_1"]

        related.append(
            RelatedDiseaseResponse(
                id=related_disease["id"],
                icd_code=related_disease["icd_code"],
                name_english=related_disease.get("name_english"),
                name_german=related_disease.get("name_german"),
                chapter_code=related_disease.get("chapter_code"),
                odds_ratio=item["odds_ratio"],
                p_value=item.get("p_value"),
                relationship_strength=item.get("relationship_strength"),
                patient_count_total=item.get("patient_count_total"),
            )
        )

    return related


@router.get("/search/{search_term}", response_model=list[SearchResultResponse])
@limiter.limit(_rate_limit)
async def search_diseases(
    request: Request,
    search_term: str,
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    client: AsyncClient = Depends(get_supabase_client),
):
    """
    Search diseases by name or ICD code.

    Args:
        search_term: Search string (min 2 characters)
        limit: Maximum number of results
    """
    # Validate search term to prevent SQL injection and malicious input
    is_valid, error_msg = validate_search_term(search_term)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    # Escape special SQL LIKE pattern characters to prevent injection
    escaped_term = (
        search_term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    )

    # Use safe ilike pattern matching with properly escaped term
    # The ilike_any_of pattern format: {pattern1,pattern2,pattern3}
    pattern = f"%{escaped_term}%"

    response = await (
        client.table("diseases")
        .select("*, icd_chapters(chapter_name)")
        .or_(
            f"name_english.ilike.{pattern},"
            f"name_german.ilike.{pattern},"
            f"icd_code.ilike.{pattern}"
        )
        .limit(limit)
        .execute()
    )

    if not response.data:
        return []

    # Transform to response model
    results = []
    for item in response.data:
        chapter_name = None
        if item.get("icd_chapters"):
            chapter_name = item["icd_chapters"].get("chapter_name")

        results.append(
            SearchResultResponse(
                id=item["id"],
                icd_code=item["icd_code"],
                name_english=item.get("name_english"),
                name_german=item.get("name_german"),
                chapter_code=item.get("chapter_code"),
                chapter_name=chapter_name,
                prevalence_total=item.get("prevalence_total"),
            )
        )

    return results
