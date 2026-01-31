#!/usr/bin/env python3
"""
Index Verification Script for Disease-Relater

Verifies that all required database indexes exist and reports their status.
Can optionally run EXPLAIN ANALYZE on common queries to verify index usage.

Usage:
    python scripts/verify_indexes.py
    python scripts/verify_indexes.py --analyze
    python scripts/verify_indexes.py --verbose
"""

import argparse
import logging
import os
import sys
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Required indexes for the Disease-Relater database
REQUIRED_INDEXES = {
    "diseases": [
        "idx_diseases_icd_code",
        "idx_diseases_chapter",
        "idx_diseases_granularity",
    ],
    "disease_relationships": [
        "idx_rel_disease1",
        "idx_rel_disease2",
        "idx_rel_odds_ratio",
        "idx_rel_composite",  # Composite index on (disease_1_id, disease_2_id)
    ],
    "prevalence_stratified": [
        "idx_prev_disease",
        "idx_prev_sex",
    ],
}


@dataclass
class IndexStatus:
    """Status of a database index."""

    name: str
    table: str
    exists: bool
    definition: Optional[str] = None
    size_bytes: Optional[int] = None


def get_database_connection():
    """Establish database connection using environment variables.

    Environment Variables:
        SUPABASE_DB_URL: Direct PostgreSQL connection URL (preferred)
                         Format: postgresql://user:password@host:port/database
        SUPABASE_URL: Supabase project URL (used to construct DB URL if SUPABASE_DB_URL not set)
        DB_PASSWORD: Database password (required if not in connection URL)

    Note: SUPABASE_KEY is the API key for the Supabase REST API and should NOT
    be used as a database password. Use DB_PASSWORD for direct PostgreSQL connections.
    """
    try:
        import psycopg2
    except ImportError:
        logger.error(
            "psycopg2 not installed. Install with: uv pip install psycopg2-binary"
        )
        sys.exit(1)

    # Prefer direct PostgreSQL URL if available
    db_url = os.getenv("SUPABASE_DB_URL", "") or os.getenv("SUPABASE_URL", "")
    db_password = os.getenv("DB_PASSWORD", "")

    if not db_url:
        logger.error(
            "Database URL not set. Set SUPABASE_DB_URL or SUPABASE_URL environment variable.\n"
            "Format: postgresql://user:password@host:port/database"
        )
        sys.exit(1)

    try:
        parsed = urlparse(db_url)

        # Check if this is a Supabase API URL (not a PostgreSQL URL)
        if parsed.scheme == "https" and "supabase.co" in (parsed.hostname or ""):
            # Construct PostgreSQL URL from Supabase project URL
            # Supabase DB host format: db.<project-ref>.supabase.co
            project_ref = (parsed.hostname or "").replace(".supabase.co", "")
            db_host = f"db.{project_ref}.supabase.co"
            logger.info(
                f"Detected Supabase API URL, constructing DB URL for: {db_host}"
            )

            if not db_password:
                logger.error(
                    "DB_PASSWORD required when using Supabase API URL.\n"
                    "Set DB_PASSWORD environment variable with your Supabase database password.\n"
                    "Note: SUPABASE_KEY (API key) is NOT the database password."
                )
                sys.exit(1)

            conn = psycopg2.connect(
                host=db_host,
                port=5432,
                database="postgres",
                user="postgres",
                password=db_password,
            )
        else:
            # Direct PostgreSQL URL
            if not parsed.password and not db_password:
                logger.error(
                    "Database password required. Either:\n"
                    "  1. Include password in URL: postgresql://user:password@host:port/db\n"
                    "  2. Set DB_PASSWORD environment variable"
                )
                sys.exit(1)

            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path.lstrip("/") if parsed.path else "postgres",
                user=parsed.username or "postgres",
                password=parsed.password or db_password,
            )

        logger.info(f"Connected to database: {parsed.hostname or 'supabase'}")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        sys.exit(1)


