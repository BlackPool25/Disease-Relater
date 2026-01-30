# Disease-Relater: Comorbidity Networks Analysis Platform

A comprehensive research platform for analyzing comorbidity networks from population-wide health data, featuring both R-based network analysis and Python-based data cleaning pipelines.

## Overview

This project provides tools to analyze comorbidity networks derived from 8.9 million Austrian hospital patients (1997-2014). It includes:

- **R Pipeline**: Network construction, analysis, and visualization (82 stratified matrices)
- **Python Pipeline**: Data cleaning, transformation, and 3D embedding generation
- **3D Embeddings**: Generate 3D coordinates using UMAP, t-SNE, or force-directed layouts for disease network visualization
- **Multi-granularity support**: ICD-10 codes (1080), ICD Blocks (131), Chronic conditions (46)
- **Statistical analysis**: Odds ratios, p-values, prevalence calculations
- **Network files**: GEXF format for Gephi visualization

## Project Structure

```
Disease-Relater/
├── Comorbidity-Networks-From-Population-Wide-Health-Data/  # R analysis scripts
│   ├── Scripts/
│   │   ├── 1_Make_AdjMatrix_ICD.R          # Create ICD adjacency matrices
│   │   ├── 1_Make_AdjMatrix_Blocks.R       # Create block-level matrices
│   │   ├── 1_Make_AdjMatrix_Chronic.R      # Create chronic condition matrices
│   │   ├── 2_Make_NET_ICD.R                # Generate ICD network files
│   │   ├── 2_Make_NET_Blocks.R             # Generate block network files
│   │   ├── 2_Make_NET_Chronic.R            # Generate chronic network files
│   │   ├── 3_Net_Properties.R              # Network analysis and metrics
│   │   └── Example_PythonScript.ipynb      # Python example notebook
│   └── README.md                           # R pipeline documentation
├── scripts/                                # Python data cleaning & embeddings
│   ├── data_cleaning.py                    # Core cleaning module
│   ├── run_cleaning.py                     # CLI entry point
│   ├── translate_descriptions.py          # ICD-10 German→English translation (Module 1.2)
│   ├── create_master_database.py           # Create unified master databases (Module 1.3)
│   ├── generate_3d_embeddings.py           # Generate 3D disease coordinates (Module 1.4)
│   ├── demo_3d_embeddings.py               # Demo script for testing embeddings
│   └── export_contingency_tables.R         # R export script (required)
├── requirements.txt                        # Python dependencies
├── pyproject.toml                          # Modern Python project config
├── README.md                               # This file
└── README_DATA_CLEANING.md                 # Python pipeline details
```

## Quick Start

### Prerequisites

- Python 3.10 or higher
- R 4.0 or higher
- uv (Python package manager) - recommended
- Git

### Installation

#### Option 1: Using uv (Recommended)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone <repository-url>
cd Disease-Relater

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python packages
uv pip install -r requirements.txt

# Or install in editable mode (for development)
uv pip install -e .
```

#### Option 2: Using pip

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Option 3: Using conda

```bash
# Create environment
conda create -n disease-relater python=3.10
conda activate disease-relater

# Install dependencies
pip install -r requirements.txt
```

### Install R Dependencies

```r
# In R console
install.packages(c("igraph", "dplyr", "rgexf", "stringr", "ggplot2", 
                   "cowplot", "ggpubr", "ggalluvial", "RColorBrewer"))
```

## Usage Guide

### 1. Python Data Cleaning Pipeline

The Python pipeline processes 82 stratified adjacency matrices into cleaned edge-list format.

**Prerequisite**: Export contingency tables to CSV format first (the RDS files cannot be read directly by Python).

```bash
# Step 0: Export contingency tables (run once)
Rscript scripts/export_contingency_tables.R

# Step 1: Process all matrices with default settings
python scripts/run_cleaning.py

# Custom data directory
python scripts/run_cleaning.py --data-dir /path/to/data --output-dir /path/to/output

# Adjust statistical thresholds
python scripts/run_cleaning.py --min-or 2.0 --min-count 200

# Enable German-to-English translation
python scripts/run_cleaning.py --translate

# Full command with all options
python scripts/run_cleaning.py \
    --data-dir Data \
    --output-dir data/processed \
    --min-or 1.5 \
    --min-count 100 \
    --translate \
    --verbose
