"""
Unit Tests for Risk Calculator

Tests the risk calculation algorithm and API endpoint.

Updated for refactored calculation engine:
- Prevalence-based base risk
- Multiplicative comorbidity multipliers
- Category-specific lifestyle adjustments
- Age-based risk adjustments
"""

import pytest
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock

from api.schemas.calculate import (
    RiskCalculationRequest,
    RiskCalculationResponse,
    RiskScore,
    UserPosition,
)
from api.services.risk_calculator import RiskCalculator


class TestRiskCalculationRequest:
    """Test Pydantic request validation."""

    def test_valid_request(self):
        """Test creating a valid request."""
        request = RiskCalculationRequest(
            age=45,
            gender="male",
            bmi=28.5,
            existing_conditions=["E11", "I10"],
            exercise_level="moderate",
            smoking=False,
        )
        assert request.age == 45
        assert request.gender == "male"
        assert request.existing_conditions == ["E11", "I10"]

    def test_invalid_age(self):
        """Test age validation."""
        with pytest.raises(ValueError):
            RiskCalculationRequest(
                age=150,  # Too high
                gender="male",
                bmi=25.0,
                existing_conditions=["E11"],
                exercise_level="moderate",
                smoking=False,
            )

    def test_invalid_bmi(self):
        """Test BMI validation."""
        with pytest.raises(ValueError):
            RiskCalculationRequest(
                age=45,
                gender="male",
                bmi=150.0,  # Too high
                existing_conditions=["E11"],
                exercise_level="moderate",
                smoking=False,
            )

    def test_empty_conditions(self):
        """Test that empty conditions list is rejected."""
        with pytest.raises(ValueError):
            RiskCalculationRequest(
                age=45,
                gender="male",
                bmi=25.0,
                existing_conditions=[],  # Empty - should fail
                exercise_level="moderate",
                smoking=False,
            )

    def test_invalid_icd_format(self):
        """Test ICD code format validation."""
        with pytest.raises(ValueError):
            RiskCalculationRequest(
                age=45,
                gender="male",
                bmi=25.0,
                existing_conditions=["A"],  # Too short
                exercise_level="moderate",
                smoking=False,
            )

    def test_too_many_conditions(self):
        """Test max conditions limit."""
        with pytest.raises(ValueError):
            RiskCalculationRequest(
                age=45,
                gender="male",
                bmi=25.0,
                existing_conditions=["E11"] * 51,  # Too many
                exercise_level="moderate",
                smoking=False,
            )


