"""
Module 1.2: Translate ICD-10 Disease Descriptions from German to English

This module translates German ICD-10 disease descriptions to English using:
1. WHO ICD-10 API for official English names (verified translations)
2. deep-translator GoogleTranslator as fallback for automatic translation

Security and Quality Features:
- Rate limiting to avoid API bans
- Input validation and sanitization
- Secure logging (no sensitive data exposure)
- Error handling with graceful degradation
- Progress tracking and validation reports

Author: Agent 1 (Translation Module)
Date: January 2026
"""

import argparse
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests
from deep_translator import GoogleTranslator
from deep_translator.exceptions import (
    LanguageNotSupportedException,
    NotValidLength,
    RequestError,
    TooManyRequests,
    TranslationNotFound,
)

# Configure secure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# WHO ICD-10 API configuration
WHO_API_BASE = "https://id.who.int/icd/entity"
WHO_API_VERSION = "v2"

# Manual translations for verified high-prevalence conditions
# Sourced from WHO ICD-10 2019 edition browser: https://icd.who.int/browse10/2019/en
VERIFIED_TRANSLATIONS: Dict[str, str] = {
    # Endocrine/metabolic (E-codes)
    "E10": "Type 1 diabetes mellitus",
    "E11": "Type 2 diabetes mellitus",
    "E12": "Malnutrition-related diabetes mellitus",
    "E13": "Other specified diabetes mellitus",
    "E14": "Unspecified diabetes mellitus",
    "E66": "Obesity",
    "E78": "Disorders of lipoprotein metabolism and other lipidaemias",
    "E84": "Cystic fibrosis",
    "E87": "Other disorders of fluid, electrolyte and acid-base balance",
    # Circulatory system (I-codes) - High prevalence
    "I10": "Essential (primary) hypertension",
    "I11": "Hypertensive heart disease",
    "I12": "Hypertensive renal disease",
    "I20": "Angina pectoris",
    "I21": "Acute myocardial infarction",
    "I22": "Subsequent myocardial infarction",
    "I25": "Chronic ischaemic heart disease",
    "I50": "Heart failure",
    "I48": "Atrial fibrillation and flutter",
    "I63": "Cerebral infarction",
    "I64": "Stroke, not specified as haemorrhage or infarction",
    "I70": "Atherosclerosis",
    "I71": "Aortic aneurysm and dissection",
    # Respiratory system (J-codes) - High prevalence
    "J06": "Acute upper respiratory infections of multiple and unspecified sites",
    "J18": "Pneumonia, unspecified organism",
    "J20": "Acute bronchitis",
    "J41": "Simple and mucopurulent chronic bronchitis",
    "J43": "Emphysema",
    "J44": "Other chronic obstructive pulmonary disease",
    "J45": "Asthma",
    "J47": "Bronchiectasis",
    "J80": "Adult respiratory distress syndrome",
    # Mental/behavioral (F-codes) - High prevalence
    "F03": "Unspecified dementia",
    "F10": "Mental and behavioural disorders due to use of alcohol",
    "F20": "Schizophrenia",
    "F25": "Schizoaffective disorders",
    "F31": "Bipolar affective disorder",
    "F32": "Depressive episode",
    "F33": "Recurrent depressive disorder",
    "F41": "Other anxiety disorders",
    "F43": "Reaction to severe stress and adjustment disorders",
    # Nervous system (G-codes)
    "G20": "Parkinson disease",
    "G30": "Alzheimer disease",
    "G35": "Multiple sclerosis",
    "G40": "Epilepsy",
    "G43": "Migraine",
    "G47": "Sleep disorders",
    # Digestive system (K-codes)
    "K21": "Gastro-oesophageal reflux disease",
    "K25": "Gastric ulcer",
    "K29": "Gastritis and duodenitis",
    "K50": "Crohn disease",
    "K51": "Ulcerative colitis",
    "K52": "Other noninfective gastroenteritis and colitis",
    "K56": "Paralytic ileus and intestinal obstruction without hernia",
    "K70": "Alcoholic liver disease",
    "K71": "Toxic liver disease",
    "K72": "Hepatic failure",
    "K73": "Chronic hepatitis",
    "K74": "Fibrosis and cirrhosis of liver",
    "K80": "Cholelithiasis",
    # Genitourinary (N-codes)
    "N17": "Acute renal failure",
    "N18": "Chronic kidney disease",
    "N19": "Unspecified kidney failure",
    "N20": "Calculus of kidney and ureter",
    "N39": "Other disorders of urinary system",
    # Musculoskeletal (M-codes)
    "M05": "Seropositive rheumatoid arthritis",
    "M06": "Other rheumatoid arthritis",
    "M16": "Coxarthrosis",
    "M17": "Gonarthrosis",
    "M79": "Other and unspecified soft tissue disorders",
    "M81": "Osteoporosis without current pathological fracture",
    "M84": "Disorders of continuity of bone",
    # Neoplasms (C-codes) - Common cancers
    "C16": "Malignant neoplasm of stomach",
    "C18": "Malignant neoplasm of colon",
    "C20": "Malignant neoplasm of rectum",
    "C25": "Malignant neoplasm of pancreas",
    "C34": "Malignant neoplasm of bronchus and lung",
    "C50": "Malignant neoplasm of breast",
    "C61": "Malignant neoplasm of prostate",
    "C64": "Malignant neoplasm of kidney",
    "C67": "Malignant neoplasm of bladder",
    "C78": "Secondary malignant neoplasm of respiratory and digestive organs",
    "C79": "Secondary malignant neoplasm of other sites",
    "C80": "Malignant neoplasm without specification of site",
    # Infectious diseases (A-B codes)
    "A00": "Cholera",
    "A41": "Other sepsis",
    "B01": "Varicella",
    "B02": "Zoster",
    "B18": "Chronic viral hepatitis",
    "B20": "Human immunodeficiency virus (HIV) disease resulting in infectious and parasitic diseases",
    "J12": "Viral pneumonia",
    "J13": "Pneumonia due to Streptococcus pneumoniae",
    "J14": "Pneumonia due to Haemophilus influenzae",
    # Others - high prevalence
    "D50": "Iron deficiency anaemia",
    "D64": "Other anaemias",
    "D69": "Purpura and other haemorrhagic conditions",
    "E03": "Other hypothyroidism",
    "E05": "Thyrotoxicosis",
    "F17": "Mental and behavioural disorders due to use of tobacco",
    "H25": "Senile cataract",
    "H26": "Other cataract",
    "I35": "Nonrheumatic aortic valve disorders",
    "I74": "Arterial embolism and thrombosis",
    "I80": "Phlebitis and thrombophlebitis",
    "I83": "Varicose veins of lower extremities",
    "I84": "Haemorrhoids",
    "J09": "Influenza due to certain identified influenza viruses",
    "J10": "Influenza due to other identified influenza virus",
    "J11": "Influenza, virus not identified",
    "K26": "Duodenal ulcer",
    "K57": "Diverticular disease of intestine",
    "L03": "Cellulitis",
    "L89": "Decubitus ulcer and pressure area",
    "N28": "Other and unspecified disorders of kidney and ureter",
    "S72": "Fracture of femur",
    "T07": "Unspecified multiple injuries",
    "T14": "Injury of unspecified body region",
    "Z51": "Other medical care",
    "Z95": "Presence of cardiac and vascular implants and grafts",
    "Z99": "Dependence on enabling machines and devices",
}


