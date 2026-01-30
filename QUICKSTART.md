# Quick Start Guide

## Installation with UV (Recommended)

This guide provides the fastest way to get started using `uv`, an extremely fast Python package manager.

### Step 1: Install UV

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip (not recommended, but works)
pip install uv
```

### Step 2: Setup Project

```bash
# Navigate to project
cd /path/to/Disease-Relater

# Create virtual environment (automatically uses project's Python version)
uv venv

# Activate environment
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows
```

### Step 3: Install Dependencies

```bash
# Option A: Install from requirements.txt
uv pip install -r requirements.txt

# Option B: Install as editable package (for development)
uv pip install -e .
```

### Step 4: Verify Installation

```bash
# Check Python version
python --version  # Should be >= 3.10

# Verify packages are installed
python -c "import pandas, numpy, pyreadr; print('All packages installed successfully')"
```

## Running the Pipeline

### Python Data Cleaning

```bash
# Basic run
python scripts/run_cleaning.py

# With all options
python scripts/run_cleaning.py \
    --data-dir Data \
    --output-dir data/processed \
    --min-or 1.5 \
    --min-count 100 \
    --translate \
    --verbose
```

### R Network Analysis

```bash
# Run R scripts
Rscript Scripts/1_Make_AdjMatrix_ICD.R
Rscript Scripts/2_Make_NET_ICD.R
Rscript Scripts/3_Net_Properties.R
```

Or from within R:
```r
source("Scripts/1_Make_AdjMatrix_ICD.R")
```

## Common UV Commands

```bash
# Install a new package
uv pip install <package-name>

# Upgrade packages
uv pip install --upgrade <package-name>

# List installed packages
uv pip list

# Save current packages to requirements.txt
uv pip freeze > requirements.txt

# Sync environment with requirements.txt
uv pip sync requirements.txt

# Run Python command in environment
uv run python script.py
```

## Troubleshooting

### UV Not Found
```bash
# Check if uv is in PATH
which uv

# If not found, add to PATH or reinstall
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Package Installation Fails
```bash
# Try with verbose output
uv pip install -v pyreadr

# Check Python version compatibility
python --version  # Must be >= 3.10
```

### Virtual Environment Issues
```bash
# Remove and recreate
rm -rf .venv
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Next Steps

1. **Download Data**: Get data from FigShare (links in main README)
2. **Run Pipeline**: Process the data with Python cleaning script
3. **Analyze Results**: Use R scripts for network analysis
4. **Explore**: Check the generated CSV files and reports

See `README.md` for complete documentation.