class TestRiskCalculator:
    """Test RiskCalculator service methods."""

    @pytest.fixture
    def mock_client(self):
        """Create mock Supabase client."""
        client = AsyncMock()
        return client

    @pytest.fixture
    def calculator(self, mock_client):
        """Create RiskCalculator instance with mock client."""
        return RiskCalculator(mock_client)

    @pytest.fixture
    def sample_conditions(self) -> List[Dict]:
        """Sample condition data."""
        return [
            {
                "id": 1,
                "icd_code": "E11",
                "name_english": "Type 2 diabetes mellitus",
                "vector_x": 0.5,
                "vector_y": -0.3,
                "vector_z": 0.8,
                "prevalence_total": 0.042,
            },
            {
                "id": 2,
                "icd_code": "I10",
                "name_english": "Essential hypertension",
                "vector_x": -0.2,
                "vector_y": 0.4,
                "vector_z": -0.1,
                "prevalence_total": 0.182,
            },
        ]

    def test_classify_risk_level(self, calculator):
        """Test risk level classification."""
        assert calculator._classify_risk_level(0.85) == "very_high"
        assert calculator._classify_risk_level(0.65) == "high"
        assert calculator._classify_risk_level(0.35) == "moderate"
        assert calculator._classify_risk_level(0.15) == "low"
        assert calculator._classify_risk_level(0.0) == "low"

    def test_get_disease_category(self, calculator):
        """Test disease category classification from ICD codes."""
        # Metabolic diseases (E chapter)
        assert calculator._get_disease_category("E11") == "metabolic"
        assert calculator._get_disease_category("E10") == "metabolic"

        # Cardiovascular diseases (I chapter)
        assert calculator._get_disease_category("I10") == "cardiovascular"
        assert calculator._get_disease_category("I25") == "cardiovascular"

        # Respiratory diseases (J chapter)
        assert calculator._get_disease_category("J45") == "respiratory"
        assert calculator._get_disease_category("J44") == "respiratory"

        # Other diseases
        assert calculator._get_disease_category("N18") == "other"
        assert calculator._get_disease_category("K50") == "other"

        # Edge cases
        assert calculator._get_disease_category("") == "other"
        assert calculator._get_disease_category("X") == "other"

    def test_get_age_group(self, calculator):
        """Test age group classification."""
        # Elderly (65+)
        assert calculator._get_age_group(65) == "elderly"
        assert calculator._get_age_group(80) == "elderly"

        # Middle (45-64)
        assert calculator._get_age_group(45) == "middle"
        assert calculator._get_age_group(64) == "middle"

        # Young adult (30-44)
        assert calculator._get_age_group(30) == "young_adult"
        assert calculator._get_age_group(44) == "young_adult"

        # Young (<30)
        assert calculator._get_age_group(25) == "young"
        assert calculator._get_age_group(18) == "young"

    def test_calculate_position(self, calculator, sample_conditions):
        """Test 3D position calculation."""
        position = calculator._calculate_position(sample_conditions)

        # Calculate expected weighted average
        # E11: weight=0.042, coords=(0.5, -0.3, 0.8)
        # I10: weight=0.182, coords=(-0.2, 0.4, -0.1)
        # Total weight = 0.224

        assert isinstance(position, UserPosition)
        assert -1.0 <= position.x <= 1.0
        assert -1.0 <= position.y <= 1.0
        assert -1.0 <= position.z <= 1.0

    def test_calculate_position_empty(self, calculator):
        """Test position calculation with no conditions."""
        position = calculator._calculate_position([])
        assert position.x == 0.0
        assert position.y == 0.0
        assert position.z == 0.0

    def test_calculate_position_missing_coordinates(self, calculator):
        """Test position calculation with conditions missing 3D coordinates."""
        conditions = [
            {
                "icd_code": "E11",
                "name_english": "Type 2 diabetes mellitus",
                "vector_x": None,  # Missing x
                "vector_y": 0.5,
                "vector_z": None,  # Missing z
                "prevalence_total": 0.05,
            },
            {
                "icd_code": "I10",
                "name_english": "Hypertension",
                # All coordinates missing
                "prevalence_total": 0.1,
            },
        ]
        position = calculator._calculate_position(conditions)

        # Should still return valid position (using 0.0 defaults)
        assert isinstance(position, UserPosition)
        assert -1.0 <= position.x <= 1.0
        assert -1.0 <= position.y <= 1.0
        assert -1.0 <= position.z <= 1.0

    def test_calculate_position_all_zero_prevalence(self, calculator):
        """Test position calculation with all zero prevalence values."""
        conditions = [
            {
                "icd_code": "E11",
                "vector_x": 0.5,
                "vector_y": 0.3,
                "vector_z": -0.2,
                "prevalence_total": 0,  # Zero prevalence
            },
            {
                "icd_code": "I10",
                "vector_x": -0.4,
                "vector_y": 0.1,
                "vector_z": 0.6,
                "prevalence_total": 0,  # Zero prevalence
            },
        ]
        position = calculator._calculate_position(conditions)

        # Should use default weight of 1.0 for each, resulting in simple average
        assert isinstance(position, UserPosition)
        # Simple average: x = (0.5 + -0.4) / 2 = 0.05
        assert position.x == pytest.approx(0.05, abs=0.001)

    def test_calculate_position_single_condition(self, calculator):
        """Test position calculation with single condition."""
        conditions = [
            {
                "icd_code": "E11",
                "vector_x": 0.7,
                "vector_y": -0.3,
                "vector_z": 0.5,
                "prevalence_total": 0.042,
            },
        ]
        position = calculator._calculate_position(conditions)

        # Position should equal the single condition's coordinates
        assert position.x == pytest.approx(0.7, abs=0.001)
        assert position.y == pytest.approx(-0.3, abs=0.001)
        assert position.z == pytest.approx(0.5, abs=0.001)

    def test_calculate_position_extreme_coordinates(self, calculator):
        """Test position calculation with extreme coordinate values outside [-1, 1]."""
        conditions = [
            {
                "icd_code": "E11",
                "vector_x": 5.0,  # Way outside [-1, 1]
                "vector_y": -3.0,  # Way outside [-1, 1]
                "vector_z": 2.5,  # Way outside [-1, 1]
                "prevalence_total": 1.0,
            },
        ]
        position = calculator._calculate_position(conditions)

        # Coordinates should be clamped to [-1, 1]
        assert position.x == 1.0
        assert position.y == -1.0
        assert position.z == 1.0

    def test_calculate_position_null_prevalence(self, calculator):
        """Test position calculation with None prevalence values."""
        conditions = [
            {
                "icd_code": "E11",
                "vector_x": 0.5,
                "vector_y": 0.5,
                "vector_z": 0.5,
                "prevalence_total": None,  # Null prevalence
            },
        ]
        position = calculator._calculate_position(conditions)

        # Should use default weight of 1.0
        assert position.x == pytest.approx(0.5, abs=0.001)
        assert position.y == pytest.approx(0.5, abs=0.001)
        assert position.z == pytest.approx(0.5, abs=0.001)

    @pytest.mark.asyncio
    async def test_apply_lifestyle_factors_metabolic_bmi(self, calculator):
        """Test BMI adjustments for metabolic diseases."""
        risks = {"E11": 0.5, "I10": 0.5}  # E=metabolic, I=cardiovascular

        # Test obese BMI
        request_obese = RiskCalculationRequest(
            age=35,  # young_adult - no age adjustment for metabolic
            gender="male",
            bmi=32.0,  # Obese
            existing_conditions=["E11"],
            exercise_level="moderate",
            smoking=False,
        )

        adjusted, factors = await calculator._apply_lifestyle_factors(
            risks, request_obese
        )

        # E11 (metabolic) should have 1.5x multiplier for obese BMI
        assert adjusted["E11"] == pytest.approx(0.5 * 1.5, rel=0.01)
        # I10 (cardiovascular) should not be affected by BMI
        assert adjusted["I10"] == pytest.approx(0.5, rel=0.01)
        assert any("obese" in f.lower() for f in factors["E11"])

    @pytest.mark.asyncio
    async def test_apply_lifestyle_factors_cardiovascular_smoking(self, calculator):
        """Test smoking adjustments for cardiovascular diseases."""
        risks = {"E11": 0.5, "I10": 0.5}

        request_smoker = RiskCalculationRequest(
            age=35,
            gender="male",
            bmi=22.0,  # Normal BMI
            existing_conditions=["E11"],
            exercise_level="moderate",
            smoking=True,
        )

        adjusted, factors = await calculator._apply_lifestyle_factors(
            risks, request_smoker
        )

        # I10 (cardiovascular) should have 1.8x multiplier for smoking
        assert adjusted["I10"] == pytest.approx(0.5 * 1.8, rel=0.01)
        # E11 (metabolic) should not be affected by smoking
        assert adjusted["E11"] == pytest.approx(0.5, rel=0.01)
        assert any("smoking" in f.lower() for f in factors["I10"])

    @pytest.mark.asyncio
    async def test_apply_lifestyle_factors_respiratory_smoking(self, calculator):
        """Test smoking adjustments for respiratory diseases."""
        risks = {"J45": 0.5}  # J=respiratory

        request_smoker = RiskCalculationRequest(
            age=35,
            gender="male",
            bmi=22.0,
            existing_conditions=["E11"],
            exercise_level="moderate",
            smoking=True,
        )

        adjusted, factors = await calculator._apply_lifestyle_factors(
            risks, request_smoker
        )

        # J45 (respiratory) should have 1.6x multiplier for smoking
        assert adjusted["J45"] == pytest.approx(0.5 * 1.6, rel=0.01)
        assert any("smoking" in f.lower() for f in factors["J45"])

    @pytest.mark.asyncio
    async def test_apply_lifestyle_factors_cardiovascular_exercise(self, calculator):
        """Test exercise adjustments for cardiovascular diseases."""
        risks = {"I10": 0.5}

        # Test low exercise (sedentary)
        request_sedentary = RiskCalculationRequest(
            age=35,
            gender="male",
            bmi=22.0,
            existing_conditions=["E11"],
            exercise_level="sedentary",
            smoking=False,
        )

        adjusted, factors = await calculator._apply_lifestyle_factors(
            risks, request_sedentary
        )
        assert adjusted["I10"] == pytest.approx(0.5 * 1.3, rel=0.01)

        # Test high exercise (active - protective)
        request_active = RiskCalculationRequest(
            age=35,
            gender="male",
            bmi=22.0,
            existing_conditions=["E11"],
            exercise_level="active",
            smoking=False,
        )

        adjusted, factors = await calculator._apply_lifestyle_factors(
            risks, request_active
        )
        assert adjusted["I10"] == pytest.approx(0.5 * 0.7, rel=0.01)
        assert any("active" in f.lower() for f in factors["I10"])

    @pytest.mark.asyncio
    async def test_apply_lifestyle_factors_age_adjustments(self, calculator):
        """Test age-based adjustments for different categories."""
        risks = {"E11": 0.5, "I10": 0.5, "J45": 0.5}

        # Test elderly age (65+)
        request_elderly = RiskCalculationRequest(
            age=70,
            gender="male",
            bmi=22.0,  # Normal BMI
            existing_conditions=["E11"],
            exercise_level="moderate",
            smoking=False,
        )

        adjusted, factors = await calculator._apply_lifestyle_factors(
            risks, request_elderly
        )

        # Elderly multipliers: metabolic=1.3, cardiovascular=1.5, respiratory=1.2
        assert adjusted["E11"] == pytest.approx(0.5 * 1.3, rel=0.01)
        assert adjusted["I10"] == pytest.approx(0.5 * 1.5, rel=0.01)
        assert adjusted["J45"] == pytest.approx(0.5 * 1.2, rel=0.01)

    @pytest.mark.asyncio
    async def test_apply_lifestyle_factors_young_protective(self, calculator):
        """Test that young age provides protective effect."""
        risks = {"I10": 0.5}  # Cardiovascular

        request_young = RiskCalculationRequest(
            age=25,  # Young
            gender="male",
            bmi=22.0,
            existing_conditions=["E11"],
            exercise_level="moderate",
            smoking=False,
        )

        adjusted, factors = await calculator._apply_lifestyle_factors(
            risks, request_young
        )

        # Young has 0.7 multiplier for cardiovascular (protective)
        assert adjusted["I10"] == pytest.approx(0.5 * 0.7, rel=0.01)
        assert any("lower" in f.lower() for f in factors["I10"])

    @pytest.mark.asyncio
    async def test_risk_cap_at_1(self, calculator):
        """Test that risk scores are capped at 1.0."""
        # Start with high base risk
        risks = {"I10": 0.8}

        # Apply multiple risk-increasing factors
        request = RiskCalculationRequest(
            age=70,  # Elderly: 1.5x for cardiovascular
            gender="male",
            bmi=22.0,
            existing_conditions=["E11"],
            exercise_level="sedentary",  # 1.3x for cardiovascular
            smoking=True,  # 1.8x for cardiovascular
        )

        # Combined: 0.8 * 1.5 * 1.3 * 1.8 = 2.808, should cap at 1.0
        adjusted, factors = await calculator._apply_lifestyle_factors(risks, request)
        assert adjusted["I10"] == 1.0

    @pytest.mark.asyncio
    async def test_calculate_risks_empty_conditions(self, calculator):
        """Test that empty conditions raises ValueError."""
        request = RiskCalculationRequest(
            age=45,
            gender="male",
            bmi=25.0,
            existing_conditions=["INVALID"],  # Non-existent code
            exercise_level="moderate",
            smoking=False,
        )

        # Mock _get_conditions to return empty
        calculator._get_conditions = AsyncMock(return_value=[])

        with pytest.raises(ValueError, match="No valid conditions found"):
            await calculator.calculate_risks(request)


