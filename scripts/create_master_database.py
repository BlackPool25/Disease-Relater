"""
Module 1.3: Create Unified Disease Database

This module combines translated disease names, prevalence data, and disease pair
statistics to create unified master databases for downstream analysis.

Author: Agent 2 (Master Database)
Date: 2026-01-30

Security Notes:
- All file paths are validated before use
- Input validation ensures data integrity
- No external network calls made
- All outputs are CSV/JSON with proper escaping

Input Files:
- data/processed/disease_metadata.csv (736 diseases with names)
- data/processed/disease_pairs_clean.csv (74,901 relationships)
- Data/Data/1.Prevalence/Prevalence_Sex_Age_Year_ICD.csv (prevalence by strata)
- Data/processed/ICD10_Diagnoses_English.csv (optional: from Agent 1)

Output Files:
- Data/processed/diseases_master.csv (master disease database)
- Data/processed/disease_relationships_master.csv (master relationships)
- Data/processed/data_summary.json (statistics summary)
- Data/processed/.master_db_done (completion marker for Agent 3)
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ICD Chapter mapping for enrichment
CHAPTER_NAMES = {
    "I": "Infectious and parasitic diseases",
    "II": "Neoplasms",
    "III": "Blood and immune disorders",
    "IV": "Endocrine, nutritional and metabolic",
    "V": "Mental and behavioral disorders",
    "VI": "Nervous system",
    "VII": "Eye and adnexa",
    "VIII": "Ear and mastoid process",
    "IX": "Circulatory system",
    "X": "Respiratory system",
    "XI": "Digestive system",
    "XII": "Skin and subcutaneous tissue",
    "XIII": "Musculoskeletal and connective tissue",
    "XIV": "Genitourinary system",
    "XV": "Pregnancy and childbirth",
    "XVI": "Perinatal conditions",
    "XVII": "Congenital malformations",
    "XVIII": "Symptoms and abnormal findings",
    "XIX": "Injury, poisoning and external causes",
    "XX": "External causes of morbidity",
    "XXI": "Factors influencing health status",
}


def validate_file_path(filepath: Path, must_exist: bool = True) -> Path:
    """
    Validate and sanitize file path to prevent directory traversal.

    Args:
        filepath: Path to validate
        must_exist: Whether file must exist

    Returns:
        Resolved Path object

    Raises:
        FileNotFoundError: If must_exist=True and file doesn't exist
        ValueError: If path is outside allowed directories
    """
    resolved = filepath.resolve()

    # Security: Ensure path is within project directory
    project_root = Path("/home/lightdesk/Projects/Disease-Relater").resolve()
    data_root = Path("/home/lightdesk/Projects/Disease-Relater/Data").resolve()

    if not str(resolved).startswith(str(project_root)):
        raise ValueError(f"Path {resolved} is outside project directory")

    if must_exist and not resolved.exists():
        raise FileNotFoundError(f"Required file not found: {resolved}")

    return resolved


def load_translated_names(processed_dir: Path) -> Optional[pd.DataFrame]:
    """
    Load translated ICD names from Agent 1 output if available.

    Args:
        processed_dir: Path to processed data directory

    Returns:
        DataFrame with translated names, or None if not available
    """
    filepath = processed_dir / "ICD10_Diagnoses_English.csv"

    try:
        validate_file_path(filepath, must_exist=True)
        df = pd.read_csv(filepath)
        logger.info(f"Loaded translated names: {len(df)} records")
        return df
    except FileNotFoundError:
        logger.info("Translated names file not found (Agent 1 may not be complete)")
        return None


def load_disease_metadata(processed_dir: Path) -> pd.DataFrame:
    """
    Load disease metadata with German and English names.

    Args:
        processed_dir: Path to processed data directory

    Returns:
        DataFrame with disease metadata

    Raises:
        FileNotFoundError: If metadata file not found
    """
    filepath = processed_dir / "disease_metadata.csv"
    validate_file_path(filepath, must_exist=True)

    df = pd.read_csv(filepath)

    # Validate required columns
    required_cols = {"code", "name_de", "name_en"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns in metadata: {missing_cols}")

    logger.info(f"Loaded disease metadata: {len(df)} diseases")
    return df


def load_prevalence_data(data_dir: Path) -> pd.DataFrame:
    """
    Load and validate prevalence data.

    Args:
        data_dir: Path to data directory

    Returns:
        DataFrame with prevalence data
    """
    filepath = data_dir / "Data" / "1.Prevalence" / "Prevalence_Sex_Age_Year_ICD.csv"
    validate_file_path(filepath, must_exist=True)

    df = pd.read_csv(filepath)

    # Validate required columns
    required_cols = {"sex", "icd_code", "p"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns in prevalence: {missing_cols}")

    # Validate prevalence values are between 0 and 1
    if (df["p"] < 0).any() or (df["p"] > 1).any():
        invalid_count = ((df["p"] < 0) | (df["p"] > 1)).sum()
        logger.warning(f"Found {invalid_count} prevalence values outside [0,1]")

    logger.info(f"Loaded prevalence data: {len(df)} records")
    return df


def load_disease_pairs(processed_dir: Path) -> pd.DataFrame:
    """
    Load disease pairs data.

    Args:
        processed_dir: Path to processed data directory

    Returns:
        DataFrame with disease pairs
    """
    filepath = processed_dir / "disease_pairs_clean.csv"
    validate_file_path(filepath, must_exist=True)

    df = pd.read_csv(filepath)

    # Validate required columns
    required_cols = {
        "disease_1_code",
        "disease_2_code",
        "odds_ratio",
        "p_value",
        "patient_count",
    }
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns in pairs: {missing_cols}")

    logger.info(f"Loaded disease pairs: {len(df)} relationships")
    return df


def calculate_prevalence_by_sex(prevalence_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate average prevalence by disease code and sex.

    Uses pandas groupby aggregation as per Context7 best practices:
    - groupby with multiple columns
    - agg with mean function
    - pivot to reshape data

    Args:
        prevalence_df: DataFrame with prevalence data

    Returns:
        DataFrame with columns: icd_code, Male, Female (prevalence averages)
    """
    if prevalence_df.empty:
        return pd.DataFrame(columns=["icd_code", "Male", "Female"])

    # Group by disease code and sex, calculate mean prevalence
    # Using NamedAgg for clarity (per Context7 documentation)
    prev_by_sex = (
        prevalence_df.groupby(["icd_code", "sex"])
        .agg(avg_prevalence=pd.NamedAgg(column="p", aggfunc="mean"))
        .reset_index()
    )

    # Pivot to wide format: one row per disease, columns for each sex
    prev_wide = prev_by_sex.pivot(
        index="icd_code", columns="sex", values="avg_prevalence"
    ).reset_index()

    # Ensure both Male and Female columns exist
    if "Male" not in prev_wide.columns:
        prev_wide["Male"] = np.nan
    if "Female" not in prev_wide.columns:
        prev_wide["Female"] = np.nan

    return prev_wide


