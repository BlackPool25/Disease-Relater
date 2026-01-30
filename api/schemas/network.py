"""
Network Pydantic Schemas

Agent 2: GET Endpoints Implementation
Defines Pydantic models for network-related API responses with examples.
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class NetworkNode(BaseModel):
    """Network node representing a disease with 3D coordinates."""

    id: int = Field(..., description="Unique disease identifier")
    icd_code: str = Field(..., description="ICD-10 code")
    name_english: Optional[str] = Field(None, description="Disease name in English")
    name_german: Optional[str] = Field(None, description="Disease name in German")
    chapter_code: Optional[str] = Field(None, description="ICD chapter code")
    vector_x: Optional[float] = Field(
        None, description="X coordinate in 3D visualization space"
    )
    vector_y: Optional[float] = Field(
        None, description="Y coordinate in 3D visualization space"
    )
    vector_z: Optional[float] = Field(
        None, description="Z coordinate in 3D visualization space"
    )
    prevalence_total: Optional[float] = Field(
        None, description="Overall prevalence rate (0-1)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "icd_code": "E11",
                "name_english": "Type 2 diabetes mellitus",
                "name_german": "Diabetes mellitus Typ 2",
                "chapter_code": "IV",
                "vector_x": -0.234,
                "vector_y": 0.567,
                "vector_z": -0.123,
                "prevalence_total": 0.076,
            }
        }
    )


class NetworkEdge(BaseModel):
    """Network edge representing a comorbidity relationship between two diseases."""

    source: int = Field(..., description="Source disease ID")
    target: int = Field(..., description="Target disease ID")
    source_icd: str = Field(..., description="Source disease ICD-10 code")
    target_icd: str = Field(..., description="Target disease ICD-10 code")
    source_name: Optional[str] = Field(
        None, description="Source disease name in English"
    )
    target_name: Optional[str] = Field(
        None, description="Target disease name in English"
    )
    odds_ratio: float = Field(
        ..., description="Odds ratio for the relationship (>=1.0)"
    )
    p_value: Optional[float] = Field(
        None, description="Statistical significance p-value"
    )
    relationship_strength: Optional[str] = Field(
        None, description="Qualitative strength: weak, moderate, strong, very_strong"
    )
    patient_count_total: Optional[int] = Field(
        None, description="Number of patients with both diseases"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source": 1,
                "target": 45,
                "source_icd": "E11",
                "target_icd": "I10",
                "source_name": "Type 2 diabetes mellitus",
                "target_name": "Essential hypertension",
                "odds_ratio": 2.34,
                "p_value": 0.001,
                "relationship_strength": "moderate",
                "patient_count_total": 15234,
            }
        }
    )


class NetworkMetadata(BaseModel):
    """Metadata for network response describing query parameters and result counts."""

    min_odds_ratio: float = Field(..., description="Minimum odds ratio filter applied")
    chapter_filter: Optional[str] = Field(
        None, description="Chapter filter applied (if any)"
    )
    total_nodes: int = Field(..., description="Total number of nodes in the network")
    total_edges: int = Field(..., description="Total number of edges in the network")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "min_odds_ratio": 1.5,
                "chapter_filter": None,
                "total_nodes": 850,
                "total_edges": 3200,
            }
        }
    )


class NetworkResponse(BaseModel):
    """Complete network data response with nodes, edges, and metadata."""

    nodes: list[NetworkNode] = Field(
        ..., description="List of disease nodes with 3D coordinates"
    )
    edges: list[NetworkEdge] = Field(
        ..., description="List of comorbidity relationship edges"
    )
    metadata: NetworkMetadata = Field(
        ..., description="Query metadata and result counts"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nodes": [
                    {
                        "id": 1,
                        "icd_code": "E11",
                        "name_english": "Type 2 diabetes mellitus",
                        "name_german": "Diabetes mellitus Typ 2",
                        "chapter_code": "IV",
                        "vector_x": -0.234,
                        "vector_y": 0.567,
                        "vector_z": -0.123,
                        "prevalence_total": 0.076,
                    }
                ],
                "edges": [
                    {
                        "source": 1,
                        "target": 45,
                        "source_icd": "E11",
                        "target_icd": "I10",
                        "source_name": "Type 2 diabetes mellitus",
                        "target_name": "Essential hypertension",
                        "odds_ratio": 2.34,
                        "p_value": 0.001,
                        "relationship_strength": "moderate",
                        "patient_count_total": 15234,
                    }
                ],
                "metadata": {
                    "min_odds_ratio": 1.5,
                    "chapter_filter": None,
                    "total_nodes": 850,
                    "total_edges": 3200,
                },
            }
        }
    )
