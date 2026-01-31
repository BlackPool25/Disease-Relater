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
├── api/                                    # FastAPI REST API
│   ├── main.py                             # FastAPI application entry point (Agent 1)
│   ├── config.py                           # Pydantic settings & env validation
│   ├── dependencies.py                     # Dependency injection (Supabase client)
│   ├── validation.py                       # Input validation (ICD codes, etc.)
│   ├── routes/
│   │   ├── health.py                       # Health check endpoints (Agent 1)
│   │   ├── calculate.py                    # Risk calculator endpoint (Agent 3)
│   │   └── __init__.py
│   ├── services/
│   │   ├── risk_calculator.py              # Risk calculation logic (Agent 3)
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── calculate.py                    # Risk calculator Pydantic models (Agent 3)
│   │   └── __init__.py
│   ├── middleware/
│   │   ├── error_handlers.py               # Custom exception handlers
│   │   └── __init__.py
│   ├── types.ts                            # TypeScript type definitions
│   └── endpoints.md                        # API documentation
├── scripts/                                # Python data cleaning & embeddings
│   ├── data_cleaning.py                    # Core cleaning module
│   ├── run_cleaning.py                     # CLI entry point
│   ├── translate_descriptions.py          # ICD-10 German→English translation (Module 1.2)
│   ├── create_master_database.py           # Create unified master databases (Module 1.3)
│   ├── generate_3d_embeddings.py           # Generate 3D disease coordinates (Module 1.4)
│   ├── validate_data.py                    # Pre-import data validation (Module 1.5)
│   ├── import_to_database.py               # PostgreSQL/Supabase import (Module 1.5)
│   ├── verify_indexes.py                   # Database index verification
│   ├── benchmark_queries.py                # Query performance benchmarking
│   ├── db_queries.py                       # Database query functions
│   ├── demo_3d_embeddings.py               # Demo script for testing embeddings
│   ├── migrations/                         # SQL migration files
│   │   └── 001_add_composite_index.sql     # Composite index migration
│   └── export_contingency_tables.R         # R export script (required)
├── tests/                                  # Unit and integration tests
│   ├── __init__.py
│   ├── test_risk_calculator.py             # Risk calculator tests (Agent 3)
│   ├── test_pull_vectors.py                # Pull vector calculation tests (Agent 2)
│   └── test_database_indexes.py            # Database index verification tests
├── requirements.txt                        # Python dependencies
├── pyproject.toml                          # Modern Python project config
├── .env.example                            # Environment variable template
├── README.md                               # This file
└── README_DATA_CLEANING.md                 # Python pipeline details
```

## Quick Start

### Prerequisites

- Python 3.10 or higher
- R 4.0 or higher
- uv (Python package manager) - **strongly recommended**
- Git

### Installation

#### Option 1: Using uv (Recommended - Fastest & Most Reliable)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone <repository-url>
cd Disease-Relater

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python packages (ultra-fast with uv)
uv pip install -r requirements.txt

# Or install in editable mode (for development)
uv pip install -e .
```

#### Option 2: Using pip (Legacy - Slower)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (slower than uv)
pip install -r requirements.txt
```

#### Option 3: Using conda

```bash
# Create environment
conda create -n disease-relater python=3.10
conda activate disease-relater

# Install dependencies via pip
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

### 3. Database Import Pipeline (Module 1.5)

Import processed data into PostgreSQL/Supabase for production use. The import handles data merging and preserves all 1,080 ICD codes.

**Prerequisites**: Data validation and cleaning must be complete.

#### Data Validation

Validate all CSV files before import to check for corruption and discrepancies:

```bash
# Basic validation
python scripts/validate_data.py

# Detailed validation with discrepancy analysis
python scripts/validate_data.py --verbose --exit-on-error

# Validate specific directory
python scripts/validate_data.py --data-dir /path/to/processed/data
```

**What validation checks:**
- File existence and non-empty
- Required columns present
- Data types valid (numeric columns contain numbers)
- No extreme outliers (possible corruption)
- Data discrepancies between datasets (736 vs 1,080 diseases)

**Data Discrepancy Handling:**
The validation will report:
- `diseases_master.csv`: 736 diseases with names, chapters, prevalence
- `disease_vectors_3d.csv`: 1,080 diseases with 3D coordinates
- Overlap: ~569 diseases in both files

The import script automatically merges these with an outer join to preserve all 1,080 ICD codes.

#### Database Import

Import validated data into PostgreSQL:

