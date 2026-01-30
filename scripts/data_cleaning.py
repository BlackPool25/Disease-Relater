"""
Data Cleaning Pipeline for Austrian Comorbidity Networks
Processes 82 stratified adjacency matrices into cleaned edge-list format.

This module provides functions for:
- Loading adjacency matrices from CSV files
- Extracting p-values and counts from R .rds contingency tables
- Converting matrices to edge-list format
- ICD chapter mapping and disease name translation
- Merging all stratified datasets
- Generating output files and validation reports
"""

import os
import re
import glob
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

import numpy as np
import pandas as pd
import pyreadr

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ICD-10 Chapter Mapping (German)
ICD_CHAPTERS_DE = {
    "A": ("I", "Infektionskrankheiten und durch Parasiten übertragene Krankheiten"),
    "B": ("I", "Infektionskrankheiten und durch Parasiten übertragene Krankheiten"),
    "C": ("II", "Neubildungen"),
    "D00-D48": ("II", "Neubildungen"),
    "D50-D89": (
        "III",
        "Krankheiten des Blutes und der blutbildenden Organe sowie bestimmte Störungen",
    ),
    "E": ("IV", "Endokrine, Ernährungs- und Stoffwechselkrankheiten"),
    "F": ("V", "Psychische und Verhaltensstörungen"),
    "G": ("VI", "Krankheiten des Nervensystems"),
    "H00-H59": ("VII", "Krankheiten des Auges und der Augenanhangsgebilde"),
    "H60-H95": ("VIII", "Krankheiten des Ohres und des Warzenfortsatzes"),
    "I": ("IX", "Krankheiten des Kreislaufsystems"),
    "J": ("X", "Krankheiten des Atmungssystems"),
    "K": ("XI", "Krankheiten des Verdauungssystems"),
    "L": ("XII", "Krankheiten der Haut und der Unterhaut"),
    "M": ("XIII", "Krankheiten des Muskel-Skelett-Systems und des Bindegewebes"),
    "N": ("XIV", "Krankheiten des Urogenitalsystems"),
    "O": ("XV", "Schwangerschaft, Geburt und Wochenbett"),
    "P": (
        "XVI",
        "Bestimmte Zustände, die ihren Ursprung in der Perinatalperiode haben",
    ),
    "Q": ("XVII", "Angeborene Fehlbildungen, Deformitäten und chromosomale Anomalien"),
    "R": (
        "XVIII",
        "Symptome und abnorme klinische und Laborbefunde, die nicht anderweitig klassifiziert sind",
    ),
    "S": (
        "XIX",
        "Verletzungen, Vergiftungen und bestimmte andere Folgen äußerer Ursachen",
    ),
    "T": (
        "XIX",
        "Verletzungen, Vergiftungen und bestimmte andere Folgen äußerer Ursachen",
    ),
    "V": ("XX", "Äußere Ursachen von Morbidität und Mortalität"),
    "W": ("XX", "Äußere Ursachen von Morbidität und Mortalität"),
    "X": ("XX", "Äußere Ursachen von Morbidität und Mortalität"),
    "Y": ("XX", "Äußere Ursachen von Morbidität und Mortalität"),
    "Z": ("XXI", "Gesundheitszustände und Kontakt mit den Gesundheitsdiensten"),
}

# ICD-10 Chapter Mapping (English translations)
ICD_CHAPTERS_EN = {
    "I": "Infectious and parasitic diseases",
    "II": "Neoplasms",
    "III": "Diseases of the blood and blood-forming organs",
    "IV": "Endocrine, nutritional and metabolic diseases",
    "V": "Mental and behavioural disorders",
    "VI": "Diseases of the nervous system",
    "VII": "Diseases of the eye and adnexa",
    "VIII": "Diseases of the ear and mastoid process",
    "IX": "Diseases of the circulatory system",
    "X": "Diseases of the respiratory system",
    "XI": "Diseases of the digestive system",
    "XII": "Diseases of the skin and subcutaneous tissue",
    "XIII": "Diseases of the musculoskeletal system and connective tissue",
    "XIV": "Diseases of the genitourinary system",
    "XV": "Pregnancy, childbirth and the puerperium",
    "XVI": "Certain conditions originating in the perinatal period",
    "XVII": "Congenital malformations, deformations and chromosomal abnormalities",
    "XVIII": "Symptoms, signs and abnormal clinical and laboratory findings",
    "XIX": "Injury, poisoning and certain other consequences of external causes",
    "XX": "External causes of morbidity and mortality",
    "XXI": "Factors influencing health status and contact with health services",
}

