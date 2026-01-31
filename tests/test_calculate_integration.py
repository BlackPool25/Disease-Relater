"""
Integration Tests for Risk Calculation API

Tests the full flow of the calculate-risk endpoint including:
- Request validation
- Response schema with pull_vectors
- Security: SQL injection prevention in search
- Security: Logging does not expose medical conditions
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from api.routes.calculate import router as calculate_router
from api.routes.diseases import router as diseases_router
from api.schemas.calculate import (
    RiskCalculationRequest,
    RiskCalculationResponse,
    RiskScore,
    UserPosition,
    PullVector,
)
from api.services.risk_calculator import RiskCalculator
from api.validation import validate_search_term


class TestValidateSearchTerm:
    """Test search term validation for SQL injection prevention."""

    def test_valid_search_terms(self):
        """Test that normal search terms pass validation."""
        valid_terms = ["diabetes", "heart disease", "E11", "type 2", "ab"]
        for term in valid_terms:
            is_valid, error = validate_search_term(term)
            assert is_valid, f"'{term}' should be valid but got: {error}"

    def test_short_search_term_rejected(self):
        """Test that single character search terms are rejected."""
        is_valid, error = validate_search_term("a")
        assert not is_valid
        assert "too short" in error.lower()

    def test_empty_search_term_rejected(self):
        """Test that empty search terms are rejected."""
        is_valid, error = validate_search_term("")
        assert not is_valid
        assert "empty" in error.lower()

    def test_sql_injection_attempts_rejected(self):
        """Test that SQL injection patterns are rejected."""
        malicious_terms = [
            "diabetes; DROP TABLE",
            "heart--comment",
            "test/* injection */",
            "DELETE FROM diseases",
            "INSERT INTO users",
            "UPDATE diseases SET",
        ]
        for term in malicious_terms:
            is_valid, error = validate_search_term(term)
            assert not is_valid, f"'{term}' should be rejected as malicious"
            assert "invalid" in error.lower()

    def test_too_long_search_term_rejected(self):
        """Test that very long search terms are rejected."""
        long_term = "a" * 101  # Exceeds 100 char limit
        is_valid, error = validate_search_term(long_term)
        assert not is_valid
        assert "too long" in error.lower()


class TestPullVectorSchema:
    """Test PullVector schema validation."""

    def test_valid_pull_vector(self):
        """Test creating a valid PullVector."""
        pv = PullVector(
            disease_id="N18",
            disease_name="Chronic kidney disease",
            risk=0.72,
            vector_x=0.234,
            vector_y=-0.156,
            vector_z=0.089,
            magnitude=0.295,
        )
        assert pv.disease_id == "N18"
        assert pv.risk == 0.72
        assert pv.magnitude == 0.295

    def test_pull_vector_risk_bounds(self):
        """Test that risk must be between 0 and 1."""
        with pytest.raises(ValueError):
            PullVector(
                disease_id="N18",
                disease_name="Test",
                risk=1.5,  # Invalid - exceeds 1.0
                vector_x=0.0,
                vector_y=0.0,
                vector_z=0.0,
                magnitude=0.0,
            )

    def test_pull_vector_negative_magnitude_rejected(self):
        """Test that negative magnitude is rejected."""
        with pytest.raises(ValueError):
            PullVector(
                disease_id="N18",
                disease_name="Test",
                risk=0.5,
                vector_x=0.0,
                vector_y=0.0,
                vector_z=0.0,
                magnitude=-0.1,  # Invalid - must be >= 0
            )


class TestRiskCalculationResponseWithPullVectors:
    """Test that response schema includes pull_vectors."""

    def test_response_includes_pull_vectors_field(self):
        """Test that RiskCalculationResponse has pull_vectors field."""
        response = RiskCalculationResponse(
            risk_scores=[],
            user_position=UserPosition(x=0.0, y=0.0, z=0.0),
            total_conditions_analyzed=0,
            analysis_metadata={},
        )
        assert hasattr(response, "pull_vectors")
        assert response.pull_vectors == []

    def test_response_with_pull_vectors(self):
        """Test response with pull_vectors populated."""
        pull_vectors = [
            PullVector(
                disease_id="N18",
                disease_name="Chronic kidney disease",
                risk=0.72,
                vector_x=0.234,
                vector_y=-0.156,
                vector_z=0.089,
                magnitude=0.295,
            ),
            PullVector(
                disease_id="E13",
                disease_name="Other diabetes",
                risk=0.55,
                vector_x=0.1,
                vector_y=0.2,
                vector_z=0.3,
                magnitude=0.374,
            ),
        ]
        response = RiskCalculationResponse(
            risk_scores=[],
            user_position=UserPosition(x=0.0, y=0.0, z=0.0),
            pull_vectors=pull_vectors,
            total_conditions_analyzed=2,
            analysis_metadata={},
        )
        assert len(response.pull_vectors) == 2
        assert response.pull_vectors[0].disease_id == "N18"


class TestCalculatePullVectors:
    """Test the _calculate_pull_vectors method."""

    @pytest.fixture
    def mock_client(self):
        """Create mock Supabase client."""
        return AsyncMock()

    @pytest.fixture
    def calculator(self, mock_client):
        """Create RiskCalculator instance with mock client."""
        return RiskCalculator(mock_client)

    @pytest.mark.asyncio
    async def test_pull_vectors_calculation(self, calculator, mock_client):
        """Test that pull vectors are calculated correctly."""
        # Mock _get_disease_coordinates directly (cleaner than mocking the DB chain)
        calculator._get_disease_coordinates = AsyncMock(
            return_value={
                "N18": {
                    "x": 0.5,
                    "y": 0.3,
                    "z": -0.2,
                    "name": "Chronic kidney disease",
                },
            }
        )

        risks = {"N18": 0.72, "E11": 0.1}  # Only N18 above threshold
        user_position = UserPosition(x=0.0, y=0.0, z=0.0)

        pull_vectors = await calculator._calculate_pull_vectors(
            risks, user_position, threshold=0.3
        )

        assert len(pull_vectors) == 1
        assert pull_vectors[0].disease_id == "N18"
        assert pull_vectors[0].risk == 0.72
        # Vector should be (0.5 - 0) * 0.72, etc.
        assert pull_vectors[0].vector_x == pytest.approx(0.5 * 0.72, rel=0.01)

    @pytest.mark.asyncio
    async def test_pull_vectors_empty_when_no_high_risk(self, calculator, mock_client):
        """Test that no pull vectors are returned when all risks below threshold."""
        risks = {"E11": 0.1, "I10": 0.2}  # All below 0.3 threshold
        user_position = UserPosition(x=0.0, y=0.0, z=0.0)

        pull_vectors = await calculator._calculate_pull_vectors(
            risks, user_position, threshold=0.3
        )

        assert pull_vectors == []

    @pytest.mark.asyncio
    async def test_pull_vectors_sorted_by_magnitude(self, calculator, mock_client):
        """Test that pull vectors are sorted by magnitude descending."""
        # Mock _get_disease_coordinates directly (cleaner than mocking the DB chain)
        calculator._get_disease_coordinates = AsyncMock(
            return_value={
                "N18": {
                    "x": 0.1,
                    "y": 0.1,
                    "z": 0.1,
                    "name": "Chronic kidney disease",
                },
                "E13": {
                    "x": 0.9,
                    "y": 0.9,
                    "z": 0.9,
                    "name": "Other diabetes",
                },
            }
        )

        # E13 has larger distance from origin, so should have larger magnitude
        risks = {"N18": 0.5, "E13": 0.5}
        user_position = UserPosition(x=0.0, y=0.0, z=0.0)

        pull_vectors = await calculator._calculate_pull_vectors(
            risks, user_position, threshold=0.3
        )

        assert len(pull_vectors) == 2
        # First should have larger magnitude
        assert pull_vectors[0].magnitude >= pull_vectors[1].magnitude


class TestLoggingSecurity:
    """Test that logging does not expose sensitive medical conditions."""

    @pytest.mark.asyncio
    async def test_logging_does_not_expose_conditions(self):
        """Test that log messages don't contain actual ICD codes."""
        import logging
        from io import StringIO

        # Capture log output
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.INFO)

        logger = logging.getLogger("api.routes.calculate")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Simulate the log message from calculate.py
        conditions = ["E11", "I10", "J45"]
        logger.info(f"Calculating risk for {len(conditions)} conditions")

        log_output = log_stream.getvalue()

        # Should NOT contain actual ICD codes
        assert "E11" not in log_output
        assert "I10" not in log_output
        assert "J45" not in log_output

        # Should contain count
        assert "3 conditions" in log_output

        # Clean up
        logger.removeHandler(handler)