```

#### Programmatic Usage

```python
from scripts.data_cleaning import process_all_matrices

# Process data
edges, metadata, report = process_all_matrices(
    data_dir='Data',
    output_dir='data/processed',
    min_odds_ratio=1.5,
    min_count=100,
    translate=True
)

print(f"Processed {len(edges)} disease pairs")
print(report)
```

**Output Files:**
- `disease_pairs_clean.csv` - Edge-list format with disease pairs and statistics
- `disease_metadata.csv` - Disease metadata with ICD chapter mapping
- `processing_report.txt` - Comprehensive validation report

### 2. 3D Embedding Generation (Module 1.4)

Generate 3D coordinates from adjacency matrices using multiple dimensionality reduction techniques for interactive disease network visualization.

**Prerequisite**: Adjacency matrices must be generated first by the R pipeline.

```bash
# Generate 3D coordinates using UMAP (recommended)
python scripts/generate_3d_embeddings.py --method umap

# Try different embedding methods
python scripts/generate_3d_embeddings.py --method tsne
python scripts/generate_3d_embeddings.py --method spring

# Process different stratifications
python scripts/generate_3d_embeddings.py --method umap --sex Female --year 2011-2012
```

#### Embedding Methods

| Method | Speed | Quality | Best For |
|--------|-------|---------|----------|
| `umap` | Fast (~30s) | Good global + local structure | **Recommended default** |
| `tsne` | Slow (~2-5min) | Best local clustering | Detailed cluster analysis |
| `spring` | Medium (~1-2min) | Network-aware layout | Network topology visualization |

#### Quality Validation

The pipeline automatically validates embedding quality by measuring clustering of diseases within the same ICD chapter:

- **Clustering Ratio**: between-chapter distance / within-chapter distance
- **Target**: > 1.5 (diseases in same chapter cluster together)
- **Output**: `Data/validation/embedding_quality_report.txt`

**Output Files:**
- `disease_vectors_3d.csv` - 3D coordinates (x, y, z) for each disease
- `Data/validation/3d_embedding_visualization.png` - 3D scatter plot colored by ICD chapter
- `Data/validation/embedding_quality_report.txt` - Quality metrics and validation

#### Demo/Testing

Test the embedding pipeline with synthetic data:

```bash
python scripts/demo_3d_embeddings.py
```

### 3. R Network Analysis Pipeline

The R scripts generate comorbidity networks from contingency tables.

#### Step 1: Generate Adjacency Matrices

```r
# Set working directory to project root
setwd("/path/to/Disease-Relater/Comorbidity-Networks-From-Population-Wide-Health-Data")

# Create ICD-level matrices
source("Scripts/1_Make_AdjMatrix_ICD.R")

# Create block-level matrices  
source("Scripts/1_Make_AdjMatrix_Blocks.R")

# Create chronic condition matrices
source("Scripts/1_Make_AdjMatrix_Chronic.R")
```

#### Step 2: Generate Network Files

```r
# Generate GEXF network files for visualization
source("Scripts/2_Make_NET_ICD.R")
source("Scripts/2_Make_NET_Blocks.R")
source("Scripts/2_Make_NET_Chronic.R")
```

#### Step 3: Network Properties Analysis

```r
# Calculate network metrics and properties
source("Scripts/3_Net_Properties.R")
```

### 3. Complete Workflow

```bash
# 1. Set up environment
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt

# 2. Download data from FigShare (see Data section)
# Place data in Data/ directory

# 3. Export contingency tables (required before Python pipeline)
Rscript scripts/export_contingency_tables.R

# 4. Run Python cleaning pipeline
python scripts/run_cleaning.py --data-dir Data --output-dir data/processed --translate

# 5. Run R analysis pipeline to generate adjacency matrices
Rscript -e "setwd('Comorbidity-Networks-From-Population-Wide-Health-Data'); source('Scripts/1_Make_AdjMatrix_ICD.R')"

