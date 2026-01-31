"""
Tests for Database Index Verification

Unit tests for the index verification and benchmark scripts.
Uses mocks to avoid requiring actual database connections.
"""

import pytest
from dataclasses import dataclass
from typing import Optional
from unittest.mock import MagicMock, patch


# Import the modules we're testing
# Using importlib to avoid issues with relative imports
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestIndexStatus:
    """Tests for IndexStatus dataclass."""

    def test_index_status_exists(self):
        """Test IndexStatus with an existing index."""
        from verify_indexes import IndexStatus

        status = IndexStatus(
            name="idx_test",
            table="test_table",
            exists=True,
            definition="CREATE INDEX idx_test ON test_table(col);",
        )

        assert status.name == "idx_test"
        assert status.table == "test_table"
        assert status.exists is True
        assert status.definition is not None

    def test_index_status_missing(self):
        """Test IndexStatus with a missing index."""
        from verify_indexes import IndexStatus

        status = IndexStatus(
            name="idx_missing",
            table="test_table",
            exists=False,
        )

        assert status.name == "idx_missing"
        assert status.exists is False
        assert status.definition is None


class TestRequiredIndexes:
    """Tests for required index definitions."""

    def test_required_indexes_defined(self):
        """Test that required indexes are properly defined."""
        from verify_indexes import REQUIRED_INDEXES

        # Check main tables have indexes defined
        assert "diseases" in REQUIRED_INDEXES
        assert "disease_relationships" in REQUIRED_INDEXES
        assert "prevalence_stratified" in REQUIRED_INDEXES

    def test_diseases_indexes(self):
        """Test that diseases table has required indexes."""
        from verify_indexes import REQUIRED_INDEXES

        indexes = REQUIRED_INDEXES["diseases"]
        assert "idx_diseases_icd_code" in indexes
        assert "idx_diseases_chapter" in indexes
        assert "idx_diseases_granularity" in indexes

    def test_relationships_indexes(self):
        """Test that disease_relationships table has required indexes."""
        from verify_indexes import REQUIRED_INDEXES

        indexes = REQUIRED_INDEXES["disease_relationships"]
        assert "idx_rel_disease1" in indexes
        assert "idx_rel_disease2" in indexes
        assert "idx_rel_odds_ratio" in indexes
        # Composite index for relationship lookups
        assert "idx_rel_composite" in indexes

    def test_prevalence_indexes(self):
        """Test that prevalence_stratified table has required indexes."""
        from verify_indexes import REQUIRED_INDEXES

        indexes = REQUIRED_INDEXES["prevalence_stratified"]
        assert "idx_prev_disease" in indexes
        assert "idx_prev_sex" in indexes


class TestGetExistingIndexes:
    """Tests for get_existing_indexes function."""

    def test_get_existing_indexes(self):
        """Test fetching existing indexes from database."""
        from verify_indexes import get_existing_indexes

        # Mock cursor and connection
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("idx_test1", "CREATE INDEX idx_test1 ON table(col1);"),
            ("idx_test2", "CREATE INDEX idx_test2 ON table(col2);"),
        ]
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        result = get_existing_indexes(mock_conn, "test_table")

        assert "idx_test1" in result
        assert "idx_test2" in result
        assert len(result) == 2


