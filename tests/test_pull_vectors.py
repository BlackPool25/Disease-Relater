"""
Unit Tests for Pull Vectors Calculation

Tests the pull vector calculation for directional vectors from user position
toward high-risk diseases, scaled by risk score.
"""

import math
import pytest
from unittest.mock import AsyncMock, MagicMock

from api.schemas.calculate import (
    PullVector,
    UserPosition,
)
from api.services.risk_calculator import RiskCalculator


class TestPullVectorSchema:
    """Test PullVector Pydantic model validation."""

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
        assert pv.disease_name == "Chronic kidney disease"
        assert pv.risk == 0.72
        assert pv.vector_x == 0.234
        assert pv.magnitude == 0.295

    def test_risk_bounds(self):
        """Test that risk must be between 0 and 1."""
        # Valid risk at boundaries
        pv_low = PullVector(
            disease_id="E11",
            disease_name="Diabetes",
            risk=0.0,
            vector_x=0.1,
            vector_y=0.1,
            vector_z=0.1,
            magnitude=0.1,
        )
        assert pv_low.risk == 0.0

        pv_high = PullVector(
            disease_id="E11",
            disease_name="Diabetes",
            risk=1.0,
            vector_x=0.1,
            vector_y=0.1,
            vector_z=0.1,
            magnitude=0.1,
        )
        assert pv_high.risk == 1.0

        # Invalid risk > 1
        with pytest.raises(ValueError):
            PullVector(
                disease_id="E11",
                disease_name="Diabetes",
                risk=1.5,
                vector_x=0.1,
                vector_y=0.1,
                vector_z=0.1,
                magnitude=0.1,
            )

    def test_magnitude_non_negative(self):
        """Test that magnitude must be non-negative."""
        # Valid zero magnitude
        pv = PullVector(
            disease_id="E11",
            disease_name="Diabetes",
            risk=0.5,
            vector_x=0.0,
            vector_y=0.0,
            vector_z=0.0,
            magnitude=0.0,
        )
        assert pv.magnitude == 0.0

        # Invalid negative magnitude
        with pytest.raises(ValueError):
            PullVector(
                disease_id="E11",
                disease_name="Diabetes",
                risk=0.5,
                vector_x=0.1,
                vector_y=0.1,
                vector_z=0.1,
                magnitude=-0.1,
            )


class TestGetDiseaseCoordinates:
    """Test _get_disease_coordinates helper method."""

    @pytest.fixture
    def mock_client(self):
        """Create mock Supabase client with proper async chain."""
        client = MagicMock()
        return client

    @pytest.fixture
    def calculator(self, mock_client):
        """Create RiskCalculator instance with mock client."""
        return RiskCalculator(mock_client)

    @pytest.mark.asyncio
    async def test_batch_fetch_coordinates(self, calculator, mock_client):
        """Test batch fetching of disease coordinates."""
        # Mock database response
        mock_response = MagicMock()
        mock_response.data = [
            {
                "icd_code": "E11",
                "name_english": "Type 2 diabetes",
                "vector_x": 0.5,
                "vector_y": -0.3,
                "vector_z": 0.2,
            },
            {
                "icd_code": "I10",
                "name_english": "Hypertension",
                "vector_x": -0.2,
                "vector_y": 0.4,
                "vector_z": 0.1,
            },
        ]

        # Set up the mock chain for async Supabase client
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_in = MagicMock()
        mock_in.execute = AsyncMock(return_value=mock_response)
        mock_select.in_ = MagicMock(return_value=mock_in)
        mock_table.select = MagicMock(return_value=mock_select)
        mock_client.table = MagicMock(return_value=mock_table)

        coords = await calculator._get_disease_coordinates(["E11", "I10"])

        assert len(coords) == 2
        assert coords["E11"]["x"] == 0.5
        assert coords["E11"]["y"] == -0.3
        assert coords["E11"]["z"] == 0.2
        assert coords["E11"]["name"] == "Type 2 diabetes"
        assert coords["I10"]["x"] == -0.2

    @pytest.mark.asyncio
    async def test_empty_codes_list(self, calculator, mock_client):
        """Test with empty ICD codes list."""
        coords = await calculator._get_disease_coordinates([])
        assert coords == {}

    @pytest.mark.asyncio
    async def test_missing_coordinates_default_to_zero(self, calculator, mock_client):
        """Test that missing coordinates default to 0.0."""
        mock_response = MagicMock()
        mock_response.data = [
            {
                "icd_code": "E11",
                "name_english": "Diabetes",
                "vector_x": None,
                "vector_y": None,
                "vector_z": None,
            },
        ]

        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_in = MagicMock()
        mock_in.execute = AsyncMock(return_value=mock_response)
        mock_select.in_ = MagicMock(return_value=mock_in)
        mock_table.select = MagicMock(return_value=mock_select)
        mock_client.table = MagicMock(return_value=mock_table)

        coords = await calculator._get_disease_coordinates(["E11"])

        assert coords["E11"]["x"] == 0.0
        assert coords["E11"]["y"] == 0.0
        assert coords["E11"]["z"] == 0.0


