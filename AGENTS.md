# AGENTS.md - Coding Guidelines for Comorbidity Networks Project

## Project Overview

R-based research project analyzing comorbidity networks from population-wide health data (8.9M Austrian hospital patients, 1997-2014). Creates adjacency matrices, GEXF network files, and visualizations for ICD-10 codes, ICD blocks, and chronic conditions.

## Build/Run Commands

Since this is a research project without formal build system:

**Run R Script:**
```r
setwd("/path/to/Comorbidity-Networks-From-Population-Wide-Health-Data")
source("Scripts/1_Make_AdjMatrix_ICD.R")
```

**Execute in R Console:**
```bash
Rscript Scripts/1_Make_AdjMatrix_ICD.R
```

**No formal test suite** - This is a research analysis project with data processing pipelines.

## Required R Packages

```r
library(igraph)      # Network analysis
library(dplyr)       # Data manipulation
library(rgexf)       # GEXF file generation
library(stringr)     # String manipulation
library(ggplot2)     # Visualization
library(cowplot)     # Plot arrangement
library(ggpubr)      # Publication-ready plots
library(ggalluvial)  # Alluvial diagrams
library(RColorBrewer)# Color palettes
```

## Code Style Guidelines

### File Headers
Every script must include a header comment with:
- Script purpose/description
- Author (@Elma Hot Dervic)
- Date (Month Year format)
- INPUT files (with paths)
- OUTPUT files (with paths)

```r
#_____________________________________________________________#
#  Script Purpose Description
# 
# @Elma Hot Dervic
# September 2024
#
# INPUT:
# "Data/2.ContingencyTables/Filename.rds"
#
# OUTPUTS:
# paste0("Data/3.AdjacencyMatrices/Output_File", variable, ".csv")
#_____________________________________________________________#
```

### Naming Conventions

**Variables:**
- Use descriptive names (e.g., `num_diag`, `all_years`, `CTables`)
- Temporary loop variables: `i`, `k`, `ii`
- Matrices: Uppercase abbreviations (e.g., `OR`, `P.value`, `CI_1`)
- Data frames: lowercase with underscores (e.g., `nodes_new`, `node_colors`)

**Files:**
- Prefix with number indicating execution order: `1_Make_`, `2_Make_`, `3_`
- Use descriptive names: `AdjMatrix`, `NET`, `Net_Properties`
- Suffix with data type: `_ICD.R`, `_Blocks.R`, `_Chronic.R`

### Code Structure

**Section Separators:**
```r
# *************** YEARS ***********************************************
# ************* MALE ******************
# ************* FEMALE ******************
# *************** AGE GROUPS ***********************************************
```

**Spacing:**
- Empty lines before/after code blocks and loops
- Indent with 2 spaces inside loops and conditionals
- Line breaks between major sections

### Data Processing Patterns

**Reading Data:**
```r
CTables <- readRDS("Data/2.ContingencyTables/Filename.rds")
str(CTables)  # Always inspect structure
```

**Matrix Operations:**
```r
P.value <- matrix(0, num_diag, num_diag)
OR <- matrix(0, num_diag, num_diag)
```

**Data Cleaning:**
```r
OR[is.na(OR)] <- 0
OR[is.nan(OR)] <- 0
OR[is.infinite(OR)] <- 0
```

**Writing Output:**
```r
write.table(OR, paste0("Data/3.AdjacencyMatrices/Adj_Matrix_Male_ICD_year_", year_matched,"-", (year_matched+1), ".csv"), row.names = F, col.names = F)
saveRDS(OR, paste0("Data/3.AdjacencyMatrices/Adj_Matrix_Male_ICD_year_", year_matched,"-", (year_matched+1), ".rds"))
```

### Visualization Standards

**ggplot2 Theme:**
```r
theme_bw(base_size=9*96/72) +
theme(
  panel.background = element_rect(fill = NA),
  panel.grid = element_line(colour = "lightgrey", size=0.2),
  axis.line = element_line(size = 0.5, colour = "darkgrey"),
  panel.ontop = FALSE,
  panel.border = element_blank(),
  legend.title = element_blank(),
  axis.text = element_text(size = 12),
  axis.title = element_text(size = 12)
)
```

### XML Sanitization

When preparing text for GEXF files, always sanitize special characters:
```r
data$column <- gsub("&", "&amp;", data$column)
data$column <- gsub("<", "&lt;", data$column)
data$column <- gsub(">", "&gt;", data$column)
data$column <- gsub("\"", "&quot;", data$column)
data$column <- gsub("'", "&apos;", data$column)
```

### Error Handling

**NULL Assignment Pattern:**
```r
test <- NULL
test <- mantelhaen.test(...)  # Function that might fail
```

**Safe Matrix Indexing:**
```r
if(length(data)>4){
  if(nrow(data)>2){
    # Process data
  }
}
```

## Data Directory Structure

```
Data/
├── 1.Prevalence/          # Prevalence data
├── 2.ContingencyTables/   # Input contingency tables (.rds)
├── 3.AdjacencyMatrices/   # Output matrices (.csv, .rds)
└── 4.Graphs-gexffiles/    # Output network files (.gexf)
```

## Key Analysis Parameters

- `num_diag`: 1080 (ICD), 131 (Blocks), 46 (Chronic)
- `all_years`: seq(2003, 2014, by = 2)
- `all_ages`: seq(1, 16, by = 2)
- Statistical threshold: p-value < 0.05, OR > 1.5, min cases = 100

## Python Notebooks

One example notebook exists (`Example_PythonScript.ipynb`) demonstrating Python equivalent using:
- `pyreadr` for reading R .rds files
- `igraph` Python library for network analysis
- `matplotlib`/`seaborn` for visualization

## Notes for Agents

1. Always maintain working directory at project root before running scripts
2. Data files are large and stored externally (FigShare) - check README for download instructions
3. This is research code - focus on reproducibility rather than formal testing
4. Color schemes follow ICD chapter organization (predefined RGB values)
5. Network node positions are predefined in `R-files/NodesPosition1080.csv`
6. Maintain parallel structure for Male/Female analysis sections
