"""
Data Validation Module for Disease-Relater Database Import

Validates CSV files before database import to ensure data integrity.
Checks file existence, column schemas, data types, and identifies
discrepancies between datasets.

Author: Agent 2 (Data Import Pipeline)
Date: 2026-01-30

Usage:
    python scripts/validate_data.py
    python scripts/validate_data.py --data-dir Data/processed --verbose
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Expected schemas for each CSV file
EXPECTED_SCHEMAS = {
    "diseases_master.csv": {
        "required_columns": [
            "icd_code",
            "name_english",
            "name_german",
            "chapter_code",
            "chapter_name",
            "granularity",
            "avg_prevalence_male",
            "avg_prevalence_female",
        ],
        "numeric_columns": [
            "avg_prevalence_male",
            "avg_prevalence_female",
        ],
        "min_rows": 700,
    },
    "disease_relationships_master.csv": {
        "required_columns": [
            "disease_1_code",
            "disease_1_name",
            "disease_2_code",
            "disease_2_name",
            "odds_ratio_avg",
            "p_value_avg",
            "patient_count_total",
            "icd_chapter_1",
            "icd_chapter_2",
        ],
        "numeric_columns": [
            "odds_ratio_avg",
            "p_value_avg",
            "patient_count_total",
        ],
        "min_rows": 9000,
    },
    "disease_vectors_3d.csv": {
        "required_columns": [
            "icd_code",
            "vector_x",
            "vector_y",
            "vector_z",
        ],
        "numeric_columns": [
            "vector_x",
            "vector_y",
            "vector_z",
        ],
        "min_rows": 1000,
    },
    "disease_pairs_clean.csv": {
        "required_columns": [
            "disease_1_code",
            "disease_1_name_de",
            "disease_1_name_en",
            "disease_2_code",
            "disease_2_name_de",
            "disease_2_name_en",
            "odds_ratio",
            "p_value",
            "patient_count",
            "sex",
            "stratum_type",
            "stratum_value",
            "granularity",
            "icd_chapter_1",
            "icd_chapter_2",
        ],
        "numeric_columns": [
            "odds_ratio",
            "p_value",
            "patient_count",
        ],
        "min_rows": 70000,
    },
}


def validate_file_exists(file_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Check if a file exists and is readable.

    Args:
        file_path: Path to the file to check

    Returns:
        Tuple of (success, error_message)
    """
    if not file_path.exists():
        return False, f"File not found: {file_path}"
    if not file_path.is_file():
        return False, f"Path is not a file: {file_path}"
    if file_path.stat().st_size == 0:
        return False, f"File is empty: {file_path}"
    return True, None


def validate_csv_structure(
    df: pd.DataFrame, filename: str, schema: Dict
) -> Tuple[bool, List[str]]:
    """
    Validate CSV structure against expected schema.

    Args:
        df: DataFrame to validate
        filename: Name of the file for error messages
        schema: Expected schema dictionary

    Returns:
        Tuple of (success, list_of_errors)
    """
    errors = []

    # Check required columns
    required_cols = schema.get("required_columns", [])
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")

    # Check row count
    min_rows = schema.get("min_rows", 0)
    if len(df) < min_rows:
        errors.append(f"Insufficient rows: {len(df)} (expected at least {min_rows})")

    # Check numeric columns have valid data
    numeric_cols = schema.get("numeric_columns", [])
    for col in numeric_cols:
        if col in df.columns:
            # Check for non-numeric values
            non_numeric = df[col].apply(
                lambda x: not pd.isna(x) and not isinstance(x, (int, float))
            )
            if non_numeric.any():
                errors.append(f"Column '{col}' contains non-numeric values")

            # Check for extreme outliers (possible data corruption)
            if df[col].dtype in [np.float64, np.float32, np.int64, np.int32]:
                col_max = df[col].max()
                col_min = df[col].min()
                if pd.notna(col_max) and abs(col_max) > 1e10:
                    errors.append(f"Column '{col}' has suspicious max value: {col_max}")
                if pd.notna(col_min) and abs(col_min) > 1e10:
                    errors.append(f"Column '{col}' has suspicious min value: {col_min}")

    return len(errors) == 0, errors


def check_data_discrepancies(
    data_dir: Path,
) -> Dict[str, any]:
    """
    Check for discrepancies between related datasets.

    Specifically checks:
    - diseases_master vs disease_vectors_3d count mismatch
    - Overlapping and unique ICD codes between datasets

    Args:
        data_dir: Directory containing the CSV files

    Returns:
        Dictionary with discrepancy report
    """
    logger.info("Checking data discrepancies between datasets...")

    discrepancies = {
        "diseases_master_count": 0,
        "disease_vectors_3d_count": 0,
        "overlap_count": 0,
        "only_in_master": [],
        "only_in_vectors": [],
        "issues": [],
    }

    try:
        # Load the datasets
        diseases_master_path = data_dir / "diseases_master.csv"
        disease_vectors_path = data_dir / "disease_vectors_3d.csv"

        if not diseases_master_path.exists() or not disease_vectors_path.exists():
            discrepancies["issues"].append(
                "Cannot check discrepancies - one or both files missing"
            )
            return discrepancies

        df_master = pd.read_csv(diseases_master_path)
        df_vectors = pd.read_csv(disease_vectors_path)

        # Get ICD code sets
        master_codes = set(df_master["icd_code"].dropna().astype(str))
        vector_codes = set(df_vectors["icd_code"].dropna().astype(str))

        discrepancies["diseases_master_count"] = len(master_codes)
        discrepancies["disease_vectors_3d_count"] = len(vector_codes)

        # Find overlaps and differences
        overlap = master_codes & vector_codes
        only_in_master = master_codes - vector_codes
        only_in_vectors = vector_codes - master_codes

        discrepancies["overlap_count"] = len(overlap)
        discrepancies["only_in_master"] = sorted(list(only_in_master))
        discrepancies["only_in_vectors"] = sorted(list(only_in_vectors))

        # Report issues
        if only_in_master:
            discrepancies["issues"].append(
                f"{len(only_in_master)} codes in diseases_master but not in disease_vectors_3d"
            )
        if only_in_vectors:
            discrepancies["issues"].append(
                f"{len(only_in_vectors)} codes in disease_vectors_3d but not in diseases_master"
            )

        logger.info(
            f"Data discrepancy check complete: {len(master_codes)} in master, "
            f"{len(vector_codes)} in vectors, {len(overlap)} overlap"
        )

    except Exception as e:
        discrepancies["issues"].append(f"Error checking discrepancies: {e}")
        logger.error(f"Error checking discrepancies: {e}")

    return discrepancies