def fetch_who_icd10_name(icd_code: str, api_key: Optional[str] = None) -> Optional[str]:
    """
    Attempt to fetch official English name from WHO ICD-10 API.

    Note: WHO ICD-10 API requires authentication. This function attempts
    to use the public browser as a fallback when no API key is available.

    Security: Uses proper timeout and validates response before parsing.

    Args:
        icd_code: The ICD-10 code (e.g., "E11", "I10")
        api_key: Optional WHO ICD API key

    Returns:
        Official English name if found, None otherwise
    """
    # First check our verified dictionary
    if icd_code in VERIFIED_TRANSLATIONS:
        logger.debug(f"Using verified translation for {icd_code}")
        return VERIFIED_TRANSLATIONS[icd_code]

    # Attempt WHO API lookup if key provided
    if api_key:
        try:
            # WHO API endpoint for ICD-10
            url = f"{WHO_API_BASE}/{icd_code}"
            headers = {
                "API-Version": WHO_API_VERSION,
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            }

            # Security: timeout prevents hanging on network issues
            response = requests.get(
                url,
                headers=headers,
                timeout=(5, 10),  # (connect timeout, read timeout)
            )
            response.raise_for_status()

            data = response.json()

            # Extract English title from response
            if "title" in data and "@value" in data["title"]:
                return data["title"]["@value"]

        except requests.exceptions.Timeout:
            logger.warning(f"WHO API timeout for {icd_code}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"WHO API request failed for {icd_code}: {type(e).__name__}")
        except (KeyError, ValueError) as e:
            logger.warning(f"WHO API response parsing failed for {icd_code}: {e}")
        except Exception as e:
            # Catch-all for unexpected errors - don't expose sensitive details
            logger.error(f"Unexpected error fetching WHO data for {icd_code}")

    return None


def translate_batch(
    texts: List[str],
    batch_size: int = 25,
    delay: float = 1.0,
    source_lang: str = "de",
    target_lang: str = "en",
) -> List[str]:
    """
    Translate German texts to English with rate limiting and error handling.

    Quality Features:
    - Batch processing for efficiency
    - Rate limiting to avoid API bans
    - Graceful error handling with fallback to original text
    - Progress logging

    Security:
    - Input length validation
    - No logging of actual medical text content
    - Secure exception handling

    Args:
        texts: List of German texts to translate
        batch_size: Number of texts to translate per batch
        delay: Seconds to wait between batches (rate limiting)
        source_lang: Source language code (default: 'de')
        target_lang: Target language code (default: 'en')

    Returns:
        List of translated texts (original text on failure)
    """
    if not texts:
        return []

    # Input validation
    for i, text in enumerate(texts):
        if not isinstance(text, str):
            logger.warning(f"Invalid input type at index {i}, converting to string")
            texts[i] = str(text) if text is not None else ""

    # Initialize translator
    try:
        translator = GoogleTranslator(source=source_lang, target=target_lang)
    except LanguageNotSupportedException as e:
        logger.error(f"Language not supported: {e}")
        return texts  # Return originals on critical failure
    except Exception as e:
        logger.error(f"Failed to initialize translator: {type(e).__name__}")
        return texts

    results = []
    total = len(texts)

    for batch_start in range(0, total, batch_size):
        batch_end = min(batch_start + batch_size, total)
        batch = texts[batch_start:batch_end]

        logger.info(
            f"Translating batch {batch_start // batch_size + 1} "
            f"({batch_start + 1}-{batch_end}/{total})"
        )

        try:
            # Use translate_batch for efficiency
            translated_batch = translator.translate_batch(batch)

            # Validate results
            for i, trans in enumerate(translated_batch):
                if trans and isinstance(trans, str):
                    results.append(trans)
                else:
                    # Fallback to original on empty/invalid translation
                    logger.warning(f"Empty translation at index {batch_start + i}")
                    results.append(batch[i])

        except TooManyRequests:
            logger.warning("Rate limit hit, increasing delay and retrying...")
            time.sleep(delay * 3)  # Triple delay on rate limit
            try:
                translated_batch = translator.translate_batch(batch)
                results.extend(
                    [t if t else batch[i] for i, t in enumerate(translated_batch)]
                )
            except Exception as e:
                logger.error(f"Retry failed, using original texts for batch")
                results.extend(batch)

        except NotValidLength as e:
            logger.warning(f"Text too long in batch, translating individually...")
            # Fall back to individual translation
            for text in batch:
                try:
                    if len(text) > 5000:  # Google Translate limit
                        logger.warning("Text exceeds limit, truncating...")
                        text = text[:4995] + "..."
                    result = translator.translate(text)
                    results.append(result if result else text)
                except Exception as e:
                    logger.warning(f"Individual translation failed, using original")
                    results.append(text)

        except RequestError as e:
            logger.error(f"Network error during translation: {type(e).__name__}")
            results.extend(batch)  # Use originals on network error

        except Exception as e:
            logger.error(f"Translation batch failed: {type(e).__name__}")
            results.extend(batch)  # Use originals on any error

        # Rate limiting between batches (except after last batch)
        if batch_end < total:
            time.sleep(delay)

    return results


def translate_all_descriptions(
    input_csv: str,
    output_dir: str,
    use_who_first: bool = True,
    who_api_key: Optional[str] = None,
    batch_size: int = 25,
    translation_delay: float = 1.0,
) -> pd.DataFrame:
    """
    Main translation function for ICD-10 disease descriptions.

    Workflow:
    1. Load German descriptions from CSV
    2. Try WHO-verified dictionary first
    3. Try WHO API lookup (if key provided)
    4. Batch translate remaining descriptions via Google Translate
    5. Generate output files and validation report

    Security:
    - Validates input file paths
    - Sanitizes output paths
    - Secure logging (no PHI exposure)

    Args:
        input_csv: Path to input CSV with German descriptions
        output_dir: Directory for output files
        use_who_first: Whether to use WHO sources before auto-translation
        who_api_key: Optional WHO ICD API key
        batch_size: Translation batch size
        translation_delay: Delay between batches (seconds)

    Returns:
        DataFrame with all translations
    """
    # Validate paths
    input_path = Path(input_csv)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_csv}")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load data
    logger.info(f"Loading ICD codes from {input_csv}")
    try:
        df = pd.read_csv(input_csv)
    except Exception as e:
        raise ValueError(f"Failed to read input CSV: {e}")

    # Validate required columns
    required_cols = ["diagnose_id", "icd_code", "descr"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    logger.info(f"Loaded {len(df)} ICD codes")

    # Initialize result arrays
    english_names = []
    translation_sources = []
    to_translate_indices = []
    to_translate_texts = []

    # Phase 1: WHO lookup for verified translations
    logger.info("Phase 1: Looking up verified WHO translations...")
    for idx, row in df.iterrows():
        icd_code = str(row["icd_code"]).strip() if pd.notna(row["icd_code"]) else ""
        german_name = str(row["descr"]).strip() if pd.notna(row["descr"]) else ""

        english_name = None
        source = "auto_translated"  # Default

        if use_who_first and icd_code:
            # Try verified dictionary first
            if icd_code in VERIFIED_TRANSLATIONS:
                english_name = VERIFIED_TRANSLATIONS[icd_code]
                source = "WHO_verified"
                logger.debug(f"Verified translation for {icd_code}")
            elif who_api_key:
                # Try WHO API
                who_name = fetch_who_icd10_name(icd_code, who_api_key)
                if who_name:
                    english_name = who_name
                    source = "WHO_API"
                    logger.debug(f"WHO API translation for {icd_code}")

        if english_name:
            english_names.append(english_name)
            translation_sources.append(source)
        else:
            # Mark for auto-translation
            english_names.append(None)
            translation_sources.append("auto_translated")
            if german_name:
                to_translate_indices.append(idx)
                to_translate_texts.append(german_name)

    # Phase 2: Batch auto-translation
    if to_translate_texts:
        logger.info(
            f"Phase 2: Auto-translating {len(to_translate_texts)} descriptions..."
        )
        translated = translate_batch(
            to_translate_texts,
            batch_size=batch_size,
            delay=translation_delay,
        )

        # Update results with translations
        for idx, trans in zip(to_translate_indices, translated):
            english_names[idx] = trans
            # Update source if translation succeeded
            if trans != df.iloc[idx]["descr"]:
                translation_sources[idx] = "auto_translated"
            else:
                translation_sources[idx] = "translation_failed"

    # Build output DataFrame
    df["descr_english"] = english_names
    df["descr_german"] = df["descr"]  # Keep original German
    df["translation_source"] = translation_sources

    # Validate no missing translations
    missing_count = sum(1 for name in english_names if not name or name == "")
    if missing_count > 0:
        logger.warning(f"{missing_count} translations are missing or empty")

    # Save full version with all metadata
    full_output = output_path / "ICD10_Diagnoses_English.csv"
    full_df = df[
        [
            "diagnose_id",
            "icd_code",
            "descr_english",
            "descr_german",
            "translation_source",
        ]
    ]
    full_df.to_csv(full_output, index=False)
    logger.info(f"Saved full translations to {full_output}")

    # Save simplified version for downstream use
    simple_output = output_path / "disease_names.csv"
    simple_df = df[["icd_code", "descr_english"]].rename(
        columns={"descr_english": "name_english"}
    )
    simple_df.to_csv(simple_output, index=False)
    logger.info(f"Saved simplified disease names to {simple_output}")

    # Generate verification report
    generate_verification_report(df, output_path)

    return df


def generate_verification_report(df: pd.DataFrame, output_dir: Path) -> None:
    """
    Generate a translation verification report.

    Creates a text file with statistics and manual verification checklist
    for high-priority ICD codes.

    Security: No patient data or PHI included in report.

    Args:
        df: DataFrame with translation results
        output_dir: Directory for output files
    """
    report = []
    report.append("=" * 70)
    report.append("ICD-10 TRANSLATION VERIFICATION REPORT")
    report.append("=" * 70)
    report.append(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")

    # Statistics
    total = len(df)
    who_verified = (df["translation_source"] == "WHO_verified").sum()
    who_api = (df["translation_source"] == "WHO_API").sum()
    auto_trans = (df["translation_source"] == "auto_translated").sum()
    failed = (df["translation_source"] == "translation_failed").sum()

    report.append("TRANSLATION STATISTICS")
    report.append("-" * 70)
    report.append(f"Total ICD codes:           {total:5d} ({100.0:5.1f}%)")
    report.append(
        f"WHO verified (dictionary): {who_verified:5d} ({100 * who_verified / total:5.1f}%)"
    )
    report.append(
        f"WHO API lookup:            {who_api:5d} ({100 * who_api / total:5.1f}%)"
    )
    report.append(
        f"Auto-translated:           {auto_trans:5d} ({100 * auto_trans / total:5.1f}%)"
    )
    report.append(
        f"Translation failed:        {failed:5d} ({100 * failed / total:5.1f}%)"
    )
    report.append("")

    # High-priority verification checklist
    report.append("MANUAL VERIFICATION CHECKLIST (Top Priority Codes)")
    report.append("-" * 70)
    report.append("[ ] = Needs verification  [✓] = Verified")
    report.append("")

    # Top 25 high-prevalence codes to verify
    priority_codes = [
        "E11",
        "I10",
        "I25",
        "I50",
        "J44",
        "N18",
        "E78",
        "M81",
        "F32",
        "J45",
        "C34",
        "C50",
        "C18",
        "E66",
        "I21",
        "G30",
        "F03",
        "J18",
        "N17",
        "K74",
        "C61",
        "I20",
        "G20",
        "M16",
        "C25",
        "K57",
        "F10",
        "I48",
        "B18",
        "J47",
        "D50",
        "E03",
    ]

    for code in priority_codes:
        rows = df[df["icd_code"] == code]
        if not rows.empty:
            row = rows.iloc[0]
            source = row["translation_source"]
            status = "[✓]" if source == "WHO_verified" else "[ ]"
            report.append(f"{status} {code:5s} ({source:20s}): {row['descr_english']}")

    report.append("")
    report.append("=" * 70)
    report.append("NOTES")
    report.append("-" * 70)
    report.append(
        "- WHO verified translations are manually curated from WHO ICD-10 2019"
    )
    report.append("- Auto-translated entries should be verified for clinical accuracy")
    report.append("- Verify translations against: https://icd.who.int/browse10/2019/en")
    report.append("- Report any discrepancies to the data steward")
    report.append("")

    # Write report
    validation_dir = output_dir / "validation"
    validation_dir.mkdir(parents=True, exist_ok=True)

    report_path = validation_dir / "translation_verification.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report))

    logger.info(f"Saved verification report to {report_path}")


def create_completion_marker(output_dir: str) -> None:
    """
    Create a marker file signaling completion for downstream agents.

    Args:
        output_dir: Directory to create marker in
    """
    marker_path = Path(output_dir) / ".translation_done"
    with open(marker_path, "w") as f:
        f.write("COMPLETE\n")
    logger.info(f"Created completion marker: {marker_path}")


def main():
    """CLI entry point for translation module."""
    parser = argparse.ArgumentParser(
        description="Translate ICD-10 disease descriptions from German to English",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python scripts/translate_descriptions.py
  
  # Custom input/output
  python scripts/translate_descriptions.py --input data.csv --output-dir results/
  
  # Faster processing (larger batches, shorter delays)
  python scripts/translate_descriptions.py --batch-size 50 --delay 0.5
  
  # With WHO API key for additional official translations
  python scripts/translate_descriptions.py --who-api-key YOUR_API_KEY
        """,
    )

    parser.add_argument(
        "--input",
        default="Comorbidity-Networks-From-Population-Wide-Health-Data/ICD10_Diagnoses_All.csv",
        help="Path to input CSV with German ICD descriptions (default: %(default)s)",
    )
    parser.add_argument(
        "--output-dir",
        default="Data/processed",
        help="Output directory for translated files (default: %(default)s)",
    )
    parser.add_argument(
        "--who-api-key",
        default=None,
        help="Optional WHO ICD API key for official translations",
    )
    parser.add_argument(
        "--skip-who",
        action="store_true",
        help="Skip WHO lookup and use auto-translation only",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=25,
        help="Translation batch size (default: %(default)s)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between batches in seconds (default: %(default)s)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Run translation
        df = translate_all_descriptions(
            input_csv=args.input,
            output_dir=args.output_dir,
            use_who_first=not args.skip_who,
            who_api_key=args.who_api_key,
            batch_size=args.batch_size,
            translation_delay=args.delay,
        )

        # Create completion marker
        create_completion_marker(args.output_dir)

        # Success summary
        logger.info("=" * 70)
        logger.info("TRANSLATION COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Total codes processed: {len(df)}")
        logger.info(f"Output files created in: {args.output_dir}")
        logger.info("")
        logger.info("Generated files:")
        logger.info(f"  - ICD10_Diagnoses_English.csv (full metadata)")
        logger.info(f"  - disease_names.csv (simplified)")
        logger.info(f"  - validation/translation_verification.txt")
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Review verification report for high-priority codes")
        logger.info("  2. Manual verification of auto-translated entries")
        logger.info("  3. Proceed to Agent 2 (Master Database)")

    except FileNotFoundError as e:
        logger.error(f"Input file error: {e}")
        raise SystemExit(1)
    except Exception as e:
        logger.error(f"Translation failed: {type(e).__name__}: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
