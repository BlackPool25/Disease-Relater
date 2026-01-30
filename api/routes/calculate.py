"""
Risk Calculation API Route

POST /api/calculate-risk endpoint for calculating disease risk scores.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import AsyncClient

from api.schemas.calculate import RiskCalculationRequest, RiskCalculationResponse
from api.services.risk_calculator import RiskCalculator
from api.dependencies import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["risk-calculation"])


@router.post(
    "/calculate-risk",
    response_model=RiskCalculationResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate disease risk scores",
    description="""
    Calculate personalized disease risk scores based on:
    - Existing conditions (ICD codes)
    - Demographics (age, gender, BMI)
    - Lifestyle factors (smoking, exercise)
    
    Returns risk scores for related diseases and user's 3D position.
    """,
    responses={
        200: {
            "description": "Risk calculation successful",
            "model": RiskCalculationResponse,
        },
        400: {
            "description": "Invalid request data or ICD codes",
        },
        500: {
            "description": "Internal server error",
        },
    },
)
async def calculate_risk(
    request: RiskCalculationRequest,
    client: AsyncClient = Depends(get_supabase_client),
) -> RiskCalculationResponse:
    """Calculate disease risk scores for a user.

    Args:
        request: RiskCalculationRequest with user data and conditions
        client: Supabase client injected via dependency

    Returns:
        RiskCalculationResponse with calculated scores and position

    Raises:
        HTTPException: 400 for invalid data, 500 for server errors
    """
    try:
        logger.info(f"Calculating risk for conditions: {request.existing_conditions}")

        calculator = RiskCalculator(client)
        result = await calculator.calculate_risks(request)

        return result

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error calculating risk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate risk scores",
        )
