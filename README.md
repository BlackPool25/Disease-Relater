# Disease-Relater: Comorbidity Networks Analysis Platform

A comprehensive research platform for analyzing comorbidity networks from population-wide health data, featuring both R-based network analysis and Python-based data cleaning pipelines.

## Overview

This project provides tools to analyze comorbidity networks derived from 8.9 million Austrian hospital patients (1997-2014). It includes:

- **R Pipeline**: Network construction, analysis, and visualization (82 stratified matrices)
- **Python Pipeline**: Data cleaning, transformation, and preprocessing
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
├── scripts/                                # Python data cleaning
│   ├── data_cleaning.py                    # Core cleaning module
│   ├── run_cleaning.py                     # CLI entry point
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

### 2. R Network Analysis Pipeline

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

# 5. Run R analysis pipeline (optional, for network generation)
Rscript -e "setwd('Comorbidity-Networks-From-Population-Wide-Health-Data'); source('Scripts/1_Make_AdjMatrix_ICD.R')"
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
