"""
Import data to Supabase using MCP server
Execute this to perform chunked imports
"""

import json
import subprocess
import pandas as pd
from pathlib import Path

PROJECT_ID = "gbohehihcncmlcpyxomv"


def execute_sql(query: str) -> dict:
    """Execute SQL via Supabase MCP server"""
    # We'll write queries to a file and execute them
    return {"query": query[:100] + "..." if len(query) > 100 else query}


# Load prepared data
diseases_df = pd.read_json("/tmp/diseases_import.json")
print(f"Loaded {len(diseases_df)} diseases")

# Generate chunked INSERT statements for diseases
BATCH_SIZE = 100
num_batches = (len(diseases_df) + BATCH_SIZE - 1) // BATCH_SIZE

print(f"\nGenerating {num_batches} batches for diseases...")

batch_files = []
for i in range(num_batches):
    start = i * BATCH_SIZE
    end = min((i + 1) * BATCH_SIZE, len(diseases_df))
    batch_df = diseases_df.iloc[start:end]

    values = []
    for _, row in batch_df.iterrows():
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

        vec_x = row.get("vector_x")
        vec_y = row.get("vector_y")
        vec_z = row.get("vector_z")

        vec_x_str = str(vec_x) if pd.notna(vec_x) else "NULL"
        vec_y_str = str(vec_y) if pd.notna(vec_y) else "NULL"
        vec_z_str = str(vec_z) if pd.notna(vec_z) else "NULL"

        val = f"('{row['icd_code']}', '{name_en}', '{name_de}', '{chapter}', '{granularity}', {prev_male}, {prev_female}, {vec_x_str}, {vec_y_str}, {vec_z_str})"
        values.append(val)

    sql = f"""INSERT INTO diseases (icd_code, name_english, name_german, chapter_code, granularity, prevalence_male, prevalence_female, vector_x, vector_y, vector_z)
VALUES {", ".join(values)}
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
    updated_at = NOW();"""

    # Save batch SQL to file
    batch_file = f"/tmp/diseases_batch_{i:03d}.sql"
    with open(batch_file, "w") as f:
        f.write(sql)
    batch_files.append(batch_file)
    print(f"  Batch {i + 1}/{num_batches}: rows {start}-{end - 1} -> {batch_file}")

print(f"\n✓ Generated {len(batch_files)} SQL batch files")
print(
    "\nReady for MCP import. Execute each batch file using supabase-mcp-server_execute_sql"
)