```bash
# Set environment variables
export SUPABASE_URL="postgresql://user:pass@host:5432/database"
export SUPABASE_KEY="your-service-role-key"

# Run import with pre-validation
python scripts/import_to_database.py --validate-first --verbose

# Import without validation (if already validated)
python scripts/import_to_database.py

# Custom batch size for large imports
python scripts/import_to_database.py --batch-size 500
```

**Environment Variables:**

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | PostgreSQL connection URL |
| `SUPABASE_KEY` | Yes | Service role key for authentication |
| `DB_PASSWORD` | No | Password if not in URL |

**Database Import:**

Import processed data into Supabase using the unified import script:

1. **Setup credentials:**
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase credentials from:
   # https://supabase.com/dashboard/project/gbohehihcncmlcpyxomv/settings/database
   ```

2. **Run the import:**
   ```bash
   source .venv/bin/activate
   python scripts/run_full_import.py
   ```

**Import Process:**

The script imports three datasets with proper foreign key relationships:

1. **diseases** - Master disease catalog (1,247 rows)
   - Merges `diseases_master.csv` (736) + `disease_vectors_3d.csv` (1,080)
   - Uses outer join to preserve all 1,080 ICD codes with 3D coordinates
   - Fields: `icd_code`, `name_english`, `name_german`, `chapter_code`, `granularity`, prevalence, 3D vectors

2. **disease_relationships** - Aggregated comorbidity pairs (9,232 rows)
   - From `disease_relationships_master.csv`
   - Foreign keys to diseases table
   - Fields: `odds_ratio`, `p_value`, `patient_count_total`, ICD chapters

3. **disease_relationships_stratified** - Detailed stratified pairs (74,901 rows)
   - From `disease_pairs_clean.csv`
   - Sex, age group, year stratifications
   - Individual odds ratios and p-values per stratum

**Verification:**

The script automatically verifies row counts after import:
```
diseases: 1,247 rows
disease_relationships: 9,232 rows
disease_relationships_stratified: 74,901 rows
icd_chapters: 21 rows
```

#### Database Index Verification

Verify that all required database indexes exist for optimal query performance:

```bash
# Basic index verification
python scripts/verify_indexes.py

# Verify indexes and analyze query plans
python scripts/verify_indexes.py --analyze

# Verbose output with detailed information
python scripts/verify_indexes.py --verbose
```

**Required Indexes:**
- `diseases`: `idx_diseases_icd_code`, `idx_diseases_chapter`, `idx_diseases_granularity`
- `disease_relationships`: `idx_rel_disease1`, `idx_rel_disease2`, `idx_rel_odds_ratio`, `idx_rel_composite`
- `prevalence_stratified`: `idx_prev_disease`, `idx_prev_sex`

#### Database Migrations

SQL migration files are stored in `scripts/migrations/`:

```bash
# Apply the composite index migration manually (if needed)
psql $SUPABASE_URL -f scripts/migrations/001_add_composite_index.sql
```

#### Query Performance Benchmarking

Measure query performance to verify index effectiveness:

```bash
# Run benchmarks with default 5 iterations
python scripts/benchmark_queries.py

# Run with more iterations for accuracy
python scripts/benchmark_queries.py --iterations 10

# Verbose output with timing details
python scripts/benchmark_queries.py --verbose
```

**Benchmark Output Example:**
```
================================================================================
QUERY BENCHMARK RESULTS
================================================================================
Query                                    Avg (ms)     Min (ms)     Max (ms)     Rows    
--------------------------------------------------------------------------------
Disease list (first 100)                 5.23         4.12         6.34         100     
Disease by ICD code                      1.12         0.98         1.45         1       
Relationships by both IDs (composite)    0.85         0.72         1.02         1       
================================================================================
```

### 4. R Network Analysis Pipeline

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

### 5. FastAPI Server

Run the FastAPI server for REST API access to disease data and comorbidity networks.

```bash
# 1. Set up environment variables
cp .env.example .env
# Edit .env with your Supabase credentials

# 2. Install dependencies with uv (recommended)
uv pip install -r requirements.txt

# 3. Start the development server
uvicorn api.main:app --reload --port 5000

# 4. Test the health endpoint
curl http://localhost:5000/api/health
```

**Available Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/api` | Available endpoints |
| GET | `/api/health` | Health check |
| GET | `/api/ready` | Readiness probe (K8s) |
| GET | `/api/live` | Liveness probe (K8s) |
| GET | `/docs` | API documentation (Swagger) |

**Configuration:**

