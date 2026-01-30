"""
Full Database Import Script for Disease-Relater
Imports all CSV data into Supabase PostgreSQL database

Usage:
    1. Copy .env.example to .env and fill in your Supabase credentials
    2. source .venv/bin/activate
    3. python scripts/run_full_import.py

Author: Agent 2 (Data Import)
Date: 2026-01-30
"""

import os
import sys
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Try to import psycopg2
try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    print("Error: psycopg2 not installed. Run: uv pip install psycopg2-binary")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
DATA_DIR = Path("/home/lightdesk/Projects/Disease-Relater/Data/processed")
STRATIFIED_DIR = Path("/home/lightdesk/Projects/Disease-Relater/data/processed")
BATCH_SIZE = 100


class SupabaseImporter:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self):
        """Establish database connection"""
        db_url = os.getenv("SUPABASE_DB_URL")

        if not db_url:
            logger.error("SUPABASE_DB_URL not found in .env file")
            logger.info("Please copy .env.example to .env and fill in your credentials")
            sys.exit(1)

        try:
            self.conn = psycopg2.connect(db_url)
            self.cursor = self.conn.cursor()
            logger.info("✓ Connected to Supabase database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            sys.exit(1)

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            logger.info("✓ Database connection closed")

    def import_diseases(self) -> int:
        """Import merged diseases data"""
        logger.info("\n" + "=" * 60)
        logger.info("IMPORTING DISEASES")
        logger.info("=" * 60)

        # Load both CSV files
        logger.info("Loading diseases_master.csv...")
        diseases_master = pd.read_csv(DATA_DIR / "diseases_master.csv")
        logger.info(f"  Loaded {len(diseases_master)} diseases from master")

        logger.info("Loading disease_vectors_3d.csv...")
        vectors_3d = pd.read_csv(DATA_DIR / "disease_vectors_3d.csv")
        logger.info(f"  Loaded {len(vectors_3d)} diseases with 3D vectors")

        # Merge with outer join
        logger.info("Merging datasets (outer join)...")
        merged = diseases_master.merge(vectors_3d, on="icd_code", how="outer")
        logger.info(f"  Total diseases to import: {len(merged)}")

        # Prepare and insert in batches
        total_inserted = 0
        for i in range(0, len(merged), BATCH_SIZE):
            batch = merged.iloc[i : i + BATCH_SIZE]
            records = []

            for _, row in batch.iterrows():
                record = (
                    row["icd_code"],
                    str(row.get("name_english", ""))
                    if pd.notna(row.get("name_english"))
                    else "",
                    str(row.get("name_german", ""))
                    if pd.notna(row.get("name_german"))
                    else "",
                    str(row.get("chapter_code", ""))
                    if pd.notna(row.get("chapter_code"))
                    and str(row.get("chapter_code", "")).strip()
                    else None,
                    str(row.get("granularity", "ICD"))
                    if pd.notna(row.get("granularity"))
                    else "ICD",
                    float(row.get("avg_prevalence_male", 0))
                    if pd.notna(row.get("avg_prevalence_male"))
                    else 0.0,
                    float(row.get("avg_prevalence_female", 0))
                    if pd.notna(row.get("avg_prevalence_female"))
                    else 0.0,
                    float(row.get("vector_x"))
                    if pd.notna(row.get("vector_x"))
                    else None,
                    float(row.get("vector_y"))
                    if pd.notna(row.get("vector_y"))
                    else None,
                    float(row.get("vector_z"))
                    if pd.notna(row.get("vector_z"))
                    else None,
                )
                records.append(record)

            # Insert batch
            try:
                execute_values(
                    self.cursor,
                    """
                    INSERT INTO diseases (icd_code, name_english, name_german, chapter_code, granularity, 
                                        prevalence_male, prevalence_female, vector_x, vector_y, vector_z)
                    VALUES %s
                    ON CONFLICT (icd_code) DO UPDATE SET
                        name_english = EXCLUDED.name_english,
                        name_german = EXCLUDED.name_german,
                        chapter_code = EXCLUDED.chapter_code,
                        granularity = EXCLUDED.granularity,
                        prevalence_male = EXCLUDED.prevalence_male,
                        prevalence_female = EXCLUDED.prevalence_female,
                        vector_x = EXCLUDED.vector_x,
                        vector_y = EXCLUDED.vector_y,
                        vector_z = EXCLUDED.vector_z,
                        updated_at = NOW()
                    """,
                    records,
                )
                self.conn.commit()
                total_inserted += len(records)

                if (i // BATCH_SIZE + 1) % 10 == 0:
                    logger.info(f"  Progress: {total_inserted}/{len(merged)} diseases")

            except Exception as e:
                self.conn.rollback()
                logger.error(f"Error inserting batch {i // BATCH_SIZE}: {e}")
                raise

        logger.info(f"✓ Imported {total_inserted} diseases")
        return total_inserted

    def import_relationships(self) -> int:
        """Import aggregated relationships"""
        logger.info("\n" + "=" * 60)
        logger.info("IMPORTING DISEASE RELATIONSHIPS")
        logger.info("=" * 60)

        # Load relationships
        logger.info("Loading disease_relationships_master.csv...")
        df = pd.read_csv(DATA_DIR / "disease_relationships_master.csv")
        logger.info(f"  Loaded {len(df)} relationships")

        # Get disease ID mapping
        self.cursor.execute("SELECT id, icd_code FROM diseases")
        disease_map = {row[1]: row[0] for row in self.cursor.fetchall()}
        logger.info(f"  Found {len(disease_map)} diseases in database")

        # Prepare records
        total_inserted = 0
        for i in range(0, len(df), BATCH_SIZE):
            batch = df.iloc[i : i + BATCH_SIZE]
            records = []

            for _, row in batch.iterrows():
                d1_id = disease_map.get(row["disease_1_code"])
                d2_id = disease_map.get(row["disease_2_code"])

                if d1_id and d2_id:
                    record = (
                        d1_id,
                        d2_id,
                        float(row["odds_ratio_avg"]),
                        float(row["p_value_avg"])
                        if pd.notna(row["p_value_avg"])
                        else None,
                        int(row["patient_count_total"])
                        if pd.notna(row["patient_count_total"])
                        else 0,
                        str(row["icd_chapter_1"])
                        if pd.notna(row["icd_chapter_1"])
                        else None,
                        str(row["icd_chapter_2"])
                        if pd.notna(row["icd_chapter_2"])
                        else None,
                    )
                    records.append(record)

            if records:
                try:
                    execute_values(
                        self.cursor,
                        """
                        INSERT INTO disease_relationships 
                        (disease_1_id, disease_2_id, odds_ratio, p_value, patient_count_total, 
                         icd_chapter_1, icd_chapter_2)
                        VALUES %s
                        ON CONFLICT (disease_1_id, disease_2_id) DO UPDATE SET
                            odds_ratio = EXCLUDED.odds_ratio,
                            p_value = EXCLUDED.p_value,
                            patient_count_total = EXCLUDED.patient_count_total,
                            icd_chapter_1 = EXCLUDED.icd_chapter_1,
                            icd_chapter_2 = EXCLUDED.icd_chapter_2
                        """,
                        records,
                    )
                    self.conn.commit()
                    total_inserted += len(records)

                    if (i // BATCH_SIZE + 1) % 10 == 0:
                        logger.info(
                            f"  Progress: {total_inserted}/{len(df)} relationships"
                        )

                except Exception as e:
                    self.conn.rollback()
                    logger.error(f"Error inserting batch {i // BATCH_SIZE}: {e}")
                    raise

        logger.info(f"✓ Imported {total_inserted} relationships")
        return total_inserted

    def import_stratified(self) -> int:
        """Import stratified disease relationships"""
        logger.info("\n" + "=" * 60)
        logger.info("IMPORTING STRATIFIED RELATIONSHIPS")
        logger.info("=" * 60)

        # Load stratified data
        logger.info("Loading disease_pairs_clean.csv...")
        df = pd.read_csv(STRATIFIED_DIR / "disease_pairs_clean.csv")
        logger.info(f"  Loaded {len(df)} stratified pairs")

        # Get disease ID mapping
        self.cursor.execute("SELECT id, icd_code FROM diseases")
        disease_map = {row[1]: row[0] for row in self.cursor.fetchall()}

        # Use smaller batch size for stratified data (more columns)
        stratified_batch_size = 50
        total_inserted = 0

        for i in range(0, len(df), stratified_batch_size):
            batch = df.iloc[i : i + stratified_batch_size]
            records = []

            for _, row in batch.iterrows():
                d1_id = disease_map.get(row["disease_1_code"])
                d2_id = disease_map.get(row["disease_2_code"])

                if d1_id and d2_id:
                    record = (
                        d1_id,
                        d2_id,
                        str(row["sex"]),
                        str(row["stratum_value"])
                        if pd.notna(row["stratum_value"])
                        else None,
                        str(row["stratum_type"])
                        if pd.notna(row["stratum_type"])
                        else None,
                        float(row["odds_ratio"]),
                        float(row["p_value"]) if pd.notna(row["p_value"]) else None,
                        int(row["patient_count"])
                        if pd.notna(row["patient_count"])
                        else 0,
                        str(row["granularity"]),
                        str(row["icd_chapter_1"])
                        if pd.notna(row["icd_chapter_1"])
                        else None,
                        str(row["icd_chapter_2"])
                        if pd.notna(row["icd_chapter_2"])
                        else None,
                    )
                    records.append(record)

            if records:
                try:
                    execute_values(
                        self.cursor,
                        """
                        INSERT INTO disease_relationships_stratified 
                        (disease_1_id, disease_2_id, sex, age_group, year_range, odds_ratio, p_value,
                         patient_count, granularity, icd_chapter_1, icd_chapter_2)
                        VALUES %s
                        ON CONFLICT (disease_1_id, disease_2_id, sex, age_group, year_range) DO UPDATE SET
                            odds_ratio = EXCLUDED.odds_ratio,
                            p_value = EXCLUDED.p_value,
                            patient_count = EXCLUDED.patient_count
                        """,
                        records,
                    )
                    self.conn.commit()
                    total_inserted += len(records)

                    if (i // stratified_batch_size + 1) % 100 == 0:
                        logger.info(
                            f"  Progress: {total_inserted}/{len(df)} stratified pairs"
                        )

                except Exception as e:
                    self.conn.rollback()
                    logger.error(
                        f"Error inserting batch {i // stratified_batch_size}: {e}"
                    )
                    raise

        logger.info(f"✓ Imported {total_inserted} stratified relationships")
        return total_inserted

    def verify_import(self):
        """Verify row counts in all tables"""
        logger.info("\n" + "=" * 60)
        logger.info("IMPORT VERIFICATION")
        logger.info("=" * 60)

        tables = [
            "diseases",
            "disease_relationships",
            "disease_relationships_stratified",
            "icd_chapters",
        ]

        expected = {
            "diseases": 1247,
            "disease_relationships": 9232,
            "disease_relationships_stratified": 74901,
            "icd_chapters": 21,
        }

        for table in tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = self.cursor.fetchone()[0]
            exp = expected.get(table, "?")
            status = "✓" if count == exp else "⚠"
            logger.info(f"{status} {table}: {count:,} rows (expected: {exp:,})")


def main():
    logger.info("=" * 60)
    logger.info("DISEASE-RELATER DATABASE IMPORT")
    logger.info("=" * 60)

    # Check if .env exists
    if not Path(".env").exists():
        logger.error(".env file not found!")
        logger.info(
            "Please copy .env.example to .env and fill in your Supabase credentials:"
        )
        logger.info("  cp .env.example .env")
        logger.info("\nGet your credentials from:")
        logger.info(
            "  https://supabase.com/dashboard/project/gbohehihcncmlcpyxomv/settings/database"
        )
        sys.exit(1)

    importer = None
    try:
        importer = SupabaseImporter()

        # Import data
        diseases_count = importer.import_diseases()
        relationships_count = importer.import_relationships()
        stratified_count = importer.import_stratified()

        # Verify
        importer.verify_import()

        logger.info("\n" + "=" * 60)
        logger.info("IMPORT COMPLETE")
        logger.info("=" * 60)
        logger.info(f"✓ Total diseases imported: {diseases_count}")
        logger.info(f"✓ Total relationships imported: {relationships_count}")
        logger.info(f"✓ Total stratified pairs imported: {stratified_count}")

    except Exception as e:
        logger.error(f"Import failed: {e}")
        sys.exit(1)
    finally:
        if importer:
            importer.close()


if __name__ == "__main__":
    main()
