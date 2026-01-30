"""
Disease Pydantic Schemas

Agent 2: GET Endpoints Implementation
Defines Pydantic models for disease-related API responses.
"""

from typing import Optional
from pydantic import BaseModel


class DiseaseResponse(BaseModel):
    """Disease data model matching database schema."""

    id: int
    icd_code: str
    name_english: Optional[str] = None
    name_german: Optional[str] = None
    chapter_code: Optional[str] = None
    chapter_name: Optional[str] = None
    prevalence_male: Optional[float] = None
    prevalence_female: Optional[float] = None
    prevalence_total: Optional[float] = None
    vector_x: Optional[float] = None
    vector_y: Optional[float] = None
    vector_z: Optional[float] = None


class DiseaseListResponse(BaseModel):
    """Response model for disease list endpoint."""

    diseases: list[DiseaseResponse]
    total: int


class ChapterResponse(BaseModel):
    """ICD chapter with disease count."""

    chapter_code: str
    chapter_name: str
    disease_count: int
    avg_prevalence: Optional[float] = None


class RelatedDiseaseResponse(BaseModel):
    """Related disease with relationship metrics."""

    id: int
    icd_code: str
    name_english: Optional[str] = None
    name_german: Optional[str] = None
    chapter_code: Optional[str] = None
    odds_ratio: float
    p_value: Optional[float] = None
    relationship_strength: Optional[str] = None
    patient_count_total: Optional[int] = None


class SearchResultResponse(BaseModel):
    """Search result model."""

    id: int
    icd_code: str
    name_english: Optional[str] = None
    name_german: Optional[str] = None
    chapter_code: Optional[str] = None
    chapter_name: Optional[str] = None
    prevalence_total: Optional[float] = None


class PrevalenceResponse(BaseModel):
    """Prevalence data response."""

    icd_code: str
    name_english: Optional[str] = None
    name_german: Optional[str] = None
    chapter_code: Optional[str] = None
    prevalence: Optional[float] = None
    prevalence_male: Optional[float] = None
    prevalence_female: Optional[float] = None
    prevalence_total: Optional[float] = None