Server settings are loaded from environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SUPABASE_URL` | Required | Supabase project URL |
| `SUPABASE_KEY` | Required | Supabase API key |
| `HOST` | 0.0.0.0 | Server bind host |
| `PORT` | 5000 | Server port |
| `CORS_ORIGINS` | localhost | Allowed origins |
| `API_RATE_LIMIT` | 100 | Requests per minute per IP |
| `MAX_REQUEST_SIZE` | 1048576 | Max request size in bytes (1MB) |
| `DEBUG` | false | Debug mode |

**Security Features:**

- **Rate Limiting**: 100 requests per minute per IP address (configurable via `API_RATE_LIMIT`)
  - Custom 429 response with structured JSON error format
  - Rate limit headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`
  - Secure IP extraction: X-Forwarded-For only trusted when `TRUST_PROXY=true`
- **Request Size Limiting**: Maximum 1MB request size (configurable via `MAX_REQUEST_SIZE`)
- **Error Sanitization**: Error messages are sanitized to prevent information leakage
- **CORS Protection**: Configurable allowed origins

**Logging & Monitoring:**

- **Request Logging**: All requests logged with method, path, client IP, and response time
- **Response Time Header**: `X-Response-Time` header added to all responses (in milliseconds)
- **File Logging**: Requests and errors logged to `logs/api.log` with rotation (10MB max, 5 backups)
- **Log Format**: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

### 6. Complete Workflow

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

# 5. Create master databases (merges all data sources)
python scripts/create_master_database.py

# 6. Run R analysis pipeline to generate adjacency matrices
Rscript -e "setwd('Comorbidity-Networks-From-Population-Wide-Health-Data'); source('Scripts/1_Make_AdjMatrix_ICD.R')"

# 7. Generate 3D embeddings for visualization
python scripts/generate_3d_embeddings.py --method umap --data-dir Data --output-dir data/processed

# 8. Validate data before database import
python scripts/validate_data.py --data-dir Data/processed --verbose --exit-on-error

# 9. Import into PostgreSQL/Supabase database
export SUPABASE_URL="postgresql://user:pass@host:5432/database"
export SUPABASE_KEY="your-service-role-key"
python scripts/import_to_database.py --validate-first --verbose

# 10. Start the FastAPI server
uvicorn api.main:app --reload --port 5000
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

### Database Import Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--data-dir` | `Data/processed` | Directory containing CSV files |
| `--validate-first` | `False` | Run validation before import |
| `--skip-stratified` | `False` | Skip stratified prevalence import |
| `--batch-size` | `1000` | Rows per insert batch |
| `--verbose` | `False` | Detailed logging output |

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

**Master Database Files (in `Data/processed/`):**

**diseases_master.csv** (Module 1.3):
- 736 diseases with names, chapters, and prevalence rates
- `icd_code`, `name_english`, `name_german`, `chapter_code`, `chapter_name`
- `granularity` (ICD/Blocks/Chronic)
- `avg_prevalence_male`, `avg_prevalence_female`

**disease_relationships_master.csv** (Module 1.3):
- 9,232 aggregated disease relationships
- `disease_1_code`, `disease_2_code`, `odds_ratio_avg`, `p_value_avg`
- `patient_count_total`, `icd_chapter_1`, `icd_chapter_2`

**data_summary.json** (Module 1.3):
- Statistics summary of all processed data
- Row counts, column names, data quality metrics

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

## Database & API

### Supabase Database

The project uses Supabase PostgreSQL for storing and serving disease data.

**Database URL:** `https://gbohehihcncmlcpyxomv.supabase.co`

**Tables:**
- `diseases` - 1,080 ICD codes with names, prevalence, and 3D coordinates
- `disease_relationships` - 9,232 aggregated comorbidity relationships
- `disease_relationships_stratified` - 74,901 detailed relationships by sex/age/year
- `icd_chapters` - 21 standard ICD-10 chapters

**Views:**
- `diseases_complete` - Full disease metadata with chapter names
- `top_relationships` - Top comorbidities ranked by odds ratio
- `disease_network_stats` - Connection counts and network metrics

**Functions:**
- `search_diseases('diabetes')` - Search by name
- `get_connected_diseases('E11')` - Get related diseases

### Query Module

Use the Python query module for database access:

```python
from scripts.db_queries import DatabaseQueries
from supabase import create_client

# Initialize client
supabase = create_client(url, key)
db = DatabaseQueries(supabase)

# 5 core query functions
disease = db.get_disease_by_code('E11')                          # Query 1
diseases = db.get_diseases_by_chapter('IX', limit=50)           # Query 2
related = db.get_related_diseases('E11', limit=20)              # Query 3
network = db.get_network_data(min_odds_ratio=5.0)               # Query 4
prevalence = db.get_prevalence_for_demographics('E11', 'Female') # Query 5

# Utility functions
results = db.search_diseases('diabetes', limit=10)
stats = db.get_disease_statistics()
chapters = db.get_chapter_statistics()
```

