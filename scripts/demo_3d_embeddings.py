"""
Demo script to test 3D embedding generation with synthetic data.

This creates a synthetic adjacency matrix simulating disease comorbidity
relationships, then runs the embedding pipeline to verify functionality.
"""

import sys
from pathlib import Path

import numpy as np

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from generate_3d_embeddings import (
    embed_spring_layout,
    embed_tsne,
    embed_umap,
    normalize_coordinates,
    validate_embedding,
    visualize_embedding,
    generate_quality_report,
)


def create_synthetic_adjacency_matrix(n_diseases: int = 50, seed: int = 42) -> tuple:
    """
    Create a synthetic adjacency matrix with chapter-based clustering.

    Simulates 50 diseases organized into 5 ICD chapters (A-E) with:
    - Higher weights within chapters (simulating comorbidity)
    - Lower weights between chapters

    Returns:
        (matrix, codes): adjacency matrix and disease codes
    """
    np.random.seed(seed)

    # Create 5 chapters with 10 diseases each
    chapters = ["A", "B", "C", "D", "E"]
    codes = []
    for ch in chapters:
        for i in range(10):
            codes.append(f"{ch}{i:02d}")

    # Create matrix with chapter-based structure
    matrix = np.random.uniform(0.1, 0.5, (n_diseases, n_diseases))

    # Add stronger connections within chapters
    for ch_idx, ch in enumerate(chapters):
        start_idx = ch_idx * 10
        end_idx = start_idx + 10
        # High within-chapter weights
        matrix[start_idx:end_idx, start_idx:end_idx] = np.random.uniform(
            1.5, 3.0, (10, 10)
        )

    # Make symmetric
    matrix = (matrix + matrix.T) / 2

    # Set diagonal to zero (no self-loops)
    np.fill_diagonal(matrix, 0)

    return matrix, codes


def main():
    print("=" * 60)
    print("3D EMBEDDING PIPELINE DEMO")
    print("=" * 60)
    print()

    # Create synthetic data
    print("Creating synthetic adjacency matrix (50 diseases, 5 chapters)...")
    adj_matrix, codes = create_synthetic_adjacency_matrix()
    print(f"Matrix shape: {adj_matrix.shape}")
    print(f"Sample codes: {codes[:5]}")
    print()

    # Test each embedding method
    methods = {
        "UMAP": embed_umap,
        "t-SNE": embed_tsne,
        "Spring": embed_spring_layout,
    }

    output_dir = Path(__file__).parent.parent / "Data" / "validation"
    output_dir.mkdir(parents=True, exist_ok=True)

    for method_name, embed_func in methods.items():
        print(f"\n{'=' * 60}")
        print(f"Testing {method_name} embedding...")
        print("=" * 60)

        try:
            # Generate embedding
            coords = embed_func(adj_matrix)

            # Normalize
            coords = normalize_coordinates(coords)

            # Validate
            metrics = validate_embedding(coords, codes)

            # Print metrics
            print(f"  Coordinates shape: {coords.shape}")
            print(
                f"  X range: [{metrics['coord_range_x'][0]:.3f}, {metrics['coord_range_x'][1]:.3f}]"
            )
            print(
                f"  Y range: [{metrics['coord_range_y'][0]:.3f}, {metrics['coord_range_y'][1]:.3f}]"
            )
            print(
                f"  Z range: [{metrics['coord_range_z'][0]:.3f}, {metrics['coord_range_z'][1]:.3f}]"
            )
            print(f"  Clustering ratio: {metrics['clustering_quality_ratio']:.2f}x")
            print(
                f"  Quality check: {'PASS' if metrics['passes_quality_threshold'] else 'FAIL'}"
            )

            # Generate visualization
            viz_path = output_dir / f"3d_demo_{method_name.lower()}.png"
            visualize_embedding(coords, codes, str(viz_path))

            # Generate report
            report_path = output_dir / f"demo_quality_{method_name.lower()}.txt"
            generate_quality_report(metrics, method_name, str(report_path))

            print(f"  ✓ Saved visualization: {viz_path}")
            print(f"  ✓ Saved report: {report_path}")

        except Exception as e:
            print(f"  ✗ Error: {e}")

    print()
    print("=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print(f"\nOutputs saved to: {output_dir}")
    print("\nTo run on real data:")
    print("  1. Run R scripts to generate adjacency matrices:")
    print(
        "     Rscript Comorbidity-Networks-From-Population-Wide-Health-Data/Scripts/1_Make_AdjMatrix_ICD.R"
    )
    print("  2. Run Python embedding script:")
    print("     python scripts/generate_3d_embeddings.py --method umap")


if __name__ == "__main__":
    main()
