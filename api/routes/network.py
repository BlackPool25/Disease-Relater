"""
Network Routes

Agent 2: GET Endpoints Implementation
GET endpoint for network data visualization.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from supabase import AsyncClient

from api.dependencies import get_supabase_client
from api.rate_limit import limiter, get_rate_limit_string
from api.schemas.network import (
    NetworkEdge,
    NetworkMetadata,
    NetworkNode,
    NetworkResponse,
)

router = APIRouter(prefix="/network", tags=["network"])

# Get rate limit string for decorators
_rate_limit = get_rate_limit_string()


@router.get("", response_model=NetworkResponse)
@limiter.limit(_rate_limit)
async def get_network(
    request: Request,
    min_odds_ratio: float = Query(
        1.5, gt=0, description="Minimum odds ratio for edges"
    ),
    max_edges: Optional[int] = Query(
        None, ge=1, le=10000, description="Maximum edges to return"
    ),
    chapter_filter: Optional[str] = Query(None, description="Filter by ICD chapter"),
    client: AsyncClient = Depends(get_supabase_client),
):
    """
    Get network data with nodes and edges for visualization.

    Returns complete network data including disease nodes with 3D coordinates
    and edges representing comorbidity relationships.
    """
    # Build nodes query
    nodes_query = client.table("diseases").select(
        "id, icd_code, name_english, name_german, chapter_code, "
        "vector_x, vector_y, vector_z, prevalence_total"
    )
    nodes_query = nodes_query.eq("has_3d_coordinates", True)

    if chapter_filter:
        nodes_query = nodes_query.eq("chapter_code", chapter_filter)

    nodes_response = await nodes_query.execute()

    if not nodes_response.data:
        return NetworkResponse(
            nodes=[],
            edges=[],
            metadata=NetworkMetadata(
                min_odds_ratio=min_odds_ratio,
                chapter_filter=chapter_filter,
                total_nodes=0,
                total_edges=0,
            ),
        )

    # Build edges query
    edges_query = (
        client.table("disease_relationships")
        .select("""
            disease_1_id,
            disease_2_id,
            odds_ratio,
            p_value,
            relationship_strength,
            patient_count_total,
            disease_1:disease_1_id(icd_code, name_english),
            disease_2:disease_2_id(icd_code, name_english)
        """)
        .gte("odds_ratio", min_odds_ratio)
        .order("odds_ratio", desc=True)
    )

    if chapter_filter:
        # Filter edges where at least one disease is in the chapter
        edges_query = edges_query.or_(
            f"icd_chapter_1.eq.{chapter_filter},icd_chapter_2.eq.{chapter_filter}"
        )

    if max_edges:
        edges_query = edges_query.limit(max_edges)

    edges_response = await edges_query.execute()

    # Transform nodes
    nodes = []
    for item in nodes_response.data:
        nodes.append(
            NetworkNode(
                id=item["id"],
                icd_code=item["icd_code"],
                name_english=item.get("name_english"),
                name_german=item.get("name_german"),
                chapter_code=item.get("chapter_code"),
                vector_x=item.get("vector_x"),
                vector_y=item.get("vector_y"),
                vector_z=item.get("vector_z"),
                prevalence_total=item.get("prevalence_total"),
            )
        )

    # Transform edges
    edges = []
    if edges_response.data:
        for item in edges_response.data:
            disease_1 = item.get("disease_1", {})
            disease_2 = item.get("disease_2", {})

            edges.append(
                NetworkEdge(
                    source=item["disease_1_id"],
                    target=item["disease_2_id"],
                    source_icd=disease_1.get("icd_code", ""),
                    target_icd=disease_2.get("icd_code", ""),
                    source_name=disease_1.get("name_english"),
                    target_name=disease_2.get("name_english"),
                    odds_ratio=item["odds_ratio"],
                    p_value=item.get("p_value"),
                    relationship_strength=item.get("relationship_strength"),
                    patient_count_total=item.get("patient_count_total"),
                )
            )

    return NetworkResponse(
        nodes=nodes,
        edges=edges,
        metadata=NetworkMetadata(
            min_odds_ratio=min_odds_ratio,
            chapter_filter=chapter_filter,
            total_nodes=len(nodes),
            total_edges=len(edges),
        ),
    )