# Granularity configuration
# These column names correspond to the actual CSV file structures:
# ICD10_Diagnoses_All.csv: diagnose_id, icd_code, descr
# Blocks_All.csv: block_id, block_name, icd_code
# Chronic_All.csv: id, label, class, icd_code
GRANULARITY_CONFIG = {
    "ICD": {"size": 1080, "code_col": "icd_code", "name_col": "descr"},
    "Blocks": {"size": 131, "code_col": "block_name", "name_col": "block_name"},
    "Chronic": {"size": 46, "code_col": "label", "name_col": "label"},
}


@dataclass
class FileStratification:
    """Data class to hold stratification info extracted from filename."""

    sex: str
    granularity: str
    stratum_type: str  # 'year' or 'age'
    stratum_value: str  # e.g., '2003-2004' or '5'
    filename: str


def get_icd_chapter(code: str) -> Tuple[str, str]:
    """
    Determine ICD-10 chapter from disease code.

    Args:
        code: ICD-10 code (e.g., 'C15', 'D34', 'E11')

    Returns:
        Tuple of (chapter_number, chapter_name)
    """
    if not code or not isinstance(code, str):
        return ("", "")

    first_char = code[0].upper()

    # Handle special ranges for D codes
    if first_char == "D":
        match = re.search(r"\d+", code)
        if match:
            try:
                num = int(match.group())
                if 0 <= num <= 48:
                    chapter_info = ICD_CHAPTERS_DE.get("D00-D48", ("", ""))
                else:
                    chapter_info = ICD_CHAPTERS_DE.get("D50-D89", ("", ""))
            except ValueError:
                chapter_info = ("", "")
        else:
            chapter_info = ("", "")
    # Handle H codes with range
    elif first_char == "H":
        match = re.search(r"\d+", code)
        if match:
            try:
                num = int(match.group())
                if 0 <= num <= 59:
                    chapter_info = ICD_CHAPTERS_DE.get("H00-H59", ("", ""))
                else:
                    chapter_info = ICD_CHAPTERS_DE.get("H60-H95", ("", ""))
            except ValueError:
                chapter_info = ICD_CHAPTERS_DE.get(first_char, ("", ""))
        else:
            chapter_info = ICD_CHAPTERS_DE.get(first_char, ("", ""))
    else:
        chapter_info = ICD_CHAPTERS_DE.get(first_char, ("", ""))

    chapter_num = chapter_info[0]
    chapter_name = ICD_CHAPTERS_EN.get(chapter_num, "")

    return (chapter_num, chapter_name)


def translate_german_to_english(texts: List[str], batch_size: int = 50) -> List[str]:
    """
    Translate German disease names to English.

    Args:
        texts: List of German text strings to translate
        batch_size: Number of texts to translate per batch

    Returns:
        List of translated English strings
    """
    try:
        from deep_translator import GoogleTranslator

        translator = GoogleTranslator(source="de", target="en")

        translated = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            # Translate each text individually with rate limiting
            for text in batch:
                try:
                    if text and isinstance(text, str):
                        translation = translator.translate(text)
                        translated.append(translation)
                    else:
                        translated.append("")
                except Exception as e:
                    logger.warning(f"Translation failed for '{text}': {e}")
                    translated.append(text)  # Keep original on failure

        return translated
    except ImportError:
        logger.warning("deep-translator not installed. Returning German names.")
        return texts