class TestRiskCalculationResponse:
    """Test response model."""

    def test_response_creation(self):
        """Test creating a response object."""
        scores = [
            RiskScore(
                disease_id="E13",
                disease_name="Other diabetes",
                risk=0.75,
                level="high",
                contributing_factors=["High odds ratio"],
            ),
        ]

        response = RiskCalculationResponse(
            risk_scores=scores,
            user_position=UserPosition(x=0.5, y=-0.3, z=0.8),
            total_conditions_analyzed=2,
            analysis_metadata={"test": "data"},
        )

        assert len(response.risk_scores) == 1
        assert response.total_conditions_analyzed == 2
        assert response.user_position.x == 0.5


class TestUserPosition:
    """Test UserPosition model validation."""

    def test_valid_position(self):
        """Test creating a valid position within bounds."""
        position = UserPosition(x=0.5, y=-0.5, z=0.0)
        assert position.x == 0.5
        assert position.y == -0.5
        assert position.z == 0.0

    def test_boundary_values(self):
        """Test position at boundary values [-1, 1]."""
        # Test minimum boundaries
        position_min = UserPosition(x=-1.0, y=-1.0, z=-1.0)
        assert position_min.x == -1.0
        assert position_min.y == -1.0
        assert position_min.z == -1.0

        # Test maximum boundaries
        position_max = UserPosition(x=1.0, y=1.0, z=1.0)
        assert position_max.x == 1.0
        assert position_max.y == 1.0
        assert position_max.z == 1.0

    def test_out_of_bounds_x(self):
        """Test that x coordinate outside [-1, 1] is rejected."""
        with pytest.raises(ValueError):
            UserPosition(x=1.5, y=0.0, z=0.0)
        with pytest.raises(ValueError):
            UserPosition(x=-1.5, y=0.0, z=0.0)

    def test_out_of_bounds_y(self):
        """Test that y coordinate outside [-1, 1] is rejected."""
        with pytest.raises(ValueError):
            UserPosition(x=0.0, y=2.0, z=0.0)
        with pytest.raises(ValueError):
            UserPosition(x=0.0, y=-2.0, z=0.0)

    def test_out_of_bounds_z(self):
        """Test that z coordinate outside [-1, 1] is rejected."""
        with pytest.raises(ValueError):
            UserPosition(x=0.0, y=0.0, z=3.0)
        with pytest.raises(ValueError):
            UserPosition(x=0.0, y=0.0, z=-3.0)

    def test_origin_position(self):
        """Test origin position (0, 0, 0)."""
        position = UserPosition(x=0.0, y=0.0, z=0.0)
        assert position.x == 0.0
        assert position.y == 0.0
        assert position.z == 0.0