See `scripts/db_queries.py` for full documentation.

### REST API

**Base URL:** `https://gbohehihcncmlcpyxomv.supabase.co/rest/v1/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/diseases` | List all diseases |
| GET | `/diseases?icd_code=eq.{code}` | Get disease by ICD code |
| GET | `/diseases?chapter_code=eq.{chapter}` | Get diseases by chapter |
| GET | `/disease_relationships` | Get related diseases |
| GET | `/diseases_complete` | Full disease data |
| GET | `/top_relationships` | Top comorbidities |

**Example:**
```bash
curl 'https://gbohehihcncmlcpyxomv.supabase.co/rest/v1/diseases?icd_code=eq.E11' \
  -H 'apikey: <your-api-key>'
```

See `api/endpoints.md` for complete documentation.

### FastAPI Server

Self-hosted FastAPI server with improved query capabilities:

**Installation:**
```bash
# Using uv (recommended - much faster)
uv pip install -r requirements.txt

# Or with pip (slower)
pip install fastapi uvicorn pydantic supabase
```

**Run the server:**
```bash
# Set environment variables
cp .env.example .env
# Edit .env with your Supabase credentials

# Start server
uvicorn api.main:app --host 0.0.0.0 --port 5000 --reload

# Or using Python
python api/main.py
```

**GET Endpoints:**

| Method | Endpoint | Description | Query Parameters |
|--------|----------|-------------|------------------|
| GET | `/api/diseases` | List diseases | `chapter`, `limit`, `offset` |
| GET | `/api/diseases/{id}` | Get disease by ID or ICD | - |
| GET | `/api/diseases/{id}/related` | Get related diseases | `limit`, `min_odds_ratio` |
| GET | `/api/diseases/search/{term}` | Search diseases | `limit` |
| GET | `/api/network` | Get network data | `min_odds_ratio`, `max_edges`, `chapter_filter` |
| GET | `/api/chapters` | List ICD chapters | - |

**Examples:**
```bash
# List diseases with chapter filter
curl "http://localhost:5000/api/diseases?chapter=IX&limit=10"

# Get disease by ICD code
curl "http://localhost:5000/api/diseases/E11"

# Get related diseases
curl "http://localhost:5000/api/diseases/E11/related?limit=10&min_odds_ratio=5.0"

# Search diseases
curl "http://localhost:5000/api/diseases/search/diabetes?limit=5"

# Get network data
curl "http://localhost:5000/api/network?min_odds_ratio=5.0&chapter_filter=IX"

# List chapters
curl "http://localhost:5000/api/chapters"
```

### Risk Calculator API

**Endpoint:** `POST /api/calculate-risk`

Calculate personalized disease risk scores based on existing conditions and demographics.

**Request Body:**
```json
{
  "age": 45,
  "gender": "male",
  "bmi": 28.5,
  "existing_conditions": ["E11", "I10"],
  "exercise_level": "moderate",
  "smoking": false
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `age` | integer | Yes | Age in years (1-120) |
| `gender` | string | Yes | "male" or "female" |
| `bmi` | float | Yes | Body Mass Index (10-60) |
| `existing_conditions` | array | Yes | List of ICD-10 codes (1-50 items) |
| `exercise_level` | string | Yes | "sedentary", "light", "moderate", "active" |
| `smoking` | boolean | Yes | Current smoking status |

**Response:**
```json
{
  "risk_scores": [
    {
      "disease_id": "E13",
      "disease_name": "Other specified diabetes",
      "risk": 0.8234,
      "level": "very_high",
      "contributing_factors": [
        "Odds ratio: 15.50 from E11",
        "Very strong relationship",
        "Elevated BMI (overweight)",
        "Middle age"
      ]
    }
  ],
  "user_position": {
    "x": 0.2341,
    "y": -0.1452,
    "z": 0.6789
  },
  "pull_vectors": [
    {
      "disease_id": "E13",
      "disease_name": "Other specified diabetes",
      "risk": 0.8234,
      "vector_x": 0.234,
      "vector_y": -0.156,
      "vector_z": 0.089,
      "magnitude": 0.295
    }
  ],
  "total_conditions_analyzed": 2,
  "analysis_metadata": {
    "conditions_processed": ["E11", "I10"],
    "related_diseases_found": 15,
    "gender": "male",
    "age": 45
  }
}
```

**User Position:**
- `x`, `y`, `z`: Coordinates bounded to [-1.0, 1.0] range
- Computed as weighted average of existing conditions' 3D disease space coordinates
- Uses prevalence as weights (defaults to 1.0 if missing)

**Pull Vectors:**

Directional vectors from user position toward high-risk diseases (risk > 0.3), scaled by risk score.
Used for visualization to show which diseases are "pulling" the user in the 3D disease network space.

| Field | Description |
|-------|-------------|
| `disease_id` | ICD-10 code of the high-risk disease |
| `disease_name` | English name of the disease |
| `risk` | Risk score that triggered this pull vector |
| `vector_x/y/z` | Direction components, scaled by risk |
| `magnitude` | Vector length: sqrt(x² + y² + z²) |

Pull vectors are sorted by magnitude (strongest pull first).

**Risk Levels:**

| Level | Score Range | Description |
|-------|-------------|-------------|
| `low` | 0.00 - 0.24 | Minimal risk |
| `moderate` | 0.25 - 0.49 | Moderate risk |
| `high` | 0.50 - 0.74 | High risk |
| `very_high` | 0.75 - 1.00 | Very high risk |

**Example Request:**
```bash
curl -X POST "http://localhost:5000/api/calculate-risk" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 45,
    "gender": "male",
    "bmi": 28.5,
    "existing_conditions": ["E11", "I10"],
    "exercise_level": "moderate",
    "smoking": false
  }'