def parse_filename_stratification(filename: str) -> FileStratification:
    """
    Parse stratification info from adjacency matrix filename.

    Args:
        filename: Adj_Matrix_{sex}_{granularity}_{stratum_type}_{stratum_value}.csv

    Returns:
        FileStratification object with parsed values
    """
    # Pattern: Adj_Matrix_{sex}_{granularity}_{stratum_type}_{stratum_value}.csv
    pattern = (
        r"Adj_Matrix_(Male|Female|Both)_(ICD|Blocks|Chronic)_(year|age)_([\d\-]+)\.csv"
    )
    match = re.match(pattern, filename)

    if match:
        return FileStratification(
            sex=match.group(1),
            granularity=match.group(2),
            stratum_type=match.group(3),
            stratum_value=match.group(4),
            filename=filename,
        )
    else:
        # Try alternative pattern matching
        parts = filename.replace(".csv", "").split("_")
        if len(parts) >= 5:
            return FileStratification(
                sex=parts[2] if len(parts) > 2 else "Unknown",
                granularity=parts[3] if len(parts) > 3 else "Unknown",
                stratum_type=parts[4] if len(parts) > 4 else "Unknown",
                stratum_value="_".join(parts[5:]) if len(parts) > 5 else "Unknown",
                filename=filename,
            )
        else:
            raise ValueError(f"Could not parse filename: {filename}")


def load_mapping(granularity: str, mapping_dir: Optional[str] = None) -> pd.DataFrame:
    """
    Load disease code mapping file.

    Args:
        granularity: 'ICD', 'Blocks', or 'Chronic'
        mapping_dir: Directory containing mapping files

    Returns:
        DataFrame with code mappings
    """
    if mapping_dir is None:
        mapping_dir = str(Path(__file__).parent.parent)

    config = GRANULARITY_CONFIG.get(granularity)
    if not config:
        raise ValueError(f"Unknown granularity: {granularity}")

    if granularity == "ICD":
        filepath = os.path.join(mapping_dir, "ICD10_Diagnoses_All.csv")
    elif granularity == "Blocks":
        filepath = os.path.join(mapping_dir, "Blocks_All.csv")
    else:  # Chronic
        filepath = os.path.join(mapping_dir, "Chronic_All.csv")

    if os.path.exists(filepath):
        df = pd.read_csv(filepath)

        # For Blocks, the CSV has multiple rows per block (one per ICD code)
        # We need to extract unique blocks only
        if granularity == "Blocks":
            # Get unique blocks maintaining order
            df = df.drop_duplicates(subset=[config["code_col"]], keep="first")
            # Reset index to ensure proper alignment with matrix (0-130)
            df = df.reset_index(drop=True)

        logger.info(f"Loaded {granularity} mapping: {len(df)} rows")
        return df
    else:
        logger.warning(f"Mapping file not found: {filepath}")
        # Create dummy mapping if file not found
        size = config["size"]
        return pd.DataFrame(
            {
                config["code_col"]: [f"CODE_{i}" for i in range(size)],
                config["name_col"]: [f"Disease_{i}" for i in range(size)],
            }
        )


def load_adjacency_matrix(filepath: str, size: int) -> np.ndarray:
    """
    Load adjacency matrix from space-separated CSV.

    Args:
        filepath: Path to CSV file
        size: Expected matrix size (1080, 131, or 46)

    Returns:
        NumPy array of shape (size, size)
    """
    try:
        matrix = np.loadtxt(filepath, delimiter=" ")

        if matrix.shape != (size, size):
            logger.warning(
                f"Matrix shape mismatch: expected ({size}, {size}), got {matrix.shape}"
            )
            # Try to reshape or pad
            if matrix.shape[0] == size:
                matrix = matrix[:size, :size]

        return matrix
    except Exception as e:
        logger.error(f"Failed to load matrix from {filepath}: {e}")
        return np.zeros((size, size))


