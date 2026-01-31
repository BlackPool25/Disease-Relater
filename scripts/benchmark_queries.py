#!/usr/bin/env python3
"""
Query Benchmark Script for Disease-Relater

Measures query performance for common database operations.
Used to verify that indexes are improving query times.

Usage:
    python scripts/benchmark_queries.py
    python scripts/benchmark_queries.py --iterations 10
    python scripts/benchmark_queries.py --verbose
"""

import argparse
import logging
import os
import sys
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of a single query benchmark."""

    name: str
    query: str
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    iterations: int
    row_count: int
    error: Optional[str] = None


def get_database_connection():
    """Establish database connection using environment variables."""
    try:
        import psycopg2
    except ImportError:
        logger.error(
            "psycopg2 not installed. Install with: uv pip install psycopg2-binary"
        )
        sys.exit(1)

    db_url = os.getenv("SUPABASE_URL", "")
    db_password = os.getenv("DB_PASSWORD", "")
    db_key = os.getenv("SUPABASE_KEY", "")

    if not db_url:
        logger.error("SUPABASE_URL environment variable not set")
        sys.exit(1)

    try:
        parsed = urlparse(db_url)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path.lstrip("/") if parsed.path else "postgres",
            user=parsed.username or "postgres",
            password=parsed.password or db_password or db_key,
        )
        logger.info(f"Connected to database: {parsed.hostname}")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        sys.exit(1)


# Benchmark queries - read-only queries for common operations
BENCHMARK_QUERIES = [
    {
        "name": "Disease list (first 100)",
        "query": "SELECT * FROM diseases LIMIT 100;",
        "description": "Fetches first 100 diseases",
    },
    {
        "name": "Disease by ICD code",
        "query": "SELECT * FROM diseases WHERE icd_code = 'E11';",
        "description": "Lookup by primary search column",
    },
    {
        "name": "Diseases by chapter",
        "query": "SELECT * FROM diseases WHERE chapter_code = 'IX' LIMIT 50;",
        "description": "Filter by chapter code",
    },
    {
        "name": "Relationships by disease_1_id",
        "query": """
            SELECT * FROM disease_relationships 
            WHERE disease_1_id = (SELECT id FROM diseases WHERE icd_code = 'E11' LIMIT 1)
            LIMIT 20;
        """,
        "description": "Get relationships for a disease",
    },
    {
        "name": "Relationships by both IDs (composite index)",
        "query": """
            SELECT * FROM disease_relationships 
            WHERE disease_1_id = (SELECT id FROM diseases WHERE icd_code = 'E11' LIMIT 1)
            AND disease_2_id = (SELECT id FROM diseases WHERE icd_code = 'I10' LIMIT 1);
        """,
        "description": "Lookup specific relationship pair",
    },
    {
        "name": "Top relationships by odds ratio",
        "query": """
            SELECT * FROM disease_relationships 
            ORDER BY odds_ratio_avg DESC NULLS LAST
            LIMIT 20;
        """,
        "description": "Find strongest relationships",
    },
    {
        "name": "Network data query",
        "query": """
            SELECT 
                d1.icd_code as disease_1_code,
                d2.icd_code as disease_2_code,
                r.odds_ratio_avg
            FROM disease_relationships r
            JOIN diseases d1 ON r.disease_1_id = d1.id
            JOIN diseases d2 ON r.disease_2_id = d2.id
            WHERE r.odds_ratio_avg > 5.0
            LIMIT 100;
        """,
        "description": "Network visualization query",
    },
    {
        "name": "Disease search (text)",
        "query": """
            SELECT * FROM diseases 
            WHERE name_english ILIKE '%diabetes%'
            LIMIT 10;
        """,
        "description": "Text search on disease name",
    },
]


def run_benchmark(
    conn, query: str, iterations: int = 5, warmup: int = 1
) -> BenchmarkResult:
    """Run a benchmark for a single query.

    Args:
        conn: Database connection
        query: SQL query to benchmark
        iterations: Number of iterations to run
        warmup: Number of warmup runs (not counted)

    Returns:
        BenchmarkResult with timing information
    """
    times = []
    row_count = 0
    error = None

    try:
        with conn.cursor() as cursor:
            # Warmup runs
            for _ in range(warmup):
                cursor.execute(query)
                cursor.fetchall()

            # Timed runs
            for _ in range(iterations):
                start = time.perf_counter()
                cursor.execute(query)
                rows = cursor.fetchall()
                end = time.perf_counter()

                times.append((end - start) * 1000)  # Convert to milliseconds
                row_count = len(rows)

    except Exception as e:
        error = str(e)
        logger.warning(f"Query failed: {e}")

    if times:
        return BenchmarkResult(
            name="",
            query=query,
            avg_time_ms=sum(times) / len(times),
            min_time_ms=min(times),
            max_time_ms=max(times),
            iterations=len(times),
            row_count=row_count,
            error=error,
        )
    else:
        return BenchmarkResult(
            name="",
            query=query,
            avg_time_ms=0,
            min_time_ms=0,
            max_time_ms=0,
            iterations=0,
            row_count=0,
            error=error,
        )


def run_all_benchmarks(
    conn, iterations: int = 5, verbose: bool = False
) -> list[BenchmarkResult]:
    """Run all benchmark queries.

    Args:
        conn: Database connection
        iterations: Number of iterations per query
        verbose: Show detailed output

    Returns:
        List of BenchmarkResult objects
    """
    results = []

    for benchmark in BENCHMARK_QUERIES:
        logger.info(f"Running: {benchmark['name']}")

        result = run_benchmark(conn, benchmark["query"], iterations)
        result.name = benchmark["name"]

        results.append(result)

        if verbose:
            if result.error:
                logger.info(f"  ✗ Error: {result.error}")
            else:
                logger.info(
                    f"  ✓ Avg: {result.avg_time_ms:.2f}ms, Rows: {result.row_count}"
                )

    return results


def print_results_table(results: list[BenchmarkResult]):
    """Print benchmark results as a formatted table."""
    print("\n" + "=" * 80)
    print("QUERY BENCHMARK RESULTS")
    print("=" * 80)
    print(
        f"{'Query':<40} {'Avg (ms)':<12} {'Min (ms)':<12} {'Max (ms)':<12} {'Rows':<8}"
    )
    print("-" * 80)

    for result in results:
        if result.error:
            print(f"{result.name:<40} {'ERROR':<12} {'-':<12} {'-':<12} {'-':<8}")
        else:
            print(
                f"{result.name:<40} "
                f"{result.avg_time_ms:<12.2f} "
                f"{result.min_time_ms:<12.2f} "
                f"{result.max_time_ms:<12.2f} "
                f"{result.row_count:<8}"
            )

    print("=" * 80)

    # Summary statistics
    successful = [r for r in results if not r.error]
    if successful:
        avg_total = sum(r.avg_time_ms for r in successful) / len(successful)
        print(f"\nOverall average query time: {avg_total:.2f}ms")
        print(f"Queries benchmarked: {len(successful)}/{len(results)}")

    # Performance notes
    print("\nPerformance Notes:")
    slow_queries = [r for r in successful if r.avg_time_ms > 100]
    if slow_queries:
        print("  ⚠ Slow queries (>100ms):")
        for r in slow_queries:
            print(f"    - {r.name}: {r.avg_time_ms:.2f}ms")
    else:
        print("  ✓ All queries performing within acceptable limits (<100ms)")


def main():
    """Main entry point for benchmark script."""
    parser = argparse.ArgumentParser(
        description="Benchmark database queries for Disease-Relater"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Number of iterations per query (default: 5)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Connect to database
    conn = get_database_connection()

    try:
        # Run benchmarks
        logger.info(f"Running benchmarks with {args.iterations} iterations each...")
        results = run_all_benchmarks(conn, args.iterations, args.verbose)

        # Print results
        print_results_table(results)

    finally:
        conn.close()
        logger.info("Database connection closed")


if __name__ == "__main__":
    main()
