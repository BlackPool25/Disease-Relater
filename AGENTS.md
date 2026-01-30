# AGENTS.md - Coding Guidelines for Disease-Relater Project

## Project Overview

Dual-language research project (R + Python) analyzing comorbidity networks from Austrian hospital data (8.9M patients, 1997-2014). R handles network analysis; Python handles data cleaning.

## Build/Run Commands

### Python

```bash
# Run pipeline
python scripts/run_cleaning.py --data-dir Data --output-dir data/processed

# Code quality (from pyproject.toml)
black scripts/           # Format code
flake8 scripts/          # Lint
mypy scripts/            # Type check
pytest tests/ -v         # Run all tests
pytest tests/test_specific.py::test_function -v  # Run single test
```

### R

```bash
# Execute R scripts
Rscript scripts/export_contingency_tables.R
Rscript Comorbidity-Networks-From-Population-Wide-Health-Data/Scripts/1_Make_AdjMatrix_ICD.R

# Or in R console:
setwd("Comorbidity-Networks-From-Population-Wide-Health-Data")
source("Scripts/1_Make_AdjMatrix_ICD.R")
```

## Code Style Guidelines

### Python (PEP 8 + Black)

**Imports:** Group: stdlib → third-party → local. Sort alphabetically within groups.

```python
import os
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from data_cleaning import process_all_matrices
```

**Formatting:** Line length: 88 characters (Black). Use double quotes. No trailing whitespace.

**Types:** Use type hints for all function signatures. Use `Optional[Type]` for nullable values.

**Naming:** Functions/variables: `snake_case`. Classes: `PascalCase`. Constants: `UPPER_CASE`. Private: `_leading_underscore`.

**Error Handling:** Use specific exceptions, not bare `except:`. Log errors with `logger.exception()`.

```python
try:
    result = risky_operation()
except FileNotFoundError as e:
    logger.error(f"File not found: {e}")
    raise
except Exception as e:
    logger.exception("Unexpected error")
    return None
```

### R (Tidyverse Style)

**File Headers:**
```r
#_____________________________________________________________#
#  Script Purpose Description
# 
# @Elma Hot Dervic
# September 2024
#
# INPUT: "Data/2.ContingencyTables/Filename.rds"
# OUTPUTS: paste0("Data/3.AdjacencyMatrices/Output", ".csv")
#_____________________________________________________________#
```

**Naming:** Variables: `descriptive_names`. Matrices: `Uppercase.Abbreviations` (e.g., `OR`, `P.value`). Files: `1_Make_{Type}_{Granularity}.R`.

**Structure:** 2-space indentation. Section headers with asterisks:
```r
# *************** YEARS ***********************************************
```

**Data Cleaning:**
```r
OR[is.na(OR)] <- 0
OR[is.nan(OR)] <- 0
OR[is.infinite(OR)] <- 0
```

## Project Structure

```
scripts/                    # Python cleaning pipeline
  data_cleaning.py         # Core processing module
  run_cleaning.py          # CLI entry point
  export_contingency_tables.R  # R export script

Comorbidity-Networks-From-Population-Wide-Health-Data/Scripts/  # R analysis
  1_Make_AdjMatrix_*.R     # Create adjacency matrices
  2_Make_NET_*.R          # Generate network files
  3_Net_Properties.R      # Network metrics

Data/
  Data/1.Prevalence/       # Prevalence data
  Data/2.ContingencyTables/ # Input .rds + exported/ CSVs
  Data/3.AdjacencyMatrices/ # Output matrices

pyproject.toml            # Python config
requirements.txt          # Python dependencies
```

## Key Parameters

- ICD: 1080 diseases, Blocks: 131, Chronic: 46
- Years: 2003-2014 (2-year intervals)
- Statistical thresholds: p < 0.05, OR > 1.5, min 100 cases

## Testing

- Python: Add tests in `tests/` directory
- No formal R test suite (research code - focus on reproducibility)
- Validate output CSVs have expected columns

## Data Flow

1. Export contingency tables: `export_contingency_tables.R`
2. Run Python pipeline: `run_cleaning.py`
3. Optional R analysis: `1_Make_AdjMatrix_*.R` → `2_Make_NET_*.R`

## Notes for Agents

1. Check data files exist before processing (large files on FigShare)
2. Always run R export before Python pipeline
3. Maintain parallel Male/Female structures in R
4. Use pandas `read_csv()` with `na_values` for exported CSVs
5. Network node positions: `R-files/NodesPosition1080.csv`