def extract_pvalues_from_csv(
    export_dir: str,
    granularity: str,
    sex: str,
    stratum_type: str,
    stratum_value: str,
    size: int,
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Extract p-values, counts, and odds ratios from exported CSV files.

    The R export script creates CSV files for each stratification with:
    - p-values (Mantel-Haenszel or Fisher's exact test)
    - counts (total patient cases)
    - odds ratios

    Args:
        export_dir: Directory containing exported CSV files
        granularity: 'ICD', 'Blocks', or 'Chronic'
        sex: 'Male' or 'Female'
        stratum_type: 'year' or 'age'
        stratum_value: e.g., '2003-2004' or '5'
        size: Expected matrix size

    Returns:
        Tuple of (odds_ratio_matrix, pvalue_matrix, count_matrix) or (None, None, None) on failure
    """
    # Construct base filename matching R export pattern
    # Pattern: {Granularity}_ContingencyTables_{sex}_{stratum_type}_{stratum_value}
    base_name = f"{granularity}_ContingencyTables_{sex}_{stratum_type}_{stratum_value}"

    pvalue_file = os.path.join(export_dir, f"{base_name}_pvalues.csv")
    count_file = os.path.join(export_dir, f"{base_name}_counts.csv")
    or_file = os.path.join(export_dir, f"{base_name}_odds_ratios.csv")

    # Check if files exist
    if not os.path.exists(pvalue_file):
        logger.warning(f"P-value file not found: {pvalue_file}")
        return None, None, None

    if not os.path.exists(count_file):
        logger.warning(f"Count file not found: {count_file}")
        return None, None, None

    try:
        # Load matrices from CSV files
        pvalues = np.loadtxt(pvalue_file, delimiter=",")
        counts = np.loadtxt(count_file, delimiter=",")

        # Load odds ratios if available, otherwise compute from adjacency matrix
        if os.path.exists(or_file):
            odds_ratios = np.loadtxt(or_file, delimiter=",")
        else:
            odds_ratios = None

        # Validate shapes
        if pvalues.shape != (size, size):
            logger.warning(
                f"P-value matrix shape mismatch: expected ({size}, {size}), got {pvalues.shape}"
            )
            return None, None, None

        if counts.shape != (size, size):
            logger.warning(
                f"Count matrix shape mismatch: expected ({size}, {size}), got {counts.shape}"
            )
            return None, None, None

        logger.info(f"Loaded CSV files for {base_name}")
        logger.info(f"  P-values: {pvalues.shape}")
        logger.info(f"  Counts: {counts.shape}")

        return odds_ratios, pvalues, counts

    except Exception as e:
        logger.error(f"Failed to load CSV files for {base_name}: {e}")
        return None, None, None


def extract_pvalues_from_rds(
    rds_path: str,
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Extract p-values and counts from R contingency table .rds files.

    DEPRECATED: Use extract_pvalues_from_csv() instead.
    This function is kept for backwards compatibility but will fail since
    pyreadr cannot read the complex array structures in these RDS files.

    Args:
        rds_path: Path to .rds file

    Returns:
        Tuple of (odds_ratio_matrix, pvalue_matrix, count_matrix) or (None, None, None) on failure
    """
    logger.warning(
        "extract_pvalues_from_rds() is deprecated. "
        "Please run scripts/export_contingency_tables.R first to generate CSV files."
    )

    try:
        result = pyreadr.read_r(rds_path)

        # The RDS structure typically contains a list of contingency tables
        # Each table is a 2x2 matrix representing disease co-occurrence
        data = list(result.values())[0]

        logger.info(f"Loaded RDS file: {rds_path}")
        logger.info(f"Data type: {type(data)}")

        if isinstance(data, list):
            # Determine matrix size based on data length
            # For a square matrix, size should be sqrt(len(data))
            n = int(np.sqrt(len(data)))

            odds_ratios = np.zeros((n, n))
            p_values = np.zeros((n, n))
            counts = np.zeros((n, n))

            for i, table in enumerate(data):
                if table is not None and len(table) > 0:
                    row = i // n
                    col = i % n

                    # Extract count (total observations)
                    if hasattr(table, "sum"):
                        counts[row, col] = table.sum()

                    # Calculate odds ratio from 2x2 table
                    # Typical structure: [[a, b], [c, d]] where a=both, b=only1, c=only2, d=neither
                    if len(table) == 2 and len(table[0]) == 2:
                        a, b = table[0]
                        c, d = table[1]

                        # Avoid division by zero
                        if b > 0 and c > 0:
                            odds_ratios[row, col] = (a * d) / (b * c)
                        else:
                            odds_ratios[row, col] = 0

            logger.info(f"Extracted matrices of size {n}x{n}")
            return odds_ratios, p_values, counts

        elif isinstance(data, dict):
            # Handle dictionary format
            logger.info(f"RDS contains dictionary with keys: {list(data.keys())}")
            # Try to find matrices in dictionary values
            for key, value in data.items():
                if isinstance(value, np.ndarray) and len(value.shape) == 2:
                    logger.info(f"Found matrix '{key}': shape {value.shape}")
            return None, None, None

        else:
            logger.warning(f"Unexpected data type in RDS: {type(data)}")
            return None, None, None

    except Exception as e:
        logger.error(f"Failed to extract from {rds_path}: {e}")
        return None, None, None


def matrix_to_edgelist(
    matrix: np.ndarray,
    codes: List[str],
    names: List[str],
    stratification: FileStratification,
    pvalues: Optional[np.ndarray] = None,
    counts: Optional[np.ndarray] = None,
    min_odds_ratio: float = 1.5,
    min_count: int = 100,
) -> pd.DataFrame:
    """
    Convert adjacency matrix to edge-list DataFrame.

    Args:
        matrix: Adjacency matrix with odds ratios
        codes: List of disease codes
        names: List of disease names (German)
        stratification: FileStratification object
        pvalues: Optional p-value matrix
        counts: Optional patient count matrix
        min_odds_ratio: Minimum odds ratio threshold
        min_count: Minimum patient count threshold

    Returns:
        DataFrame in edge-list format
    """
    edges = []
    n = len(codes)

    # Get ICD chapters for all codes
    chapters = [get_icd_chapter(code) for code in codes]

    for i in range(n):
        for j in range(i + 1, n):  # Upper triangle only (undirected)
            or_value = matrix[i, j]

            # Skip if below thresholds
            if or_value < min_odds_ratio:
                continue

            count = counts[i, j] if counts is not None else None
            if count is not None and count < min_count:
                continue

            p_value = pvalues[i, j] if pvalues is not None else None

            edge = {
                "disease_1_code": codes[i],
                "disease_1_name_de": names[i],
                "disease_2_code": codes[j],
                "disease_2_name_de": names[j],
                "odds_ratio": or_value,
                "p_value": p_value,
                "patient_count": count,
                "sex": stratification.sex,
                "stratum_type": stratification.stratum_type,
                "stratum_value": stratification.stratum_value,
                "granularity": stratification.granularity,
                "icd_chapter_1": chapters[i][0],
                "icd_chapter_2": chapters[j][0],
            }
            edges.append(edge)

    return pd.DataFrame(edges)


def load_prevalence_data(prevalence_dir: str) -> pd.DataFrame:
    """
    Load prevalence data from CSV.

    Args:
        prevalence_dir: Directory containing prevalence files

    Returns:
        DataFrame with prevalence information
    """
    filepath = os.path.join(prevalence_dir, "Prevalence_Sex_Age_Year_ICD.csv")

    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        logger.info(f"Loaded prevalence data: {len(df)} rows")
        return df
    else:
        logger.warning(f"Prevalence file not found: {filepath}")
        return pd.DataFrame()


def generate_metadata(
    all_edges: pd.DataFrame,
    mappings: Dict[str, pd.DataFrame],
    prevalence_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Generate disease metadata from processed edges.

    Args:
        all_edges: Combined edge-list DataFrame
        mappings: Dictionary of mapping DataFrames by granularity
        prevalence_df: Optional prevalence DataFrame

    Returns:
        DataFrame with disease metadata
    """
    metadata = []

    for granularity in ["ICD", "Blocks", "Chronic"]:
        if granularity not in mappings:
            continue

        mapping = mappings[granularity]
        config = GRANULARITY_CONFIG[granularity]
        code_col = config["code_col"]
        name_col = config["name_col"]

        # Get unique diseases from edges for this granularity
        gran_edges = all_edges[all_edges["granularity"] == granularity]

        disease_1_codes = gran_edges[["disease_1_code", "disease_1_name_de"]].rename(
            columns={"disease_1_code": "code", "disease_1_name_de": "name_de"}
        )
        disease_2_codes = gran_edges[["disease_2_code", "disease_2_name_de"]].rename(
            columns={"disease_2_code": "code", "disease_2_name_de": "name_de"}
        )

        unique_diseases = pd.concat([disease_1_codes, disease_2_codes]).drop_duplicates(
            "code"
        )

        for _, row in unique_diseases.iterrows():
            code = row["code"]
            name_de = row["name_de"]

            # Get chapter info
            chapter_num, chapter_name = get_icd_chapter(code)

            # Calculate aggregated prevalence if data available
            prevalence_rate = None
            if prevalence_df is not None and not prevalence_df.empty:
                prev_subset = prevalence_df[prevalence_df["ICD"] == code]
                if not prev_subset.empty:
                    prevalence_rate = prev_subset["Prevalence"].mean()

            metadata.append(
                {
                    "code": code,
                    "name_de": name_de,
                    "name_en": "",  # Will be filled by translation
                    "icd_chapter": chapter_num,
                    "icd_chapter_name": chapter_name,
                    "granularity": granularity,
                    "prevalence_rate": prevalence_rate,
                }
            )

    return pd.DataFrame(metadata)


def generate_processing_report(
    edges_df: pd.DataFrame, metadata_df: pd.DataFrame, processing_stats: Dict[str, Any]
) -> str:
    """
    Generate validation and processing report.

    Args:
        edges_df: Final edge-list DataFrame
        metadata_df: Metadata DataFrame
        processing_stats: Dictionary of processing statistics

    Returns:
        Report string
    """
    report = []
    report.append("=" * 70)
    report.append("DATA CLEANING PIPELINE REPORT")
    report.append("Austrian Comorbidity Networks - Austrian Hospital Data (1997-2014)")
    report.append("=" * 70)
    report.append("")

    # Processing summary
    report.append("PROCESSING SUMMARY")
    report.append("-" * 70)
    report.append(
        f"Total matrices processed: {processing_stats.get('total_matrices', 0)}"
    )
    report.append(
        f"Total disease pairs before filtering: {processing_stats.get('pairs_before_filter', 0)}"
    )
    report.append(f"Total disease pairs after filtering: {len(edges_df)}")
    report.append("")

    # Granularity breakdown
    report.append("DISEASE PAIRS BY GRANULARITY")
    report.append("-" * 70)
    for granularity in ["ICD", "Blocks", "Chronic"]:
        count = len(edges_df[edges_df["granularity"] == granularity])
        report.append(f"  {granularity}: {count:,} pairs")
    report.append("")

    # Sex breakdown
    report.append("DISEASE PAIRS BY SEX")
    report.append("-" * 70)
    for sex in edges_df["sex"].unique():
        count = len(edges_df[edges_df["sex"] == sex])
        report.append(f"  {sex}: {count:,} pairs")
    report.append("")

    # Stratification breakdown
    report.append("DISEASE PAIRS BY STRATIFICATION TYPE")
    report.append("-" * 70)
    for stype in edges_df["stratum_type"].unique():
        count = len(edges_df[edges_df["stratum_type"] == stype])
        report.append(f"  {stype}: {count:,} pairs")
    report.append("")

    # Odds ratio statistics
    report.append("ODDS RATIO STATISTICS")
    report.append("-" * 70)
    report.append(f"  Mean: {edges_df['odds_ratio'].mean():.3f}")
    report.append(f"  Median: {edges_df['odds_ratio'].median():.3f}")
    report.append(f"  Max: {edges_df['odds_ratio'].max():.3f}")
    report.append(f"  Min: {edges_df['odds_ratio'].min():.3f}")
    report.append("")

    # ICD chapter distribution
    report.append("ICD CHAPTER DISTRIBUTION (Disease 1)")
    report.append("-" * 70)
    chapter_counts = edges_df["icd_chapter_1"].value_counts().sort_index()
    for chapter, count in chapter_counts.items():
        pct = count / len(edges_df) * 100
        chapter_name = ICD_CHAPTERS_EN.get(str(chapter), "Unknown")
        report.append(
            f"  Chapter {chapter}: {count:,} pairs ({pct:.1f}%) - {chapter_name}"
        )
    report.append("")

    # Unique diseases
    report.append("UNIQUE DISEASES")
    report.append("-" * 70)
    report.append(f"  Total unique diseases: {len(metadata_df)}")
    for granularity in ["ICD", "Blocks", "Chronic"]:
        count = len(metadata_df[metadata_df["granularity"] == granularity])
        report.append(f"    {granularity}: {count} diseases")
    report.append("")

    # Data quality metrics
    report.append("DATA QUALITY METRICS")
    report.append("-" * 70)
    report.append(
        f"  P-values available: {edges_df['p_value'].notna().sum():,} / {len(edges_df):,}"
    )
    report.append(
        f"  Patient counts available: {edges_df['patient_count'].notna().sum():,} / {len(edges_df):,}"
    )
    report.append(f"  Missing translations: {metadata_df['name_en'].eq('').sum():,}")
    report.append("")

    # Filtering statistics
    report.append("FILTERING SUMMARY")
    report.append("-" * 70)
    report.append(
        f"  Min odds ratio threshold: {processing_stats.get('min_odds_ratio', 1.5)}"
    )
    report.append(
        f"  Min patient count threshold: {processing_stats.get('min_count', 100)}"
    )
    report.append("")

    report.append("=" * 70)
    report.append("Report generated successfully")
    report.append("=" * 70)

    return "\n".join(report)


def process_all_matrices(
    data_dir: str,
    output_dir: str,
    min_odds_ratio: float = 1.5,
    min_count: int = 100,
    translate: bool = False,
) -> Tuple[pd.DataFrame, pd.DataFrame, str]:
    """
    Main processing function to convert all stratified matrices to edge-lists.

    Args:
        data_dir: Root data directory
        output_dir: Output directory for processed files
        min_odds_ratio: Minimum odds ratio threshold
        min_count: Minimum patient count threshold
        translate: Whether to translate German names to English

    Returns:
        Tuple of (edges_df, metadata_df, report)
    """
    adjacency_dir = os.path.join(data_dir, "Data", "3.AdjacencyMatrices")
    contingency_dir = os.path.join(data_dir, "Data", "2.ContingencyTables")
    prevalence_dir = os.path.join(data_dir, "Data", "1.Prevalence")
    mapping_dir = os.path.join(
        data_dir, "..", "Comorbidity-Networks-From-Population-Wide-Health-Data"
    )  # Mapping files located in sibling directory

    # Load mappings
    logger.info("Loading disease mappings...")
    mappings = {}
    for granularity in ["ICD", "Blocks", "Chronic"]:
        try:
            mappings[granularity] = load_mapping(granularity, mapping_dir)
        except Exception as e:
            logger.error(f"Failed to load {granularity} mapping: {e}")

    # Load prevalence data
    logger.info("Loading prevalence data...")
    prevalence_df = load_prevalence_data(prevalence_dir)

    # Find all matrix files
    matrix_files = glob.glob(os.path.join(adjacency_dir, "Adj_Matrix_*.csv"))
    logger.info(f"Found {len(matrix_files)} adjacency matrix files")

    # Process each matrix
    all_edges = []
    processing_stats = {
        "total_matrices": len(matrix_files),
        "pairs_before_filter": 0,
        "min_odds_ratio": min_odds_ratio,
        "min_count": min_count,
    }

    for filepath in matrix_files:
        filename = os.path.basename(filepath)
        logger.info(f"Processing {filename}...")

        try:
            # Parse stratification from filename
            strat = parse_filename_stratification(filename)
            config = GRANULARITY_CONFIG[strat.granularity]
            size = config["size"]

            # Load mapping for this granularity
            mapping = mappings.get(strat.granularity)
            if mapping is None:
                logger.warning(f"No mapping for {strat.granularity}, skipping")
                continue

            codes = mapping[config["code_col"]].tolist()
            names = mapping[config["name_col"]].tolist()

            # Load adjacency matrix
            matrix = load_adjacency_matrix(filepath, size)

            # Try to load corresponding contingency table for p-values and counts
            # First try exported CSV files (generated by scripts/export_contingency_tables.R)
            pvalues = None
            counts = None

            export_dir = os.path.join(contingency_dir, "exported")
            _, pvalues, counts = extract_pvalues_from_csv(
                export_dir=export_dir,
                granularity=strat.granularity,
                sex=strat.sex,
                stratum_type=strat.stratum_type,
                stratum_value=strat.stratum_value,
                size=size,
            )

            if pvalues is None:
                logger.warning(
                    f"Exported CSV files not found for {strat.granularity} {strat.sex} {strat.stratum_type} {strat.stratum_value}. "
                    f"Please run: Rscript scripts/export_contingency_tables.R"
                )

            # Convert to edge-list
            edges = matrix_to_edgelist(
                matrix=matrix,
                codes=codes,
                names=names,
                stratification=strat,
                pvalues=pvalues,
                counts=counts,
                min_odds_ratio=min_odds_ratio,
                min_count=min_count,
            )

            all_edges.append(edges)
            processing_stats["pairs_before_filter"] += len(edges)

            logger.info(f"  Extracted {len(edges)} edges from {filename}")

        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            continue

    # Combine all edges
    logger.info("Combining all edge-lists...")
    combined_edges = pd.concat(all_edges, ignore_index=True)

    # Generate metadata
    logger.info("Generating disease metadata...")
    metadata_df = generate_metadata(combined_edges, mappings, prevalence_df)

    # Translate names if requested
    if translate and len(metadata_df) > 0:
        logger.info("Translating German disease names to English...")
        german_names = metadata_df["name_de"].tolist()
        english_names = translate_german_to_english(german_names)
        metadata_df["name_en"] = english_names

        # Also translate in edges dataframe
        name_map = dict(zip(metadata_df["code"], metadata_df["name_en"]))
        combined_edges["disease_1_name_en"] = combined_edges["disease_1_code"].map(
            name_map
        )
        combined_edges["disease_2_name_en"] = combined_edges["disease_2_code"].map(
            name_map
        )
    else:
        # Add empty columns for English names
        metadata_df["name_en"] = ""
        combined_edges["disease_1_name_en"] = ""
        combined_edges["disease_2_name_en"] = ""

    # Reorder columns for output
    edge_columns = [
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
    ]
    combined_edges = combined_edges[edge_columns]

    # Generate report
    logger.info("Generating processing report...")
    report = generate_processing_report(combined_edges, metadata_df, processing_stats)

    # Save outputs
    os.makedirs(output_dir, exist_ok=True)

    edges_path = os.path.join(output_dir, "disease_pairs_clean.csv")
    combined_edges.to_csv(edges_path, index=False)
    logger.info(f"Saved disease pairs to: {edges_path}")

    metadata_path = os.path.join(output_dir, "disease_metadata.csv")
    metadata_df.to_csv(metadata_path, index=False)
    logger.info(f"Saved disease metadata to: {metadata_path}")

    report_path = os.path.join(output_dir, "processing_report.txt")
    with open(report_path, "w") as f:
        f.write(report)
    logger.info(f"Saved processing report to: {report_path}")

    return combined_edges, metadata_df, report


if __name__ == "__main__":
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(description="Process Austrian comorbidity data")
    parser.add_argument("--data-dir", default="Data", help="Data directory path")
    parser.add_argument(
        "--output-dir", default="data/processed", help="Output directory"
    )
    parser.add_argument("--min-or", type=float, default=1.5, help="Minimum odds ratio")
    parser.add_argument(
        "--min-count", type=int, default=100, help="Minimum patient count"
    )
    parser.add_argument(
        "--translate", action="store_true", help="Translate German names"
    )

    args = parser.parse_args()

    edges, metadata, report = process_all_matrices(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        min_odds_ratio=args.min_or,
        min_count=args.min_count,
        translate=args.translate,
    )

    print(report)