# 6. Generate 3D embeddings for visualization
python scripts/generate_3d_embeddings.py --method umap --data-dir Data --output-dir data/processed
```

## Data Requirements

### Download Data

Due to size constraints, data files are hosted on FigShare. Download and place them in the following structure:

```
Data/
├── Data/
│   ├── 1.Prevalence/
│   │   └── Prevalence_Sex_Age_Year_ICD.csv
│   ├── 2.ContingencyTables/
│   │   ├── exported/                           # Generated by scripts/export_contingency_tables.R
│   │   │   ├── ICD_ContingencyTables_Male_year_2003-2004_pvalues.csv
│   │   │   ├── ICD_ContingencyTables_Male_year_2003-2004_counts.csv
│   │   │   ├── ICD_ContingencyTables_Male_year_2003-2004_odds_ratios.csv
│   │   │   └── ... (252 CSV files total)
│   │   ├── ICD_ContingencyTables_Male_Final.rds
│   │   ├── ICD_ContingencyTables_Female_Final.rds
│   │   ├── Blocks_ContingencyTables_Male_Final.rds
│   │   ├── Blocks_ContingencyTables_Female_Final.rds
│   │   ├── Chronic_ContingencyTables_Male_Final.rds
│   │   └── Chronic_ContingencyTables_Female_Final.rds
│   └── 3.AdjacencyMatrices/
│       ├── Adj_Matrix_Male_ICD_year_2003-2004.csv
│       ├── Adj_Matrix_Female_ICD_year_2003-2004.csv
│       └── ... (82 total files)
├── ICD10_Diagnoses_All.csv
├── Blocks_All.csv
└── Chronic_All.csv
```

**Data Download Links:**
- [FigShare Repository](https://figshare.com/) (links in original README)

## Configuration

### Python Pipeline Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--data-dir` | `Data` | Root data directory |
| `--output-dir` | `data/processed` | Output directory |
| `--min-or` | `1.5` | Minimum odds ratio threshold |
| `--min-count` | `100` | Minimum patient count |
| `--translate` | `False` | Enable German→English translation |
| `--verbose` | `False` | Enable detailed logging |

### R Pipeline Parameters

Edit the R scripts to adjust:
- `num_diag`: Number of diagnoses (1080 for ICD, 131 for Blocks, 46 for Chronic)
- `all_years`: Year ranges (default: seq(2003, 2014, by = 2))
- `all_ages`: Age groups (default: seq(1, 16, by = 2))
- Statistical thresholds: p-value < 0.05, OR > 1.5, min cases = 100

### 3D Embedding Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--method` | `umap` | Embedding algorithm: umap, tsne, or spring |
| `--sex` | `Male` | Patient sex stratification: Male or Female |
| `--year` | `2013-2014` | Year period for data |
| `--data-dir` | `Data` | Root data directory |
| `--output-dir` | `data/processed` | Output directory |

**Algorithm-Specific Parameters:**

UMAP (via `embed_umap()`):
- `n_neighbors`: Number of neighbors for local structure (default: 15)
- `min_dist`: Minimum distance between points (default: 0.1)

t-SNE (via `embed_tsne()`):
- `perplexity`: Effective number of neighbors (default: 30, range: 5-50)
- `max_iter`: Number of optimization iterations (default: 1000)

Spring Layout (via `embed_spring_layout()`):
- `k`: Optimal distance between nodes (default: 0.5)
- `iterations`: Convergence iterations (default: 100)

## Output Files

### Python Pipeline Outputs

**disease_pairs_clean.csv:**
- `disease_1_code`, `disease_2_code`: Disease identifiers
- `disease_1_name_de`, `disease_2_name_de`: German names
- `disease_1_name_en`, `disease_2_name_en`: English translations
- `odds_ratio`: Association strength
- `p_value`: Statistical significance
- `patient_count`: Co-occurrence count
- `sex`, `stratum_type`, `stratum_value`: Stratification info
- `granularity`: ICD/Blocks/Chronic
- `icd_chapter_1`, `icd_chapter_2`: ICD-10 chapters

**disease_metadata.csv:**
- Disease codes, names (DE/EN), ICD chapters, prevalence rates

**disease_vectors_3d.csv:**
- `icd_code`: Disease identifier
- `vector_x`, `vector_y`, `vector_z`: 3D coordinates (normalized to [-1, 1])

**3D Embedding Validation:**
- `Data/validation/3d_embedding_visualization.png` - 3D scatter plot colored by ICD chapter
- `Data/validation/embedding_quality_report.txt` - Clustering quality metrics

### R Pipeline Outputs

**Adjacency Matrices:**
- Space-separated CSV files with odds ratios

**Network Files (GEXF):**
- Gephi-compatible network files with node positions and attributes

**Visualizations:**
- PNG plots of network properties and distributions

## Development

### Using uv for Development