class TestDiseaseNameResolution:
    """Test disease name resolution from database."""

    @pytest.fixture
    def mock_client(self):
        """Create mock Supabase client."""
        return AsyncMock()

    @pytest.fixture
    def calculator(self, mock_client):
        """Create RiskCalculator instance with mock client."""
        return RiskCalculator(mock_client)

    @pytest.mark.asyncio
    async def test_get_disease_names_caching(self, calculator, mock_client):
        """Test that disease names are cached properly."""
        # Pre-populate cache
        calculator._disease_names_cache["E11"] = "Type 2 diabetes mellitus"
        calculator._disease_names_cache["I10"] = "Essential hypertension"

        # Should not make any database calls for cached codes
        names = await calculator._get_disease_names(["E11", "I10"])

        assert names["E11"] == "Type 2 diabetes mellitus"
        assert names["I10"] == "Essential hypertension"
        # No database calls should have been made
        mock_client.table.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_disease_names_fallback(self, calculator, mock_client):
        """Test fallback to ICD code when name not found."""
        # Mock empty response
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.table.return_value.select.return_value.in_.return_value.execute = (
            AsyncMock(return_value=mock_response)
        )

        names = await calculator._get_disease_names(["UNKNOWN"])

        # Should fall back to the ICD code itself
        assert names["UNKNOWN"] == "UNKNOWN"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