```

**Algorithm Overview:**

The risk calculator uses a four-stage multiplicative pipeline:

1. **Base Risk (Prevalence):** Uses population prevalence as the base risk score
   ```
   base_risk[disease] = prevalence[disease][sex]
   ```

2. **Comorbidity Multipliers:** Applies multiplicative odds ratios from disease relationships
   ```
   risk[disease] *= odds_ratio[existing_condition, disease]
   ```

3. **Lifestyle Adjustments:** Category-specific multiplicative factors
   
   | Category | Factor | Multiplier |
   |----------|--------|------------|
   | Metabolic (E) | BMI >= 30 (obese) | 1.5x |
   | Metabolic (E) | BMI 25-30 (overweight) | 1.2x |
   | Cardiovascular (I) | Smoking | 1.8x |
   | Cardiovascular (I) | Sedentary/light exercise | 1.3x |
   | Cardiovascular (I) | Active exercise | 0.7x (protective) |
   | Respiratory (J) | Smoking | 1.6x |

4. **Age Adjustments:** Category-specific age multipliers
   
   | Age Group | Metabolic | Cardiovascular | Respiratory |
   |-----------|-----------|----------------|-------------|
   | Elderly (65+) | 1.3x | 1.5x | 1.2x |
   | Middle (45-64) | 1.15x | 1.25x | 1.1x |
   | Young adult (30-44) | 1.0x | 1.0x | 1.0x |
   | Young (<30) | 0.8x | 0.7x | 0.9x |

5. **User Position:** Weighted average of 3D disease coordinates using prevalence as weights
   - Input coordinates are validated and clamped to [-1, 1] range
   - Missing coordinates default to 0.0 with debug logging
   - Zero/missing prevalence values use default weight of 1.0
   - Output coordinates are bounded to [-1, 1] range

**Files:**
- `api/routes/calculate.py` - FastAPI endpoint
- `api/services/risk_calculator.py` - Calculation logic
- `api/schemas/calculate.py` - Pydantic models with field validation
- `tests/test_risk_calculator.py` - Unit tests (33 tests)

### TypeScript Types

Generated types for frontend development:

```typescript
// api/types.ts
import { Disease, DiseaseRelationship } from './api/types';

const disease: Disease = {
  id: 1,
  icd_code: 'E11',
  name_english: 'Type 2 diabetes mellitus',
  // ...
};
```

### SQL Reference

Reference queries in `database/queries.sql`:

```sql
-- Get disease with chapter info
SELECT d.*, c.chapter_name 
FROM diseases d
LEFT JOIN icd_chapters c ON d.chapter_code = c.chapter_code
WHERE d.icd_code = 'E11';

-- Get top related diseases
SELECT * FROM get_connected_diseases('E11');

-- Search by name
SELECT * FROM search_diseases('diabetes');
```

### Schema Files

- `database/schema.sql` - Complete database schema
- `database/queries.sql` - Reference SQL queries
- `api/endpoints.md` - API documentation
- `api/types.ts` - TypeScript type definitions

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
