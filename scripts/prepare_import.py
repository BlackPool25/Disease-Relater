"""
Database Import using Supabase MCP Server
Reads CSV files and imports data using Supabase MCP execute_sql tool
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configuration
DATA_DIR = Path("/home/lightdesk/Projects/Disease-Relater/Data/processed")
STRATIFIED_DIR = Path("/home/lightdesk/Projects/Disease-Relater/data/processed")
PROJECT_ID = "gbohehihcncmlcpyxomv"


def load_diseases_data() -> pd.DataFrame:
    """Load and merge diseases data from both CSV files"""
    print("Loading diseases_master.csv...")
    diseases_master = pd.read_csv(DATA_DIR / "diseases_master.csv")
    print(f"  ✓ Loaded {len(diseases_master)} diseases from master")

    print("Loading disease_vectors_3d.csv...")
    vectors_3d = pd.read_csv(DATA_DIR / "disease_vectors_3d.csv")
    print(f"  ✓ Loaded {len(vectors_3d)} diseases with 3D vectors")

    # Merge the data - outer join to preserve all 1,080 ICD codes
    print("\nMerging datasets (outer join)...")
    merged = diseases_master.merge(vectors_3d, on="icd_code", how="outer")

    # Fill missing values appropriately
    merged["name_english"] = merged["name_english"].fillna("")
    merged["name_german"] = merged["name_german"].fillna("")
    merged["chapter_code"] = merged["chapter_code"].fillna("")
    merged["chapter_name"] = merged["chapter_name"].fillna("")
    merged["granularity"] = merged["granularity"].fillna("ICD")
    merged["avg_prevalence_male"] = merged["avg_prevalence_male"].fillna(0)
    merged["avg_prevalence_female"] = merged["avg_prevalence_female"].fillna(0)

    print(f"  ✓ Merged dataset: {len(merged)} total diseases")
    print(
        f"    - With both metadata and vectors: {merged[['name_german', 'vector_x']].notna().all(axis=1).sum()}"
    )
    print(
        f"    - Metadata only: {(merged['name_german'].notna() & merged['vector_x'].isna()).sum()}"
    )
    print(
        f"    - Vectors only: {(merged['name_german'].isna() & merged['vector_x'].notna()).sum()}"
    )

    return merged


def generate_disease_insert_sql(df: pd.DataFrame) -> str:
    """Generate SQL INSERT statements for diseases table"""
    values_list = []

    for _, row in df.iterrows():
        # Handle NaN values
        name_en = (
            str(row.get("name_english", "")).replace("'", "''")
            if pd.notna(row.get("name_english"))
            else ""
        )
        name_de = (
            str(row.get("name_german", "")).replace("'", "''")
            if pd.notna(row.get("name_german"))
            else ""
        )
        chapter = (
            str(row.get("chapter_code", ""))
            if pd.notna(row.get("chapter_code"))
            else ""
        )
        granularity = (
            str(row.get("granularity", "ICD"))
            if pd.notna(row.get("granularity"))
            else "ICD"
        )

        prev_male = (
            row.get("avg_prevalence_male", 0)
            if pd.notna(row.get("avg_prevalence_male"))
            else 0
        )
        prev_female = (
            row.get("avg_prevalence_female", 0)
            if pd.notna(row.get("avg_prevalence_female"))
            else 0
        )

        vec_x = row.get("vector_x") if pd.notna(row.get("vector_x")) else "NULL"
        vec_y = row.get("vector_y") if pd.notna(row.get("vector_y")) else "NULL"
        vec_z = row.get("vector_z") if pd.notna(row.get("vector_z")) else "NULL"

        # Build value tuple
        val = f"('{row['icd_code']}', '{name_en}', '{name_de}', '{chapter}', '{granularity}', {prev_male}, {prev_female}, {vec_x}, {vec_y}, {vec_z})"
        values_list.append(val)

    # Create the full INSERT statement
    sql = f"""
INSERT INTO diseases (icd_code, name_english, name_german, chapter_code, granularity, prevalence_male, prevalence_female, vector_x, vector_y, vector_z)
VALUES {", ".join(values_list)}
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
    updated_at = NOW();
"""
    return sql


def load_and_prepare_import():
    """Prepare all data for import"""
    print("=" * 60)
    print("DATA IMPORT PREPARATION")
    print("=" * 60)

    # Load diseases
    diseases_df = load_diseases_data()

    # Load relationships
    print("\nLoading disease_relationships_master.csv...")
    relationships_df = pd.read_csv(DATA_DIR / "disease_relationships_master.csv")
    print(f"  ✓ Loaded {len(relationships_df)} relationships")

    # Load stratified pairs
    print("\nLoading disease_pairs_clean.csv...")
    stratified_df = pd.read_csv(STRATIFIED_DIR / "disease_pairs_clean.csv")
    print(f"  ✓ Loaded {len(stratified_df)} stratified pairs")

    print("\n" + "=" * 60)
    print("IMPORT SUMMARY")
    print("=" * 60)
    print(f"Diseases to import: {len(diseases_df)}")
    print(f"Relationships to import: {len(relationships_df)}")
    print(f"Stratified pairs to import: {len(stratified_df)}")

    return diseases_df, relationships_df, stratified_df


if __name__ == "__main__":
    diseases_df, relationships_df, stratified_df = load_and_prepare_import()

    # Save prepared data for MCP import
    print("\nSaving prepared data...")
    diseases_df.to_json("/tmp/diseases_import.json", orient="records", indent=2)
    relationships_df.to_json(
        "/tmp/relationships_import.json", orient="records", indent=2
    )
    stratified_df.head(1000).to_json(
        "/tmp/stratified_import_sample.json", orient="records", indent=2
    )

    print("\n✓ Data prepared for import via MCP server")
    print("\nNext steps:")
    print("1. Use supabase-mcp-server_execute_sql to import diseases")
    print("2. Then import relationships with disease_id lookups")
    print("3. Finally import stratified data")