def get_existing_indexes(conn, table_name: str) -> dict[str, str]:
    """Get all indexes for a given table.

    Args:
        conn: Database connection
        table_name: Name of the table to check

    Returns:
        Dictionary mapping index name to index definition
    """
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = %s;
            """,
            (table_name,),
        )
        return {row[0]: row[1] for row in cursor.fetchall()}


def verify_all_indexes(conn, verbose: bool = False) -> list[IndexStatus]:
    """Verify all required indexes exist.

    Args:
        conn: Database connection
        verbose: Whether to print detailed information

    Returns:
        List of IndexStatus objects for all required indexes
    """
    results = []

    for table_name, required_indexes in REQUIRED_INDEXES.items():
        existing = get_existing_indexes(conn, table_name)

        if verbose:
            logger.info(f"\nChecking table: {table_name}")
            logger.info(f"  Found {len(existing)} indexes")

        for index_name in required_indexes:
            exists = index_name in existing
            definition = existing.get(index_name)

            status = IndexStatus(
                name=index_name,
                table=table_name,
                exists=exists,
                definition=definition,
            )
            results.append(status)

            if verbose:
                status_str = "✓" if exists else "✗"
                logger.info(f"  {status_str} {index_name}")

    return results


def run_explain_analyze(conn, verbose: bool = False) -> list[dict]:
    """Run EXPLAIN ANALYZE on common queries to verify index usage.

    Args:
        conn: Database connection
        verbose: Whether to print detailed query plans

    Returns:
        List of query analysis results
    """
    # Common queries that should use indexes
    test_queries = [
        {
            "name": "Disease lookup by ICD code",
            "query": "SELECT * FROM diseases WHERE icd_code = 'E11';",
            "expected_index": "idx_diseases_icd_code",
        },
        {
            "name": "Diseases by chapter",
            "query": "SELECT * FROM diseases WHERE chapter_code = 'IX';",
            "expected_index": "idx_diseases_chapter",
        },
        {
            "name": "Relationship lookup by disease_1_id",
            "query": """
                SELECT * FROM disease_relationships 
                WHERE disease_1_id = 1 LIMIT 10;
            """,
            "expected_index": "idx_rel_disease1",
        },
        {
            "name": "Relationship lookup by both IDs (composite)",
            "query": """
                SELECT * FROM disease_relationships 
                WHERE disease_1_id = 1 AND disease_2_id = 2;
            """,
            "expected_index": "idx_rel_composite",
        },
        {
            "name": "Relationships ordered by odds ratio",
            "query": """
                SELECT * FROM disease_relationships 
                ORDER BY odds_ratio_avg DESC LIMIT 20;
            """,
            "expected_index": "idx_rel_odds_ratio",
        },
    ]

    results = []

    for test in test_queries:
        try:
            with conn.cursor() as cursor:
                cursor.execute(f"EXPLAIN ANALYZE {test['query']}")
                plan = cursor.fetchall()
                plan_text = "\n".join(row[0] for row in plan)

                # Check if any index is being used
                uses_index = "Index" in plan_text
                uses_expected = test["expected_index"] in plan_text

                result = {
                    "name": test["name"],
                    "uses_index": uses_index,
                    "uses_expected_index": uses_expected,
                    "expected_index": test["expected_index"],
                    "plan": plan_text if verbose else None,
                }
                results.append(result)

                status = "✓" if uses_index else "✗"
                logger.info(f"  {status} {test['name']}")

                if verbose:
                    logger.info(f"    Plan:\n{plan_text}")

        except Exception as e:
            logger.warning(f"  ⚠ {test['name']}: {e}")
            results.append(
                {
                    "name": test["name"],
                    "error": str(e),
                }
            )

    return results


def print_summary(
    index_results: list[IndexStatus], analyze_results: Optional[list[dict]] = None
):
    """Print a summary of verification results."""
    print("\n" + "=" * 60)
    print("INDEX VERIFICATION SUMMARY")
    print("=" * 60)

    # Index existence summary
    total = len(index_results)
    existing = sum(1 for r in index_results if r.exists)
    missing = total - existing

    print(f"\nIndexes: {existing}/{total} exist")

    if missing > 0:
        print("\nMissing indexes:")
        for result in index_results:
            if not result.exists:
                print(f"  - {result.table}.{result.name}")

    # Query analysis summary
    if analyze_results:
        print("\nQuery Analysis:")
        using_index = sum(1 for r in analyze_results if r.get("uses_index", False))
        print(f"  Queries using indexes: {using_index}/{len(analyze_results)}")

    print("=" * 60)

    # Return exit code
    return 0 if missing == 0 else 1


def main():
    """Main entry point for index verification."""
    parser = argparse.ArgumentParser(
        description="Verify database indexes for Disease-Relater"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Run EXPLAIN ANALYZE on test queries",
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
        # Verify indexes exist
        logger.info("Verifying required indexes...")
        index_results = verify_all_indexes(conn, args.verbose)

        # Optionally analyze query plans
        analyze_results = None
        if args.analyze:
            logger.info("\nAnalyzing query plans...")
            analyze_results = run_explain_analyze(conn, args.verbose)

        # Print summary and exit
        exit_code = print_summary(index_results, analyze_results)
        sys.exit(exit_code)

    finally:
        conn.close()
        logger.info("Database connection closed")


if __name__ == "__main__":
    main()