```bash
# Create development environment
uv venv
source .venv/bin/activate

# Install in editable mode
uv pip install -e .

# Add new dependencies
uv pip install <package>
uv pip freeze > requirements.txt

# Run tests (when available)
uv run pytest
```

### Code Style

- Python: Follow PEP 8 with docstrings for all functions
- R: Follow AGENTS.md guidelines in project root
- Comments: Explain "why" not just "what"

## Troubleshooting

### Common Issues

**Issue:** `ModuleNotFoundError: No module named 'pyreadr'`
```bash
# Solution: Install with uv
uv pip install pyreadr>=0.5.0
```

**Issue:** `FileNotFoundError: Data directory not found`
```bash
# Solution: Ensure data is downloaded and placed correctly
ls Data/Data/3.AdjacencyMatrices/
```

**Issue:** R package installation fails
```r
# Solution: Install dependencies manually
install.packages("igraph")
install.packages("dplyr")
# etc.
```

**Issue:** Translation fails or is slow
```bash
# Solution: Check internet connection or disable translation
python scripts/run_cleaning.py  # without --translate flag
```

**Issue:** `ERROR: Exported CSV files not found`
```bash
# Solution: Run the R export script first
Rscript scripts/export_contingency_tables.R

# Then run Python pipeline
python scripts/run_cleaning.py
```

**Issue:** R export script fails or produces empty CSVs
```r
# Solution: Check R version and install required packages
R --version  # Should be 4.0+
Rscript -e "install.packages('stats')"  # Usually included in base R
```

**Issue:** Report shows "P-values available: X / Y" with missing values
```bash
# This is normal and can occur for several reasons:

# 1. Export still running (ICD Male takes 30-60 minutes)
# Check progress:
ls Data/Data/2.ContingencyTables/exported/ | grep ICD_ContingencyTables_Male | wc -l
# Should show 42 files when complete (14 stratifications × 3 file types)

# 2. Statistical tests failed for some disease pairs
# The R script attempts Mantel-Haenszel test first, then falls back to Fisher's exact test
# If both fail (insufficient data), p-value is set to NA

# 3. Export was interrupted
# Solution: Simply re-run the export script - it will continue where it left off
Rscript scripts/export_contingency_tables.R
```

**Issue:** `ModuleNotFoundError: No module named 'umap'` or similar
```bash
# Solution: Install ML dependencies
pip3 install networkx scikit-learn umap-learn matplotlib scipy

# Or with uv:
uv pip install networkx scikit-learn umap-learn matplotlib scipy
```

**Issue:** `FileNotFoundError: Adjacency matrix not found`
```bash
# Solution: Run R scripts to generate adjacency matrices first
Rscript -e "setwd('Comorbidity-Networks-From-Population-Wide-Health-Data'); source('Scripts/1_Make_AdjMatrix_ICD.R')"

# Then re-run 3D embedding script
python scripts/generate_3d_embeddings.py --method umap
```

**Issue:** Embedding quality ratio < 1.5 (clustering check fails)
```bash
# Solution: Try a different embedding method
tpython scripts/generate_3d_embeddings.py --method tsne  # Often better for local clusters
python scripts/generate_3d_embeddings.py --method spring  # Network-aware layout

# Or adjust UMAP parameters for more structure
# Edit scripts/generate_3d_embeddings.py and increase n_neighbors
```

### Performance Tips

- ICD matrices (1080×1080) take longest to process
- Use `--verbose` flag to monitor progress
- Translation requires internet and adds processing time
- Consider processing subsets for testing

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Citation

If you use this software in your research, please cite:

```
Dervic, E. H. et al. Comorbidity Networks From Population-Wide Health Data: 
Aggregated Data of 8.9M Hospital Patients (1997-2014).
```

## License

MIT License - see LICENSE file for details

## Contact

- **Primary Contact:** Elma H. Dervic (dervic@csh.ac.at)
- **Project Page:** https://vis.csh.ac.at/comorbidity_networks/
- **Issues:** Please use GitHub Issues for bug reports

## Resources

- **Web Application:** https://vis.csh.ac.at/comorbidity_networks/
- **Documentation:** See individual README files in subdirectories
- **R Guidelines:** AGENTS.md in project root
- **Data:** FigShare repository (links in Comorbidity-Networks-From-Population-Wide-Health-Data/README.md)

---

**Last Updated:** January 2026