def validate_all_data(data_dir: Path, verbose: bool = False) -> Dict[str, any]:
    """
    Run complete validation on all data files.

    Args:
        data_dir: Directory containing CSV files
        verbose: Whether to print detailed progress

    Returns:
        Validation report dictionary
    """
    report = {
        "valid": True,
        "files_checked": [],
        "files_valid": [],
        "files_invalid": [],
        "errors": [],
        "warnings": [],
        "discrepancies": {},
    }

    logger.info(f"Starting data validation in: {data_dir}")

    # Check each expected file
    for filename, schema in EXPECTED_SCHEMAS.items():
        file_path = data_dir / filename

        if verbose:
            logger.info(f"Validating {filename}...")

        # Check file exists
        exists, error = validate_file_exists(file_path)
        if not exists:
            report["valid"] = False
            report["files_invalid"].append(filename)
            report["errors"].append(f"{filename}: {error}")
            logger.error(f"Validation failed for {filename}: {error}")
            continue

        # Try to read CSV
        try:
            df = pd.read_csv(file_path)
            report["files_checked"].append(filename)
        except Exception as e:
            report["valid"] = False
            report["files_invalid"].append(filename)
            report["errors"].append(f"{filename}: Cannot read CSV - {e}")
            logger.error(f"Cannot read {filename}: {e}")
            continue

        # Validate structure
        is_valid, errors = validate_csv_structure(df, filename, schema)

        if is_valid:
            report["files_valid"].append(filename)
            if verbose:
                logger.info(f"✓ {filename}: Valid ({len(df)} rows)")
        else:
            report["valid"] = False
            report["files_invalid"].append(filename)
            for error in errors:
                report["errors"].append(f"{filename}: {error}")
            logger.error(f"Validation failed for {filename}: {errors}")

    # Check for data discrepancies
    report["discrepancies"] = check_data_discrepancies(data_dir)

    # Overall summary
    logger.info(
        f"Validation complete: {len(report['files_valid'])} valid, "
        f"{len(report['files_invalid'])} invalid"
    )

    return report


def print_validation_report(report: Dict[str, any]) -> None:
    """
    Print formatted validation report to console.

    Args:
        report: Validation report dictionary
    """
    print("\n" + "=" * 60)
    print("DATA VALIDATION REPORT")
    print("=" * 60)

    # Overall status
    if report["valid"]:
        print("\n✓ Overall Status: PASSED")
    else:
        print("\n✗ Overall Status: FAILED")

    # File summary
    print(f"\nFiles Checked: {len(report['files_checked'])}")
    print(f"Valid: {len(report['files_valid'])}")
    print(f"Invalid: {len(report['files_invalid'])}")

    # List valid files
    if report["files_valid"]:
        print("\n✓ Valid Files:")
        for f in report["files_valid"]:
            print(f"  - {f}")

    # List invalid files with errors
    if report["files_invalid"]:
        print("\n✗ Invalid Files:")
        for f in report["files_invalid"]:
            print(f"  - {f}")

    # List all errors
    if report["errors"]:
        print("\nErrors:")
        for error in report["errors"]:
            print(f"  • {error}")

    # Data discrepancies
    discrepancies = report.get("discrepancies", {})
    if discrepancies:
        print("\n" + "-" * 60)
        print("DATA DISCREPANCY ANALYSIS")
        print("-" * 60)
        print(
            f"diseases_master.csv: {discrepancies.get('diseases_master_count', 0)} codes"
        )
        print(
            f"disease_vectors_3d.csv: {discrepancies.get('disease_vectors_3d_count', 0)} codes"
        )
        print(f"Overlap: {discrepancies.get('overlap_count', 0)} codes")

        only_in_vectors = discrepancies.get("only_in_vectors", [])
        if only_in_vectors:
            print(f"\nCodes only in disease_vectors_3d ({len(only_in_vectors)}):")
            # Show first 10, summarize rest
            for code in only_in_vectors[:10]:
                print(f"  - {code}")
            if len(only_in_vectors) > 10:
                print(f"  ... and {len(only_in_vectors) - 10} more")

        if discrepancies.get("issues"):
            print("\nDiscrepancy Issues:")
            for issue in discrepancies["issues"]:
                print(f"  ⚠ {issue}")

    print("\n" + "=" * 60)


def main():
    """Main entry point for validation script."""
    parser = argparse.ArgumentParser(
        description="Validate Disease-Relater data files before database import"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="Data/processed",
        help="Directory containing CSV files (default: Data/processed)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--exit-on-error",
        action="store_true",
        help="Exit with non-zero code if validation fails",
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run validation
    data_dir = Path(args.data_dir)
    report = validate_all_data(data_dir, verbose=args.verbose)

    # Print report
    print_validation_report(report)

    # Exit with appropriate code
    if args.exit_on_error and not report["valid"]:
        sys.exit(1)

    return report


if __name__ == "__main__":
    main()