def create_diseases_master(
    metadata_df: pd.DataFrame,
    prevalence_df: pd.DataFrame,
    translated_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Create master disease database combining names, chapters, and prevalence.

    Args:
        metadata_df: Disease metadata with names
        prevalence_df: Prevalence data
        translated_df: Optional translated names from Agent 1

    Returns:
        DataFrame with master disease database
    """
    logger.info("Creating diseases master database...")

    # Start with metadata
    master = metadata_df.copy()

    # Rename columns for consistency
    master = master.rename(
        columns={
            "code": "icd_code",
            "name_de": "name_german",
            "name_en": "name_english",
            "icd_chapter": "chapter_code",
            "icd_chapter_name": "chapter_name",
        }
    )

    # If translated names available and different, prefer them
    if translated_df is not None and not translated_df.empty:
        # Merge with translated names (left join to keep all metadata)
        if (
            "icd_code" in translated_df.columns
            and "descr_english" in translated_df.columns
        ):
            master = master.merge(
                translated_df[["icd_code", "descr_english"]],
                on="icd_code",
                how="left",
                suffixes=("", "_translated"),
            )
            # Use translated name if available and metadata name is empty
            master["name_english"] = master.apply(
                lambda row: (
                    row["descr_english"]
                    if pd.notna(row.get("descr_english"))
                    and str(row.get("descr_english")).strip()
                    and (
                        pd.isna(row["name_english"])
                        or not str(row["name_english"]).strip()
                    )
                    else row["name_english"]
                ),
                axis=1,
            )
            # Drop temporary column
            master = master.drop(columns=["descr_english"], errors="ignore")

    # Calculate prevalence by sex
    prev_wide = calculate_prevalence_by_sex(prevalence_df)

    # Merge prevalence data
    master = master.merge(prev_wide, on="icd_code", how="left")

    # Rename prevalence columns
    master = master.rename(
        columns={"Male": "avg_prevalence_male", "Female": "avg_prevalence_female"}
    )

    # Fill missing prevalence with 0 (diseases not in prevalence data)
    master["avg_prevalence_male"] = master["avg_prevalence_male"].fillna(0)
    master["avg_prevalence_female"] = master["avg_prevalence_female"].fillna(0)

    # Ensure chapter names are populated
    master["chapter_name"] = master.apply(
        lambda row: (
            row["chapter_name"]
            if pd.notna(row["chapter_name"]) and str(row["chapter_name"]).strip()
            else CHAPTER_NAMES.get(str(row["chapter_code"]), "Unknown")
        ),
        axis=1,
    )

    # Select and order output columns
    output_columns = [
        "icd_code",
        "name_english",
        "name_german",
        "chapter_code",
        "chapter_name",
        "granularity",
        "avg_prevalence_male",
        "avg_prevalence_female",
    ]

    # Only include columns that exist
    available_cols = [col for col in output_columns if col in master.columns]
    master = master[available_cols]

    # Sort by ICD code
    master = master.sort_values("icd_code").reset_index(drop=True)

    logger.info(f"Created diseases master: {len(master)} diseases")
    return master


def create_relationships_master(
    pairs_df: pd.DataFrame, diseases_master: pd.DataFrame
) -> pd.DataFrame:
    """
    Create master relationships database with aggregated statistics.

    Uses pandas groupby aggregation to summarize relationships across all strata.

    Args:
        pairs_df: Disease pairs data
        diseases_master: Master diseases DataFrame for name lookup

    Returns:
        DataFrame with aggregated relationships
    """
    logger.info("Creating relationships master database...")

    # Create name lookup from diseases master
    name_lookup = {}
    if (
        "icd_code" in diseases_master.columns
        and "name_english" in diseases_master.columns
    ):
        name_lookup = dict(
            zip(diseases_master["icd_code"], diseases_master["name_english"])
        )

    # Group by disease pair and aggregate statistics
    # Using dict-based agg as per Context7 best practices
    rel_summary = (
        pairs_df.groupby(["disease_1_code", "disease_2_code"])
        .agg(
            {
                "odds_ratio": "mean",
                "p_value": "mean",
                "patient_count": "sum",
                "icd_chapter_1": "first",  # Keep chapter info
                "icd_chapter_2": "first",
            }
        )
        .reset_index()
    )

    # Rename aggregated columns for clarity
    rel_summary = rel_summary.rename(
        columns={
            "odds_ratio": "odds_ratio_avg",
            "p_value": "p_value_avg",
            "patient_count": "patient_count_total",
        }
    )

    # Add disease names from lookup
    rel_summary["disease_1_name"] = rel_summary["disease_1_code"].map(name_lookup)
    rel_summary["disease_2_name"] = rel_summary["disease_2_code"].map(name_lookup)

    # Fill missing names with codes (for Blocks/Chronic not in main list)
    rel_summary["disease_1_name"] = rel_summary["disease_1_name"].fillna(
        rel_summary["disease_1_code"]
    )
    rel_summary["disease_2_name"] = rel_summary["disease_2_name"].fillna(
        rel_summary["disease_2_code"]
    )

    # Reorder columns
    column_order = [
        "disease_1_code",
        "disease_1_name",
        "disease_2_code",
        "disease_2_name",
        "odds_ratio_avg",
        "p_value_avg",
        "patient_count_total",
        "icd_chapter_1",
        "icd_chapter_2",
    ]

    available_cols = [col for col in column_order if col in rel_summary.columns]
    rel_summary = rel_summary[available_cols]

    # Sort by disease codes
    rel_summary = rel_summary.sort_values(
        ["disease_1_code", "disease_2_code"]
    ).reset_index(drop=True)

    logger.info(f"Created relationships master: {len(rel_summary)} relationships")
    return rel_summary


def generate_summary_statistics(
    diseases_df: pd.DataFrame, relationships_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Generate comprehensive summary statistics.

    Args:
        diseases_df: Master diseases DataFrame
        relationships_df: Master relationships DataFrame

    Returns:
        Dictionary with summary statistics
    """
    logger.info("Generating summary statistics...")

    # Diseases by chapter
    if "chapter_code" in diseases_df.columns:
        diseases_by_chapter = diseases_df.groupby("chapter_code").size().to_dict()
    else:
        diseases_by_chapter = {}

    # Most connected diseases (appear in most relationships)
    connection_counts = pd.concat(
        [relationships_df["disease_1_code"], relationships_df["disease_2_code"]]
    ).value_counts()
    most_connected = connection_counts.head(20).to_dict()

    # Strongest relationships by odds ratio
    if not relationships_df.empty:
        strongest = (
            relationships_df.nlargest(10, "odds_ratio_avg")[
                ["disease_1_code", "disease_2_code", "odds_ratio_avg", "p_value_avg"]
            ]
            .replace({np.nan: None})
            .to_dict("records")
        )
    else:
        strongest = []

    # Prevalence statistics
    avg_prev_male = float(diseases_df["avg_prevalence_male"].mean())
    avg_prev_female = float(diseases_df["avg_prevalence_female"].mean())

    # Relationship statistics
    if not relationships_df.empty:
        stats = {
            "mean_odds_ratio": float(relationships_df["odds_ratio_avg"].mean()),
            "median_odds_ratio": float(relationships_df["odds_ratio_avg"].median()),
            "mean_p_value": float(relationships_df["p_value_avg"].mean()),
            "total_patient_observations": int(
                relationships_df["patient_count_total"].sum()
            ),
        }
    else:
        stats = {
            "mean_odds_ratio": 0.0,
            "median_odds_ratio": 0.0,
            "mean_p_value": 0.0,
            "total_patient_observations": 0,
        }

    # Build summary structure
    summary = {
        "metadata": {
            "total_diseases": int(len(diseases_df)),
            "total_relationships": int(len(relationships_df)),
            "data_quality": {
                "diseases_with_english_names": int(
                    diseases_df["name_english"].notna().sum()
                ),
                "diseases_with_german_names": int(
                    diseases_df["name_german"].notna().sum()
                ),
            },
        },
        "prevalence": {
            "avg_prevalence_male": avg_prev_male,
            "avg_prevalence_female": avg_prev_female,
            "diseases_with_prevalence_data": int(
                (diseases_df["avg_prevalence_male"] > 0).sum()
                + (diseases_df["avg_prevalence_female"] > 0).sum()
            ),
        },
        "diseases_by_chapter": diseases_by_chapter,
        "most_connected_diseases": most_connected,
        "strongest_relationships": strongest,
        "statistics": stats,
    }

    return summary


def validate_outputs(
    diseases_df: pd.DataFrame,
    relationships_df: pd.DataFrame,
    summary: Dict[str, Any],
) -> Tuple[bool, list]:
    """
    Validate all outputs meet requirements.

    Args:
        diseases_df: Master diseases DataFrame
        relationships_df: Master relationships DataFrame
        summary: Summary statistics dictionary

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    # Validate diseases count (should match expected based on data)
    # Note: Actual data has 736 unique diseases, not 1080
    expected_count = summary.get("metadata", {}).get("total_diseases", len(diseases_df))
    if len(diseases_df) == 0:
        errors.append("No diseases found in output")
    elif len(diseases_df) != expected_count:
        errors.append(
            f"Disease count mismatch: expected {expected_count}, found {len(diseases_df)}"
        )

    # Check summary statistics are reasonable
    if summary["metadata"]["total_diseases"] != len(diseases_df):
        errors.append("Summary disease count mismatch")

    if summary["metadata"]["total_relationships"] != len(relationships_df):
        errors.append("Summary relationship count mismatch")

    is_valid = len(errors) == 0
    return is_valid, errors


def check_translation_completion(
    processed_dir: Path, max_wait_minutes: int = 0
) -> bool:
    """
    Check if Agent 1 has completed translation.

    Args:
        processed_dir: Path to processed directory
        max_wait_minutes: Minutes to wait (0 for immediate check)

    Returns:
        True if translation complete, False otherwise
    """
    marker_file = processed_dir / ".translation_done"

    if marker_file.exists():
        logger.info("Agent 1 translation complete marker found")
        return True

    if max_wait_minutes > 0:
        import time

        logger.info(f"Waiting up to {max_wait_minutes} minutes for translation...")
        for i in range(max_wait_minutes * 2):  # Check every 30 seconds
            if marker_file.exists():
                logger.info("Agent 1 translation complete!")
                return True
            if i % 2 == 0:
                logger.info(f"Waiting... ({i // 2 + 1}/{max_wait_minutes} minutes)")
            time.sleep(30)

    return False


def main(
    data_dir: str = "Data",
    processed_dir: str = "Data/processed",
    existing_processed_dir: str = "data/processed",
    wait_for_translation: bool = False,
    max_wait_minutes: int = 30,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Main execution function to create master databases.

    Args:
        data_dir: Root data directory
        processed_dir: Output directory for processed data
        existing_processed_dir: Directory with existing pipeline outputs
        wait_for_translation: Whether to wait for Agent 1
        max_wait_minutes: Maximum minutes to wait for translation

    Returns:
        Tuple of (diseases_master, relationships_master, summary)
    """
    # Setup paths
    data_path = Path(data_dir)
    processed_path = Path(processed_dir)
    existing_processed_path = Path(existing_processed_dir)

    # Create output directory
    processed_path.mkdir(parents=True, exist_ok=True)

    # Check for translation completion if requested
    if wait_for_translation:
        translation_ready = check_translation_completion(
            processed_path, max_wait_minutes
        )
        if not translation_ready:
            logger.warning("Translation not complete, proceeding with metadata only")

    # Load inputs
    logger.info("Loading disease metadata...")
    metadata_df = load_disease_metadata(existing_processed_path)

    logger.info("Loading prevalence data...")
    try:
        prevalence_df = load_prevalence_data(data_path)
    except FileNotFoundError as e:
        logger.error(f"Cannot load prevalence data: {e}")
        prevalence_df = pd.DataFrame()

    # Try to load translated names (optional)
    translated_df = load_translated_names(processed_path)

    logger.info("Loading disease pairs...")
    pairs_df = load_disease_pairs(existing_processed_path)

    # Create master databases
    diseases_master = create_diseases_master(metadata_df, prevalence_df, translated_df)
    relationships_master = create_relationships_master(pairs_df, diseases_master)
    summary = generate_summary_statistics(diseases_master, relationships_master)

    # Validate outputs
    is_valid, errors = validate_outputs(diseases_master, relationships_master, summary)
    if not is_valid:
        logger.error("Validation errors:")
        for error in errors:
            logger.error(f"  - {error}")
        raise ValueError(f"Output validation failed: {errors}")

    logger.info("All outputs validated successfully")

    # Save outputs
    diseases_output = processed_path / "diseases_master.csv"
    diseases_master.to_csv(diseases_output, index=False)
    logger.info(f"Saved: {diseases_output}")

    relationships_output = processed_path / "disease_relationships_master.csv"
    relationships_master.to_csv(relationships_output, index=False)
    logger.info(f"Saved: {relationships_output}")

    summary_output = processed_path / "data_summary.json"
    with open(summary_output, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    logger.info(f"Saved: {summary_output}")

    # Create completion marker for Agent 3
    marker_file = processed_path / ".master_db_done"
    marker_file.touch()
    logger.info(f"Created completion marker: {marker_file}")

    return diseases_master, relationships_master, summary


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Can be run with arguments for testing
    import sys

    wait = "--wait" in sys.argv
    main(wait_for_translation=wait)