def _setup_mock_client(mock_client, response_data):
    """Helper to set up mock Supabase client with proper async chain."""
    mock_response = MagicMock()
    mock_response.data = response_data
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_in = MagicMock()
    mock_in.execute = AsyncMock(return_value=mock_response)
    mock_select.in_ = MagicMock(return_value=mock_in)
    mock_table.select = MagicMock(return_value=mock_select)
    mock_client.table = MagicMock(return_value=mock_table)


class TestCalculatePullVectors:
    """Test _calculate_pull_vectors method."""

    @pytest.fixture
    def mock_client(self):
        """Create mock Supabase client."""
        return MagicMock()

    @pytest.fixture
    def calculator(self, mock_client):
        """Create RiskCalculator instance with mock client."""
        return RiskCalculator(mock_client)

    @pytest.fixture
    def user_position(self):
        """Sample user position at origin."""
        return UserPosition(x=0.0, y=0.0, z=0.0)

    @pytest.mark.asyncio
    async def test_no_high_risk_diseases(self, calculator, mock_client):
        """Test with no diseases above threshold - returns empty list."""
        user_pos = UserPosition(x=0.0, y=0.0, z=0.0)
        risks = {"E11": 0.2, "I10": 0.1}  # All below 0.3 threshold

        pull_vectors = await calculator._calculate_pull_vectors(
            risks, user_pos, threshold=0.3
        )

        assert pull_vectors == []

    @pytest.mark.asyncio
    async def test_vector_math_correct(self, calculator, mock_client, user_position):
        """Test that vector calculation is mathematically correct."""
        # Disease at (0.5, 0.4, 0.3), user at origin, risk = 0.5
        _setup_mock_client(
            mock_client,
            [
                {
                    "icd_code": "E11",
                    "name_english": "Diabetes",
                    "vector_x": 0.5,
                    "vector_y": 0.4,
                    "vector_z": 0.3,
                },
            ],
        )

        risks = {"E11": 0.5}
        pull_vectors = await calculator._calculate_pull_vectors(
            risks, user_position, threshold=0.3
        )

        assert len(pull_vectors) == 1
        pv = pull_vectors[0]

        # Vector = (disease_pos - user_pos) * risk
        # = (0.5 - 0, 0.4 - 0, 0.3 - 0) * 0.5
        # = (0.25, 0.2, 0.15)
        assert pv.vector_x == pytest.approx(0.25, rel=0.01)
        assert pv.vector_y == pytest.approx(0.2, rel=0.01)
        assert pv.vector_z == pytest.approx(0.15, rel=0.01)

    @pytest.mark.asyncio
    async def test_magnitude_calculation(self, calculator, mock_client, user_position):
        """Test magnitude calculation: sqrt(x^2 + y^2 + z^2)."""
        # Use a 3-4-5 triangle scaled for easy verification
        # Vector (0.3, 0.4, 0.0) has magnitude 0.5
        _setup_mock_client(
            mock_client,
            [
                {
                    "icd_code": "E11",
                    "name_english": "Diabetes",
                    "vector_x": 0.6,  # After * 0.5 risk -> 0.3
                    "vector_y": 0.8,  # After * 0.5 risk -> 0.4
                    "vector_z": 0.0,
                },
            ],
        )

        risks = {"E11": 0.5}
        pull_vectors = await calculator._calculate_pull_vectors(
            risks, user_position, threshold=0.3
        )

        pv = pull_vectors[0]
        # magnitude = sqrt(0.3^2 + 0.4^2 + 0^2) = sqrt(0.09 + 0.16) = sqrt(0.25) = 0.5
        assert pv.magnitude == pytest.approx(0.5, rel=0.01)

    @pytest.mark.asyncio
    async def test_threshold_filtering(self, calculator, mock_client, user_position):
        """Test that only diseases above threshold are included."""
        _setup_mock_client(
            mock_client,
            [
                {
                    "icd_code": "E11",
                    "name_english": "Diabetes",
                    "vector_x": 0.5,
                    "vector_y": 0.5,
                    "vector_z": 0.5,
                },
            ],
        )

        risks = {
            "E11": 0.35,  # Above threshold
            "I10": 0.25,  # Below threshold
            "N18": 0.31,  # Just above threshold
        }

        pull_vectors = await calculator._calculate_pull_vectors(
            risks, user_position, threshold=0.3
        )

        # Only E11 should be fetched (mock only returns E11)
        # The mock is set up to return E11, so N18 won't be found
        included_ids = [pv.disease_id for pv in pull_vectors]
        assert "E11" in included_ids
        assert "I10" not in included_ids

    @pytest.mark.asyncio
    async def test_user_position_offset(self, calculator, mock_client):
        """Test vector calculation with non-origin user position."""
        user_pos = UserPosition(x=0.2, y=0.1, z=0.0)

        _setup_mock_client(
            mock_client,
            [
                {
                    "icd_code": "E11",
                    "name_english": "Diabetes",
                    "vector_x": 0.7,
                    "vector_y": 0.5,
                    "vector_z": 0.3,
                },
            ],
        )

        risks = {"E11": 1.0}  # risk = 1.0 for easy calculation
        pull_vectors = await calculator._calculate_pull_vectors(
            risks, user_pos, threshold=0.3
        )

        pv = pull_vectors[0]
        # Vector = (0.7 - 0.2, 0.5 - 0.1, 0.3 - 0.0) * 1.0
        # = (0.5, 0.4, 0.3)
        assert pv.vector_x == pytest.approx(0.5, rel=0.01)
        assert pv.vector_y == pytest.approx(0.4, rel=0.01)
        assert pv.vector_z == pytest.approx(0.3, rel=0.01)

    @pytest.mark.asyncio
    async def test_sorted_by_magnitude(self, calculator, mock_client, user_position):
        """Test that pull vectors are sorted by magnitude descending."""
        _setup_mock_client(
            mock_client,
            [
                {
                    "icd_code": "E11",
                    "name_english": "Diabetes",
                    "vector_x": 0.1,
                    "vector_y": 0.1,
                    "vector_z": 0.1,
                },
                {
                    "icd_code": "I10",
                    "name_english": "Hypertension",
                    "vector_x": 0.5,
                    "vector_y": 0.5,
                    "vector_z": 0.5,
                },
            ],
        )

        # Same risk, different positions -> different magnitudes
        risks = {"E11": 0.5, "I10": 0.5}
        pull_vectors = await calculator._calculate_pull_vectors(
            risks, user_position, threshold=0.3
        )

        # I10 (farther from origin) should have higher magnitude and come first
        assert len(pull_vectors) == 2
        assert pull_vectors[0].magnitude >= pull_vectors[1].magnitude

    @pytest.mark.asyncio
    async def test_zero_magnitude_at_same_position(
        self, calculator, mock_client, user_position
    ):
        """Test that magnitude is zero when disease is at user position."""
        _setup_mock_client(
            mock_client,
            [
                {
                    "icd_code": "E11",
                    "name_english": "Diabetes",
                    "vector_x": 0.0,  # Same as user position
                    "vector_y": 0.0,
                    "vector_z": 0.0,
                },
            ],
        )

        risks = {"E11": 0.5}
        pull_vectors = await calculator._calculate_pull_vectors(
            risks, user_position, threshold=0.3
        )

        pv = pull_vectors[0]
        assert pv.magnitude == 0.0
        assert pv.vector_x == 0.0
        assert pv.vector_y == 0.0
        assert pv.vector_z == 0.0


class TestPullVectorsIntegration:
    """Integration tests for pull vectors in full response."""

    @pytest.fixture
    def mock_client(self):
        """Create mock Supabase client."""
        return AsyncMock()

    @pytest.fixture
    def calculator(self, mock_client):
        """Create RiskCalculator instance with mock client."""
        return RiskCalculator(mock_client)

    def test_pull_vector_magnitude_formula(self):
        """Verify magnitude formula with known values."""
        # 3-4-5 right triangle
        x, y, z = 3.0, 4.0, 0.0
        expected_magnitude = 5.0
        actual_magnitude = math.sqrt(x**2 + y**2 + z**2)
        assert actual_magnitude == expected_magnitude

        # 3D pythagorean
        x, y, z = 1.0, 2.0, 2.0
        expected_magnitude = 3.0
        actual_magnitude = math.sqrt(x**2 + y**2 + z**2)
        assert actual_magnitude == expected_magnitude


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
