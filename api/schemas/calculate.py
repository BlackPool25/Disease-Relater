"""
Risk Calculation API Schemas

Pydantic models for the POST /api/calculate-risk endpoint.
Defines request and response validation schemas.
"""

from typing import Literal, List
from pydantic import BaseModel, Field, field_validator


class RiskCalculationRequest(BaseModel):
    """Request model for risk calculation endpoint.

    Contains user demographic data and existing conditions for risk assessment.
    """

    age: int = Field(ge=0, le=120, description="User age in years")
    gender: Literal["male", "female"] = Field(
        description="User gender for prevalence stratification"
    )
    bmi: float = Field(gt=0, le=100, description="Body Mass Index")
    existing_conditions: List[str] = Field(
        description="List of ICD-10 codes for existing conditions",
        min_length=1,
        max_length=50,
    )
    exercise_level: Literal["sedentary", "light", "moderate", "active"] = Field(
        description="Physical activity level"
    )
    smoking: bool = Field(description="Current smoking status")

    @field_validator("existing_conditions")
    @classmethod
    def validate_icd_codes(cls, v: List[str]) -> List[str]:
        """Validate that ICD codes are properly formatted."""
        if not v:
            raise ValueError("At least one existing condition is required")

        for code in v:
            if not code or not isinstance(code, str):
                raise ValueError(f"Invalid ICD code: {code}")
            # Basic ICD format validation (alphanumeric, 3-7 chars)
            if len(code) < 2 or len(code) > 8:
                raise ValueError(f"ICD code {code} must be 2-8 characters")

        return v


class RiskScore(BaseModel):
    """Individual disease risk score model.

    Represents the calculated risk for a single disease.
    """

    disease_id: str = Field(description="ICD-10 code of the disease")
    disease_name: str = Field(description="English name of the disease")
    risk: float = Field(
        ge=0.0, le=1.0, description="Risk score from 0.0 (low) to 1.0 (high)"
    )
    level: Literal["low", "moderate", "high", "very_high"] = Field(
        description="Risk level classification"
    )
    contributing_factors: List[str] = Field(
        default_factory=list, description="Factors that contributed to this risk score"
    )


class UserPosition(BaseModel):
    """User's position in 3D disease space.

    Weighted average of user's existing conditions' 3D coordinates.
    """

    x: float = Field(description="X coordinate in 3D space")
    y: float = Field(description="Y coordinate in 3D space")
    z: float = Field(description="Z coordinate in 3D space")


class RiskCalculationResponse(BaseModel):
    """Response model for risk calculation endpoint.

    Contains calculated risk scores, user position, and metadata.
    """

    risk_scores: List[RiskScore] = Field(
        description="List of risk scores for related diseases"
    )
    user_position: UserPosition = Field(
        description="User's position in 3D disease space"
    )
    total_conditions_analyzed: int = Field(
        ge=0, description="Total number of conditions analyzed"
    )
    analysis_metadata: dict = Field(
        default_factory=dict, description="Additional analysis metadata"
    )
