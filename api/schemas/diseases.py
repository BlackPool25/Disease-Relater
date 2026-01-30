"""
Disease Pydantic Schemas

Agent 2: GET Endpoints Implementation
Defines Pydantic models for disease-related API responses with examples.
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DiseaseResponse(BaseModel):
    """Disease data model matching database schema."""

    id: int = Field(..., description="Unique disease identifier")
    icd_code: str = Field(..., description="ICD-10 code (e.g., E11)")
    name_english: Optional[str] = Field(None, description="Disease name in English")
    name_german: Optional[str] = Field(None, description="Disease name in German")
    chapter_code: Optional[str] = Field(
        None, description="ICD chapter code (Roman numeral)"
    )
    chapter_name: Optional[str] = Field(None, description="ICD chapter name")
    prevalence_male: Optional[float] = Field(
        None, description="Prevalence rate in male population (0-1)"
    )
    prevalence_female: Optional[float] = Field(
        None, description="Prevalence rate in female population (0-1)"
    )
    prevalence_total: Optional[float] = Field(
        None, description="Overall prevalence rate (0-1)"
    )
    vector_x: Optional[float] = Field(
        None, description="X coordinate in 3D visualization space"
    )
    vector_y: Optional[float] = Field(
        None, description="Y coordinate in 3D visualization space"
    )
    vector_z: Optional[float] = Field(
        None, description="Z coordinate in 3D visualization space"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "icd_code": "E11",
                "name_english": "Type 2 diabetes mellitus",
                "name_german": "Diabetes mellitus Typ 2",
                "chapter_code": "IV",
                "chapter_name": "Endocrine, nutritional and metabolic diseases",
                "prevalence_male": 0.085,
                "prevalence_female": 0.068,
                "prevalence_total": 0.076,
                "vector_x": -0.234,
                "vector_y": 0.567,
                "vector_z": -0.123,
            }
        }
    )


class DiseaseListResponse(BaseModel):
    """Response model for disease list endpoint."""

    diseases: list[DiseaseResponse] = Field(..., description="List of disease objects")
    total: int = Field(..., description="Total number of diseases matching the query")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "diseases": [
                    {
                        "id": 1,
                        "icd_code": "E11",
                        "name_english": "Type 2 diabetes mellitus",
                        "name_german": "Diabetes mellitus Typ 2",
                        "chapter_code": "IV",
                        "chapter_name": "Endocrine, nutritional and metabolic diseases",
                        "prevalence_male": 0.085,
                        "prevalence_female": 0.068,
                        "prevalence_total": 0.076,
                        "vector_x": -0.234,
                        "vector_y": 0.567,
                        "vector_z": -0.123,
                    }
                ],
                "total": 1080,
            }
        }
    )


class ChapterResponse(BaseModel):
    """ICD chapter with disease count."""

    chapter_code: str = Field(..., description="ICD chapter code (Roman numeral I-XXI)")
    chapter_name: str = Field(..., description="ICD chapter name")
    disease_count: int = Field(..., description="Number of diseases in this chapter")
    avg_prevalence: Optional[float] = Field(
        None, description="Average prevalence across diseases in chapter"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chapter_code": "IX",
                "chapter_name": "Diseases of the circulatory system",
                "disease_count": 156,
                "avg_prevalence": 0.142,
            }
        }
    )


class RelatedDiseaseResponse(BaseModel):
    """Related disease with relationship metrics."""

    id: int = Field(..., description="Unique disease identifier")
    icd_code: str = Field(..., description="ICD-10 code")
    name_english: Optional[str] = Field(None, description="Disease name in English")
    name_german: Optional[str] = Field(None, description="Disease name in German")
    chapter_code: Optional[str] = Field(None, description="ICD chapter code")
    odds_ratio: float = Field(
        ..., description="Odds ratio for comorbidity relationship (>=1.0)"
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
                "id": 45,
                "icd_code": "I10",
                "name_english": "Essential hypertension",
                "name_german": "Essentielle Hypertonie",
                "chapter_code": "IX",
                "odds_ratio": 2.34,
                "p_value": 0.001,
                "relationship_strength": "moderate",
                "patient_count_total": 15234,
            }
        }
    )


class SearchResultResponse(BaseModel):
    """Search result model."""

    id: int = Field(..., description="Unique disease identifier")
    icd_code: str = Field(..., description="ICD-10 code")
    name_english: Optional[str] = Field(None, description="Disease name in English")
    name_german: Optional[str] = Field(None, description="Disease name in German")
    chapter_code: Optional[str] = Field(None, description="ICD chapter code")
    chapter_name: Optional[str] = Field(None, description="ICD chapter name")
    prevalence_total: Optional[float] = Field(
        None, description="Overall prevalence rate"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "icd_code": "E11",
                "name_english": "Type 2 diabetes mellitus",
                "name_german": "Diabetes mellitus Typ 2",
                "chapter_code": "IV",
                "chapter_name": "Endocrine, nutritional and metabolic diseases",
                "prevalence_total": 0.076,
            }
        }
    )


class PrevalenceResponse(BaseModel):
    """Prevalence data response."""

    icd_code: str = Field(..., description="ICD-10 code")
    name_english: Optional[str] = Field(None, description="Disease name in English")
    name_german: Optional[str] = Field(None, description="Disease name in German")
    chapter_code: Optional[str] = Field(None, description="ICD chapter code")
    prevalence: Optional[float] = Field(None, description="Population prevalence rate")
    prevalence_male: Optional[float] = Field(
        None, description="Male population prevalence"
    )
    prevalence_female: Optional[float] = Field(
        None, description="Female population prevalence"
    )
    prevalence_total: Optional[float] = Field(
        None, description="Overall prevalence rate"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "icd_code": "E11",
                "name_english": "Type 2 diabetes mellitus",
                "name_german": "Diabetes mellitus Typ 2",
                "chapter_code": "IV",
                "prevalence": 0.076,
                "prevalence_male": 0.085,
                "prevalence_female": 0.068,
                "prevalence_total": 0.076,
            }
        }
    )
