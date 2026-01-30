"""
Supabase Data Import Script
Uses supabase-py client to import data from CSV files
"""

import os
import sys
import pandas as pd
from pathlib import Path
from supabase import create_client, Client
from typing import List, Dict, Any
import time

# Configuration
SUPABASE_URL = "https://gbohehihcncmlcpyxomv.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")  # Need service role key

DATA_DIR = Path("/home/lightdesk/Projects/Disease-Relater/Data/processed")
STRATIFIED_DIR = Path("/home/lightdesk/Projects/Disease-Relater/data/processed")


class SupabaseImporter:
    def __init__(self, url: str, key: str):
        self.supabase: Client = create_client(url, key)
        self.batch_size = 100

    def import_diseases(self) -> int:
        """Import diseases data from merged CSV files"""
        print("Loading diseases data...")

        # Load both files
        diseases_master = pd.read_csv(DATA_DIR / "diseases_master.csv")
        vectors_3d = pd.read_csv(DATA_DIR / "disease_vectors_3d.csv")

        print(f"  diseases_master: {len(diseases_master)} rows")
        print(f"  disease_vectors_3d: {len(vectors_3d)} rows")

        # Merge with outer join
        merged = diseases_master.merge(vectors_3d, on="icd_code", how="outer")
        print(f"  Merged: {len(merged)} total diseases")

        # Prepare records
        records = []
        for _, row in merged.iterrows():
            record = {
                "icd_code": row["icd_code"],
                "name_english": str(row["name_english"])
                if pd.notna(row.get("name_english"))
                else "",
                "name_german": str(row["name_german"])
                if pd.notna(row.get("name_german"))
                else "",
                "chapter_code": str(row["chapter_code"])
                if pd.notna(row.get("chapter_code"))
                else "",
                "granularity": str(row["granularity"])
                if pd.notna(row.get("granularity"))
                else "ICD",
                "prevalence_male": float(row["avg_prevalence_male"])
                if pd.notna(row.get("avg_prevalence_male"))
                else 0.0,
                "prevalence_female": float(row["avg_prevalence_female"])
                if pd.notna(row.get("avg_prevalence_female"))
                else 0.0,
                "vector_x": float(row["vector_x"])
                if pd.notna(row.get("vector_x"))
                else None,
                "vector_y": float(row["vector_y"])
                if pd.notna(row.get("vector_y"))
                else None,
                "vector_z": float(row["vector_z"])
                if pd.notna(row.get("vector_z"))
                else None,
            }
            records.append(record)

        # Batch insert
        total_inserted = 0
        for i in range(0, len(records), self.batch_size):
            batch = records[i : i + self.batch_size]
            try:
                # Use upsert to handle conflicts
                response = self.supabase.table("diseases").upsert(batch).execute()
                total_inserted += len(batch)
                print(
                    f"  Inserted batch {i // self.batch_size + 1}: {len(batch)} records"
                )
                time.sleep(0.1)  # Rate limiting
            except Exception as e:
                print(f"  Error inserting batch: {e}")

        print(f"✓ Imported {total_inserted} diseases")
        return total_inserted

    def import_relationships(self) -> int:
        """Import aggregated relationships"""
        print("\nLoading relationships data...")

        df = pd.read_csv(DATA_DIR / "disease_relationships_master.csv")
        print(f"  Loaded {len(df)} relationships")

        # Get disease ID mapping
        response = self.supabase.table("diseases").select("id, icd_code").execute()
        disease_map = {d["icd_code"]: d["id"] for d in response.data}

        records = []
        for _, row in df.iterrows():
            d1_id = disease_map.get(row["disease_1_code"])
            d2_id = disease_map.get(row["disease_2_code"])

            if d1_id and d2_id:
                record = {
                    "disease_1_id": d1_id,
                    "disease_2_id": d2_id,
                    "odds_ratio": float(row["odds_ratio_avg"]),
                    "p_value": float(row["p_value_avg"])
                    if pd.notna(row["p_value_avg"])
                    else None,
                    "patient_count_total": int(row["patient_count_total"])
                    if pd.notna(row["patient_count_total"])
                    else 0,
                    "icd_chapter_1": str(row["icd_chapter_1"]),
                    "icd_chapter_2": str(row["icd_chapter_2"]),
                }
                records.append(record)

        print(f"  Prepared {len(records)} valid relationships")

        # Batch insert
        total_inserted = 0
        for i in range(0, len(records), self.batch_size):
            batch = records[i : i + self.batch_size]
            try:
                response = (
                    self.supabase.table("disease_relationships").upsert(batch).execute()
                )
                total_inserted += len(batch)
                print(
                    f"  Inserted batch {i // self.batch_size + 1}: {len(batch)} records"
                )
                time.sleep(0.1)
            except Exception as e:
                print(f"  Error inserting batch: {e}")

        print(f"✓ Imported {total_inserted} relationships")
        return total_inserted

    def verify_import(self):
        """Verify row counts in database"""
        print("\nVerifying import...")

        diseases_count = (
            self.supabase.table("diseases").select("*", count="exact").execute()
        )
        print(f"  Diseases table: {diseases_count.count} rows")

        rel_count = (
            self.supabase.table("disease_relationships")
            .select("*", count="exact")
            .execute()
        )
        print(f"  Relationships table: {rel_count.count} rows")

        strat_count = (
            self.supabase.table("disease_relationships_stratified")
            .select("*", count="exact")
            .execute()
        )
        print(f"  Stratified table: {strat_count.count} rows")


def main():
    if not SUPABASE_KEY:
        print("Error: SUPABASE_SERVICE_KEY environment variable not set")
        print("Set it with: export SUPABASE_SERVICE_KEY='your-service-role-key'")
        sys.exit(1)

    print("=" * 60)
    print("SUPABASE DATA IMPORT")
    print("=" * 60)
    print(f"Project URL: {SUPABASE_URL}")
    print()

    importer = SupabaseImporter(SUPABASE_URL, SUPABASE_KEY)

    # Import diseases
    diseases_count = importer.import_diseases()

    # Import relationships
    rel_count = importer.import_relationships()

    # Verify
    importer.verify_import()

    print("\n" + "=" * 60)
    print("IMPORT COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