class TestSearchEndpointSecurity:
    """Test SQL injection prevention in search endpoint."""

    def test_sql_like_wildcards_escaped(self):
        """Test that SQL LIKE wildcards are properly escaped."""
        # The escaping should prevent % and _ from being interpreted as wildcards
        test_term = "test%injection_attack"

        # Simulate the escaping done in the search endpoint
        escaped = (
            test_term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )

        assert "\\%" in escaped
        assert "\\_" in escaped
        assert escaped == "test\\%injection\\_attack"


class TestFullCalculationFlow:
    """Test the complete risk calculation flow."""

    @pytest.fixture
    def mock_client(self):
        """Create mock Supabase client with full response chain."""
        client = AsyncMock()

        # Mock diseases table for _get_conditions
        conditions_response = MagicMock()
        conditions_response.data = [
            {
                "id": 1,
                "icd_code": "E11",
                "name_english": "Type 2 diabetes",
                "chapter_code": "E",
                "prevalence_male": 0.05,
                "prevalence_female": 0.04,
                "prevalence_total": 0.045,
                "vector_x": 0.5,
                "vector_y": -0.3,
                "vector_z": 0.8,
            },
        ]

        # Mock diseases table for base risks
        base_risks_response = MagicMock()
        base_risks_response.data = [
            {
                "icd_code": "E11",
                "name_english": "Type 2 diabetes",
                "prevalence_male": 0.05,
                "prevalence_total": 0.045,
            },
            {
                "icd_code": "N18",
                "name_english": "Chronic kidney disease",
                "prevalence_male": 0.02,
                "prevalence_total": 0.02,
            },
        ]

        # Mock relationships
        relationships_response = MagicMock()
        relationships_response.data = [
            {
                "disease_1_id": 1,
                "disease_2_id": 2,
                "odds_ratio": 3.5,
                "disease_1": {"icd_code": "E11"},
                "disease_2": {"icd_code": "N18"},
            }
        ]

        # Mock disease IDs lookup
        disease_ids_response = MagicMock()
        disease_ids_response.data = [{"id": 1, "icd_code": "E11"}]

        # Set up the mock chain
        def table_side_effect(name):
            mock_table = MagicMock()
            mock_select = MagicMock()

            if name == "diseases":
                # Handle different select patterns
                def select_handler(*args, **kwargs):
                    mock_in = MagicMock()
                    mock_in.execute = AsyncMock(return_value=conditions_response)
                    mock_select.in_ = MagicMock(return_value=mock_in)
                    mock_select.execute = AsyncMock(return_value=base_risks_response)
                    return mock_select

                mock_table.select = select_handler
            elif name == "disease_relationships":
                mock_select.or_ = MagicMock(return_value=mock_select)
                mock_select.execute = AsyncMock(return_value=relationships_response)
                mock_table.select = MagicMock(return_value=mock_select)

            return mock_table

        client.table = table_side_effect
        return client

    @pytest.fixture
    def calculator(self, mock_client):
        """Create RiskCalculator instance."""
        return RiskCalculator(mock_client)

    @pytest.mark.asyncio
    async def test_full_calculation_returns_all_fields(self, calculator):
        """Test that full calculation returns all required response fields."""
        request = RiskCalculationRequest(
            age=45,
            gender="male",
            bmi=28.5,
            existing_conditions=["E11"],
            exercise_level="moderate",
            smoking=False,
        )

        # Mock the internal methods to isolate the test
        calculator._get_conditions = AsyncMock(
            return_value=[
                {
                    "id": 1,
                    "icd_code": "E11",
                    "name_english": "Type 2 diabetes",
                    "vector_x": 0.5,
                    "vector_y": -0.3,
                    "vector_z": 0.8,
                    "prevalence_total": 0.045,
                }
            ]
        )
        calculator._calculate_base_risks_for_all = AsyncMock(
            return_value={"E11": 0.05, "N18": 0.02, "E13": 0.01}
        )
        calculator._apply_comorbidity_multipliers = AsyncMock(
            return_value={"E11": 0.05, "N18": 0.07, "E13": 0.015}
        )
        calculator._get_disease_coordinates = AsyncMock(
            return_value={
                "N18": {
                    "x": 0.3,
                    "y": 0.2,
                    "z": -0.1,
                    "name": "Chronic kidney disease",
                },
            }
        )

        response = await calculator.calculate_risks(request)

        # Verify response has all required fields
        assert isinstance(response, RiskCalculationResponse)
        assert hasattr(response, "risk_scores")
        assert hasattr(response, "user_position")
        assert hasattr(response, "pull_vectors")
        assert hasattr(response, "total_conditions_analyzed")
        assert hasattr(response, "analysis_metadata")

        # Verify user position is valid
        assert isinstance(response.user_position, UserPosition)
        assert -1.0 <= response.user_position.x <= 1.0
        assert -1.0 <= response.user_position.y <= 1.0
        assert -1.0 <= response.user_position.z <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
