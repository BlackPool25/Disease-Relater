"""
Network Pydantic Schemas

Agent 2: GET Endpoints Implementation
Defines Pydantic models for network-related API responses.
"""

from typing import Optional
from pydantic import BaseModel


class NetworkNode(BaseModel):
    """Network node representing a disease."""

    id: int
    icd_code: str
    name_english: Optional[str] = None
    name_german: Optional[str] = None
    chapter_code: Optional[str] = None
    vector_x: Optional[float] = None
    vector_y: Optional[float] = None
    vector_z: Optional[float] = None
    prevalence_total: Optional[float] = None


class NetworkEdge(BaseModel):
    """Network edge representing a disease relationship."""

    source: int
    target: int
    source_icd: str
    target_icd: str
    source_name: Optional[str] = None
    target_name: Optional[str] = None
    odds_ratio: float
    p_value: Optional[float] = None
    relationship_strength: Optional[str] = None
    patient_count_total: Optional[int] = None


class NetworkMetadata(BaseModel):
    """Metadata for network response."""

    min_odds_ratio: float
    chapter_filter: Optional[str] = None
    total_nodes: int
    total_edges: int


class NetworkResponse(BaseModel):
    """Complete network data response."""

    nodes: list[NetworkNode]
    edges: list[NetworkEdge]
    metadata: NetworkMetadata
