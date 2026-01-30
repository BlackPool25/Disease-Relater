"""
Risk Calculation API Schemas

Pydantic models for the POST /api/calculate-risk endpoint.
Defines request and response validation schemas with examples.
"""

from typing import Literal, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class RiskCalculationRequest(BaseModel):
    """Request model for risk calculation endpoint.

    Contains user demographic data and existing conditions for risk assessment.
    """

    age: int = Field(ge=1, le=120, description="Age in years (1-120)")
    gender: Literal["male", "female"] = Field(
        description="User gender for prevalence stratification"
    )
    bmi: float = Field(ge=10.0, le=60.0, description="Body Mass Index (10-60)")
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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "age": 45,
                "gender": "male",
                "bmi": 28.5,
                "existing_conditions": ["E11", "I10"],
                "exercise_level": "moderate",
                "smoking": False,
            }
        }
    )


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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "disease_id": "N18",
                "disease_name": "Chronic kidney disease",
                "risk": 0.72,
                "level": "high",
                "contributing_factors": ["existing:E11", "existing:I10"],
            }
        }
    )


class UserPosition(BaseModel):
    """User's position in 3D disease space.

    Weighted average of user's existing conditions' 3D coordinates.
    """

    x: float = Field(description="X coordinate in 3D space")
    y: float = Field(description="Y coordinate in 3D space")
    z: float = Field(description="Z coordinate in 3D space")

    model_config = ConfigDict(
        json_schema_extra={"example": {"x": -0.145, "y": 0.398, "z": -0.067}}
    )


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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "risk_scores": [
                    {
                        "disease_id": "N18",
                        "disease_name": "Chronic kidney disease",
                        "risk": 0.72,
                        "level": "high",
                        "contributing_factors": ["existing:E11", "existing:I10"],
                    },
                    {
                        "disease_id": "E78",
                        "disease_name": "Disorders of lipoprotein metabolism",
                        "risk": 0.45,
                        "level": "moderate",
                        "contributing_factors": ["existing:E11", "demographic:male"],
                    },
                ],
                "user_position": {"x": -0.145, "y": 0.398, "z": -0.067},
                "total_conditions_analyzed": 2,
                "analysis_metadata": {
                    "calculation_timestamp": "2026-01-30T12:00:00Z",
                    "model_version": "1.0.0",
                },
            }
        }
    )
