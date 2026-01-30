#!/usr/bin/env python3
"""
Entry point script for the Austrian Comorbidity Data Cleaning Pipeline.

This script provides a command-line interface for processing adjacency matrices
into cleaned edge-list format.

Usage:
    python run_cleaning.py --data-dir Data --output-dir data/processed

    # With filters
    python run_cleaning.py --min-or 2.0 --min-count 50

    # With German-to-English translation
    python run_cleaning.py --translate

Author: Claude Code
Date: January 2026
"""

import argparse
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from data_cleaning import process_all_matrices


def main():
    """Main entry point for the data cleaning pipeline."""
    parser = argparse.ArgumentParser(
        description="Process Austrian comorbidity adjacency matrices into cleaned edge-list format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python run_cleaning.py
  
  # Custom data and output directories
  python run_cleaning.py --data-dir /path/to/data --output-dir /path/to/output
  
  # Adjust filtering thresholds
  python run_cleaning.py --min-or 2.0 --min-count 200
  
  # Enable German-to-English translation (requires internet connection)
  python run_cleaning.py --translate
  
  # Full command with all options
  python run_cleaning.py \\
      --data-dir Data \\
      --output-dir data/processed \\
      --min-or 1.5 \\
      --min-count 100 \\
      --translate
        """,
    )

    parser.add_argument(
        "--data-dir",
        type=str,
        default="Data",
        help="Root directory containing the data (default: Data)",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Output directory for processed files (default: data/processed)",
    )

    parser.add_argument(
        "--min-or",
        type=float,
        default=1.5,
        metavar="ODDS_RATIO",
        help="Minimum odds ratio threshold for disease pairs (default: 1.5)",
    )

    parser.add_argument(
        "--min-count",
        type=int,
        default=100,
        metavar="COUNT",
        help="Minimum patient count threshold (default: 100)",
    )

    parser.add_argument(
        "--translate",
        action="store_true",
        help="Enable German-to-English translation of disease names",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    # Configure logging if verbose mode
    if args.verbose:
        import logging

        logging.getLogger().setLevel(logging.DEBUG)

    print("=" * 70)
    print("AUSTRIAN COMORBIDITY DATA CLEANING PIPELINE")
    print("=" * 70)
    print(f"Data directory:    {args.data_dir}")
    print(f"Output directory:  {args.output_dir}")
    print(f"Min odds ratio:    {args.min_or}")
    print(f"Min count:         {args.min_count}")
    print(f"Translation:       {'Enabled' if args.translate else 'Disabled'}")
    print("=" * 70)
    print()

    try:
        # Run the main processing function
        edges_df, metadata_df, report = process_all_matrices(
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            min_odds_ratio=args.min_or,
            min_count=args.min_count,
            translate=args.translate,
        )

        # Print report
        print(report)

        # Summary
        print()
        print("=" * 70)
        print("PROCESSING COMPLETE")
        print("=" * 70)
        print(f"Total disease pairs: {len(edges_df):,}")
        print(f"Unique diseases:     {len(metadata_df):,}")
        print()
        print("Output files created:")
        print(f"  - {args.output_dir}/disease_pairs_clean.csv")
        print(f"  - {args.output_dir}/disease_metadata.csv")
        print(f"  - {args.output_dir}/processing_report.txt")
        print("=" * 70)

        return 0

    except FileNotFoundError as e:
        print(f"\nERROR: Required file or directory not found: {e}", file=sys.stderr)
        print("\nPlease ensure:")
        print("  1. The data directory exists and contains the required files")
        print("  2. Adjacency matrices are in: Data/Data/3.AdjacencyMatrices/")
        print("  3. Contingency tables are in: Data/Data/2.ContingencyTables/")
        print("  4. Prevalence data is in: Data/Data/1.Prevalence/")
        return 1

    except Exception as e:
        print(f"\nERROR: Processing failed: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