class TestVerifyAllIndexes:
    """Tests for verify_all_indexes function."""

    @patch("verify_indexes.get_existing_indexes")
    def test_verify_all_indexes_all_exist(self, mock_get_existing):
        """Test verification when all indexes exist."""
        from verify_indexes import verify_all_indexes, REQUIRED_INDEXES

        # Mock all indexes as existing
        def mock_existing(conn, table_name):
            return {
                idx: f"CREATE INDEX {idx}..."
                for idx in REQUIRED_INDEXES.get(table_name, [])
            }

        mock_get_existing.side_effect = mock_existing

        mock_conn = MagicMock()
        results = verify_all_indexes(mock_conn, verbose=False)

        # All indexes should exist
        assert all(r.exists for r in results)

    @patch("verify_indexes.get_existing_indexes")
    def test_verify_all_indexes_some_missing(self, mock_get_existing):
        """Test verification when some indexes are missing."""
        from verify_indexes import verify_all_indexes, REQUIRED_INDEXES

        # Mock some indexes as missing
        def mock_existing(conn, table_name):
            if table_name == "diseases":
                return {"idx_diseases_icd_code": "CREATE INDEX..."}  # Only one exists
            return {}

        mock_get_existing.side_effect = mock_existing

        mock_conn = MagicMock()
        results = verify_all_indexes(mock_conn, verbose=False)

        # Some indexes should be missing
        missing = [r for r in results if not r.exists]
        assert len(missing) > 0


class TestBenchmarkResult:
    """Tests for BenchmarkResult dataclass."""

    def test_benchmark_result_success(self):
        """Test BenchmarkResult with successful benchmark."""
        from benchmark_queries import BenchmarkResult

        result = BenchmarkResult(
            name="Test Query",
            query="SELECT 1;",
            avg_time_ms=5.2,
            min_time_ms=4.1,
            max_time_ms=6.3,
            iterations=5,
            row_count=1,
        )

        assert result.name == "Test Query"
        assert result.avg_time_ms == 5.2
        assert result.error is None

    def test_benchmark_result_error(self):
        """Test BenchmarkResult with error."""
        from benchmark_queries import BenchmarkResult

        result = BenchmarkResult(
            name="Failed Query",
            query="SELECT * FROM nonexistent;",
            avg_time_ms=0,
            min_time_ms=0,
            max_time_ms=0,
            iterations=0,
            row_count=0,
            error="relation does not exist",
        )

        assert result.error is not None
        assert "does not exist" in result.error


class TestBenchmarkQueries:
    """Tests for benchmark query definitions."""

    def test_benchmark_queries_defined(self):
        """Test that benchmark queries are properly defined."""
        from benchmark_queries import BENCHMARK_QUERIES

        assert len(BENCHMARK_QUERIES) > 0

        for benchmark in BENCHMARK_QUERIES:
            assert "name" in benchmark
            assert "query" in benchmark
            assert "description" in benchmark

    def test_benchmark_queries_are_read_only(self):
        """Test that all benchmark queries are read-only (SELECT)."""
        from benchmark_queries import BENCHMARK_QUERIES

        for benchmark in BENCHMARK_QUERIES:
            query = benchmark["query"].strip().upper()
            # All queries should start with SELECT (read-only)
            assert query.startswith("SELECT"), (
                f"Query '{benchmark['name']}' is not read-only"
            )


class TestHealthCheckDatabase:
    """Tests for health check database connectivity."""

    @pytest.mark.asyncio
    async def test_check_database_connectivity_connected(self):
        """Test database connectivity check when connected."""
        # This would require mocking the Supabase async client
        # For now, we just verify the function exists
        from api.routes.health import _check_database_connectivity

        # The function should exist and be async
        assert callable(_check_database_connectivity)

    def test_health_response_model(self):
        """Test HealthResponse model structure."""
        from api.routes.health import HealthResponse

        response = HealthResponse(
            status="healthy",
            version="1.0.0",
            database="connected",
            timestamp="2026-01-30T12:00:00Z",
            uptime_seconds=3600.0,
        )

        assert response.status == "healthy"
        assert response.database == "connected"

    def test_health_check_result_model(self):
        """Test HealthCheckResult model structure."""
        from api.routes.health import HealthCheckResult

        result = HealthCheckResult(
            status="healthy",
            checks={
                "config": {"status": "ok"},
                "database": {"status": "ok", "message": "Connected"},
            },
        )

        assert result.status == "healthy"
        assert "database" in result.checks
        assert result.checks["database"]["status"] == "ok"
