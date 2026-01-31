"""
Database Import Module for Disease-Relater

Imports processed CSV data into PostgreSQL/Supabase database.
Handles data merging, table creation, and bulk inserts with integrity checks.

Author: Agent 2 (Data Import Pipeline)
Date: 2026-01-30

Environment Variables:
    SUPABASE_URL - Database connection URL (postgresql://...)
    SUPABASE_KEY - Service role key for authentication
    DB_PASSWORD - Database password (if not in URL)

Usage:
    python scripts/import_to_database.py
    python scripts/import_to_database.py --validate-first --verbose
    python scripts/import_to_database.py --skip-stratified
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse

import pandas as pd
import numpy as np

# Try to import psycopg2, provide helpful error if not installed
try:
    import psycopg2
    from psycopg2.extras import execute_values
    from psycopg2 import sql
except ImportError:
    print("Error: psycopg2-binary not installed.")
    print("Install with: pip install psycopg2-binary")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Database schema definitions
TABLE_SCHEMAS = {
    "diseases": """
        CREATE TABLE IF NOT EXISTS diseases (
            id SERIAL PRIMARY KEY,
            icd_code VARCHAR(20) UNIQUE NOT NULL,
            name_english VARCHAR(255),
            name_german VARCHAR(255),
            chapter_code VARCHAR(10),
            chapter_name VARCHAR(255),
            granularity VARCHAR(20),
            avg_prevalence_male FLOAT,
            avg_prevalence_female FLOAT,
            vector_x FLOAT,
            vector_y FLOAT,
            vector_z FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """,
    "disease_relationships": """
        CREATE TABLE IF NOT EXISTS disease_relationships (
            id SERIAL PRIMARY KEY,
            disease_1_id INTEGER REFERENCES diseases(id),
            disease_2_id INTEGER REFERENCES diseases(id),
            disease_1_code VARCHAR(20),
            disease_2_code VARCHAR(20),
            odds_ratio_avg FLOAT,
            p_value_avg FLOAT,
            patient_count_total INTEGER,
            icd_chapter_1 VARCHAR(10),
            icd_chapter_2 VARCHAR(10),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(disease_1_id, disease_2_id)
        );
    """,
    "prevalence_stratified": """
        CREATE TABLE IF NOT EXISTS prevalence_stratified (
            id SERIAL PRIMARY KEY,
            disease_id INTEGER REFERENCES diseases(id),
            icd_code VARCHAR(20),
            sex VARCHAR(10),
            stratum_type VARCHAR(20),
            stratum_value VARCHAR(50),
            odds_ratio FLOAT,
            p_value FLOAT,
            patient_count INTEGER,
            granularity VARCHAR(20),
            icd_chapter_1 VARCHAR(10),
            icd_chapter_2 VARCHAR(10),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """,
}


INDEX_DEFINITIONS = {
    "diseases": [
        "CREATE INDEX IF NOT EXISTS idx_diseases_icd_code ON diseases(icd_code);",
        "CREATE INDEX IF NOT EXISTS idx_diseases_chapter ON diseases(chapter_code);",
        "CREATE INDEX IF NOT EXISTS idx_diseases_granularity ON diseases(granularity);",
    ],
    "disease_relationships": [
        "CREATE INDEX IF NOT EXISTS idx_rel_disease1 ON disease_relationships(disease_1_id);",
        "CREATE INDEX IF NOT EXISTS idx_rel_disease2 ON disease_relationships(disease_2_id);",
        "CREATE INDEX IF NOT EXISTS idx_rel_odds_ratio ON disease_relationships(odds_ratio_avg);",
        # Composite index for efficient relationship lookups by both disease IDs
        "CREATE INDEX IF NOT EXISTS idx_rel_composite ON disease_relationships(disease_1_id, disease_2_id);",
    ],
    "prevalence_stratified": [
        "CREATE INDEX IF NOT EXISTS idx_prev_disease ON prevalence_stratified(disease_id);",
        "CREATE INDEX IF NOT EXISTS idx_prev_sex ON prevalence_stratified(sex);",
    ],
}


def get_database_connection() -> Tuple[
    Optional[psycopg2.extensions.connection], Optional[str]
]:
    """
    Establish database connection using environment variables.

    Returns:
        Tuple of (connection, error_message)
    """
    # Get connection details from environment
    db_url = os.getenv("SUPABASE_URL", "")
    db_key = os.getenv("SUPABASE_KEY", "")
    db_password = os.getenv("DB_PASSWORD", "")

    if not db_url:
        return None, "SUPABASE_URL environment variable not set"

    try:
        # Parse the connection URL
        parsed = urlparse(db_url)

        # Extract connection parameters
        host = parsed.hostname
        port = parsed.port or 5432
        database = parsed.path.lstrip("/") if parsed.path else "postgres"
        user = parsed.username or "postgres"
        password = parsed.password or db_password or db_key

        if not host:
            return None, f"Could not parse host from URL: {db_url}"

        # Connect to database
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
        )

        logger.info(f"Connected to database: {host}:{port}/{database}")
        return conn, None

    except Exception as e:
        return None, f"Database connection failed: {e}"


def create_tables(conn: psycopg2.extensions.connection) -> Tuple[bool, Optional[str]]:
    """
    Create database tables if they don't exist.

    Args:
        conn: Database connection

    Returns:
        Tuple of (success, error_message)
    """
    try:
        with conn.cursor() as cursor:
            # Create tables
            for table_name, schema_sql in TABLE_SCHEMAS.items():
                logger.info(f"Creating table: {table_name}")
                cursor.execute(schema_sql)
                conn.commit()

            # Create indexes
            for table_name, indexes in INDEX_DEFINITIONS.items():
                for idx_sql in indexes:
                    cursor.execute(idx_sql)
                conn.commit()

        logger.info("Tables and indexes created successfully")
        return True, None

    except Exception as e:
        return False, f"Failed to create tables: {e}"


def merge_disease_data(data_dir: Path) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Merge diseases_master.csv with disease_vectors_3d.csv using outer join.

    Args:
        data_dir: Directory containing CSV files

    Returns:
        Tuple of (merged_dataframe, error_message)
    """
    try:
        logger.info("Loading disease data for merging...")

        # Load both datasets
        df_master = pd.read_csv(data_dir / "diseases_master.csv")
        df_vectors = pd.read_csv(data_dir / "disease_vectors_3d.csv")

        logger.info(
            f"Loaded: {len(df_master)} from diseases_master, {len(df_vectors)} from disease_vectors_3d"
        )

        # Perform outer join on icd_code
        df_merged = df_master.merge(
            df_vectors, on="icd_code", how="outer", suffixes=("", "_vec")
        )

        # Log merge results
        from_master_only = df_merged["vector_x"].isna().sum()
        from_vectors_only = df_merged["chapter_code"].isna().sum()
        merged_count = len(df_merged) - from_master_only - from_vectors_only

        logger.info(f"Merge results:")
        logger.info(f"  - Both sources: {merged_count}")
        logger.info(f"  - Master only: {from_master_only}")
        logger.info(f"  - Vectors only: {from_vectors_only}")
        logger.info(f"  - Total: {len(df_merged)}")

        # Fill missing values appropriately
        df_merged["name_english"] = df_merged["name_english"].fillna("")
        df_merged["name_german"] = df_merged["name_german"].fillna("")
        df_merged["chapter_code"] = df_merged["chapter_code"].fillna("")
        df_merged["chapter_name"] = df_merged["chapter_name"].fillna("")
        df_merged["granularity"] = df_merged["granularity"].fillna("")
        df_merged["avg_prevalence_male"] = df_merged["avg_prevalence_male"].fillna(0.0)
        df_merged["avg_prevalence_female"] = df_merged["avg_prevalence_female"].fillna(
            0.0
        )
        df_merged["vector_x"] = df_merged["vector_x"].fillna(0.0)
        df_merged["vector_y"] = df_merged["vector_y"].fillna(0.0)
        df_merged["vector_z"] = df_merged["vector_z"].fillna(0.0)

        return df_merged, None

    except Exception as e:
        return None, f"Failed to merge disease data: {e}"


def import_diseases(
    conn: psycopg2.extensions.connection, df: pd.DataFrame, batch_size: int = 1000
) -> Tuple[bool, int, Optional[str]]:
    """
    Import merged disease data into database.

    Args:
        conn: Database connection
        df: Merged disease DataFrame
        batch_size: Number of rows per batch

    Returns:
        Tuple of (success, rows_imported, error_message)
    """
    try:
        logger.info(f"Importing {len(df)} diseases...")

        # Prepare data for insert
        columns = [
            "icd_code",
            "name_english",
            "name_german",
            "chapter_code",
            "chapter_name",
            "granularity",
            "avg_prevalence_male",
            "avg_prevalence_female",
            "vector_x",
            "vector_y",
            "vector_z",
        ]

        data = [tuple(row[col] for col in columns) for _, row in df.iterrows()]

        # Insert in batches
        with conn.cursor() as cursor:
            for i in range(0, len(data), batch_size):
                batch = data[i : i + batch_size]
                execute_values(
                    cursor,
                    """
                    INSERT INTO diseases (
                        icd_code, name_english, name_german, chapter_code,
                        chapter_name, granularity, avg_prevalence_male,
                        avg_prevalence_female, vector_x, vector_y, vector_z
                    ) VALUES %s
                    ON CONFLICT (icd_code) DO UPDATE SET
                        name_english = EXCLUDED.name_english,
                        name_german = EXCLUDED.name_german,
                        chapter_code = EXCLUDED.chapter_code,
                        chapter_name = EXCLUDED.chapter_name,
                        granularity = EXCLUDED.granularity,
                        avg_prevalence_male = EXCLUDED.avg_prevalence_male,
                        avg_prevalence_female = EXCLUDED.avg_prevalence_female,
                        vector_x = EXCLUDED.vector_x,
                        vector_y = EXCLUDED.vector_y,
                        vector_z = EXCLUDED.vector_z;
                    """,
                    batch,
                )
                conn.commit()
                logger.debug(
                    f"Imported batch {i // batch_size + 1}/{(len(data) - 1) // batch_size + 1}"
                )

        logger.info(f"Successfully imported {len(df)} diseases")
        return True, len(df), None

    except Exception as e:
        conn.rollback()
        return False, 0, f"Failed to import diseases: {e}"


def import_relationships(
    conn: psycopg2.extensions.connection, data_dir: Path, batch_size: int = 1000
) -> Tuple[bool, int, Optional[str]]:
    """
    Import disease relationships from aggregated file.

    Args:
        conn: Database connection
        data_dir: Directory containing CSV files
        batch_size: Number of rows per batch

    Returns:
        Tuple of (success, rows_imported, error_message)
    """
    try:
        logger.info("Loading disease relationships...")
        df = pd.read_csv(data_dir / "disease_relationships_master.csv")
        logger.info(f"Loaded {len(df)} relationships")

        # Build ICD code to ID mapping
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, icd_code FROM diseases;")
            code_to_id = {row[1]: row[0] for row in cursor.fetchall()}

        logger.info(f"Built mapping for {len(code_to_id)} diseases")

        # Prepare data with foreign key lookups
        relationships = []
        skipped = 0

        for _, row in df.iterrows():
            disease_1_id = code_to_id.get(row["disease_1_code"])
            disease_2_id = code_to_id.get(row["disease_2_code"])

            if not disease_1_id or not disease_2_id:
                skipped += 1
                continue

            relationships.append(
                (
                    disease_1_id,
                    disease_2_id,
                    row["disease_1_code"],
                    row["disease_2_code"],
                    float(row["odds_ratio_avg"])
                    if pd.notna(row["odds_ratio_avg"])
                    else None,
                    float(row["p_value_avg"]) if pd.notna(row["p_value_avg"]) else None,
                    int(row["patient_count_total"])
                    if pd.notna(row["patient_count_total"])
                    else 0,
                    row["icd_chapter_1"],
                    row["icd_chapter_2"],
                )
            )

        if skipped > 0:
            logger.warning(
                f"Skipped {skipped} relationships due to missing disease codes"
            )

        # Insert in batches
        with conn.cursor() as cursor:
            for i in range(0, len(relationships), batch_size):
                batch = relationships[i : i + batch_size]
                execute_values(
                    cursor,
                    """
                    INSERT INTO disease_relationships (
                        disease_1_id, disease_2_id, disease_1_code, disease_2_code,
                        odds_ratio_avg, p_value_avg, patient_count_total,
                        icd_chapter_1, icd_chapter_2
                    ) VALUES %s
                    ON CONFLICT (disease_1_id, disease_2_id) DO UPDATE SET
                        odds_ratio_avg = EXCLUDED.odds_ratio_avg,
                        p_value_avg = EXCLUDED.p_value_avg,
                        patient_count_total = EXCLUDED.patient_count_total;
                    """,
                    batch,
                )
                conn.commit()

        logger.info(f"Successfully imported {len(relationships)} relationships")
        return True, len(relationships), None

    except Exception as e:
        conn.rollback()
        return False, 0, f"Failed to import relationships: {e}"


def verify_import(conn: psycopg2.extensions.connection) -> Dict[str, Any]:
    """
    Verify data integrity after import with row counts.

    Args:
        conn: Database connection

    Returns:
        Dictionary with verification results
    """
    results = {}

    try:
        with conn.cursor() as cursor:
            # Count rows in each table
            for table in ["diseases", "disease_relationships", "prevalence_stratified"]:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                results[table] = count
                logger.info(f"Table {table}: {count} rows")

            # Spot check: verify some diseases have relationships
            cursor.execute("""
                SELECT d.icd_code, COUNT(r.id) as rel_count
                FROM diseases d
                LEFT JOIN disease_relationships r ON d.id = r.disease_1_id
                GROUP BY d.id, d.icd_code
                ORDER BY rel_count DESC
                LIMIT 5;
            """)
            top_diseases = cursor.fetchall()
            results["top_connected_diseases"] = [
                {"icd_code": row[0], "relationships": row[1]} for row in top_diseases
            ]

        results["valid"] = True
        return results

    except Exception as e:
        results["valid"] = False
        results["error"] = str(e)
        return results


def main():
    """Main entry point for import script."""
    parser = argparse.ArgumentParser(
        description="Import Disease-Relater data into PostgreSQL database"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="Data/processed",
        help="Directory containing CSV files (default: Data/processed)",
    )
    parser.add_argument(
        "--validate-first",
        action="store_true",
        help="Run validation before import",
    )
    parser.add_argument(
        "--skip-stratified",
        action="store_true",
        help="Skip importing stratified prevalence data",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Batch size for inserts (default: 1000)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    data_dir = Path(args.data_dir)

    # Validate first if requested
    if args.validate_first:
        logger.info("Running pre-import validation...")
        from scripts.validate_data import validate_all_data, print_validation_report

        report = validate_all_data(data_dir, verbose=args.verbose)
        print_validation_report(report)

        if not report["valid"]:
            logger.error("Validation failed. Aborting import.")
            sys.exit(1)

    # Connect to database
    logger.info("Connecting to database...")
    conn, error = get_database_connection()
    if not conn:
        logger.error(f"Database connection failed: {error}")
        print("\nMake sure environment variables are set:")
        print("  export SUPABASE_URL='postgresql://...'")
        print("  export SUPABASE_KEY='your-service-role-key'")
        sys.exit(1)

    try:
        # Create tables
        logger.info("Creating tables...")
        success, error = create_tables(conn)
        if not success:
            logger.error(f"Failed to create tables: {error}")
            sys.exit(1)

        # Import diseases (merge master + vectors)
        logger.info("Merging and importing disease data...")
        df_diseases, error = merge_disease_data(data_dir)
        if df_diseases is None:
            logger.error(f"Failed to merge disease data: {error}")
            sys.exit(1)

        success, count, error = import_diseases(conn, df_diseases, args.batch_size)
        if not success:
            logger.error(f"Failed to import diseases: {error}")
            sys.exit(1)

        # Import relationships
        logger.info("Importing disease relationships...")
        success, count, error = import_relationships(conn, data_dir, args.batch_size)
        if not success:
            logger.error(f"Failed to import relationships: {error}")
            sys.exit(1)

        # Verify import
        logger.info("Verifying import...")
        verification = verify_import(conn)

        # Print summary
        print("\n" + "=" * 60)
        print("IMPORT SUMMARY")
        print("=" * 60)
        print(f"Diseases imported: {verification.get('diseases', 0)}")
        print(f"Relationships imported: {verification.get('disease_relationships', 0)}")
        print("\nTop connected diseases:")
        for disease in verification.get("top_connected_diseases", []):
            print(f"  {disease['icd_code']}: {disease['relationships']} relationships")
        print("=" * 60)

        logger.info("Import completed successfully!")

    except Exception as e:
        logger.exception("Import failed with error")
        sys.exit(1)

    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed")


if __name__ == "__main__":
    main()
