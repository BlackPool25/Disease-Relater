"""Alter table to fix icd_code column size"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv("SUPABASE_DB_URL"))
cursor = conn.cursor()

# Drop dependent views first
cursor.execute("DROP VIEW IF EXISTS diseases_complete;")
cursor.execute("DROP VIEW IF EXISTS top_relationships;")
cursor.execute("DROP VIEW IF EXISTS disease_network_stats;")
conn.commit()
print("✓ Dropped dependent views")

# Alter the column
cursor.execute("ALTER TABLE diseases ALTER COLUMN icd_code TYPE VARCHAR(50);")
conn.commit()
print("✓ Altered diseases.icd_code to VARCHAR(50)")

# Recreate views
cursor.execute("""
CREATE OR REPLACE VIEW diseases_complete AS
SELECT 
    d.id,
    d.icd_code,
    d.name_english,
    d.name_german,
    d.chapter_code,
    ic.chapter_name,
    d.granularity,
    d.prevalence_male,
    d.prevalence_female,
    d.prevalence_total,
    d.vector_x,
    d.vector_y,
    d.vector_z,
    d.has_english_name,
    d.has_german_name,
    d.has_prevalence_data,
    d.has_3d_coordinates
FROM diseases d
LEFT JOIN icd_chapters ic ON d.chapter_code = ic.chapter_code
WHERE d.has_3d_coordinates = TRUE;
""")
conn.commit()
print("✓ Recreated diseases_complete view")

cursor.close()
conn.close()
