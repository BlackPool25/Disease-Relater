#!/usr/bin/env python3
"""Quick test to verify mapping file fixes."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from data_cleaning import load_mapping, GRANULARITY_CONFIG

# Test loading each mapping file
print("Testing mapping file loading...")
print()

for granularity in ["ICD", "Blocks", "Chronic"]:
    print(f"\n{granularity}:")
    print(f"  Config: {GRANULARITY_CONFIG[granularity]}")

    try:
        df = load_mapping(granularity)
        print(f"  Loaded successfully: {len(df)} rows")
        print(f"  Columns: {list(df.columns)}")
        print(
            f"  First code: {df.iloc[0][GRANULARITY_CONFIG[granularity]['code_col']]}"
        )
        print(
            f"  First name: {df.iloc[0][GRANULARITY_CONFIG[granularity]['name_col']]}"
        )
    except Exception as e:
        print(f"  ERROR: {e}")

print("\n✓ Mapping files test complete!")
