# Disease-Relater API Specification

## Overview

REST API for accessing comorbidity network data from the Disease-Relater database.

**Base URL:** `https://gbohehihcncmlcpyxomv.supabase.co/rest/v1/`

**Authentication:** Requires Supabase API key in header:
```
apikey: <your-anon-key>
```

---

## API Endpoints

### 1. List All Diseases

**Endpoint:** `GET /diseases`

Returns paginated list of all diseases in the database.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `select` | string | `*` | Fields to return |
| `chapter_code` | string | - | Filter by ICD chapter |
| `limit` | integer | 100 | Maximum results (max 1000) |
| `offset` | integer | 0 | Pagination offset |
| `order` | string | `icd_code.asc` | Sort order |

**Example Request:**
```bash
curl -X GET 'https://gbohehihcncmlcpyxomv.supabase.co/rest/v1/diseases?select=id,icd_code,name_english,chapter_code&limit=10' \
  -H 'apikey: <your-api-key>'
```

**Example Response:**
```json
[
  {
    "id": 1,
    "icd_code": "A00",
    "name_english": "Cholera",
    "chapter_code": "I"
  },
  {
    "id": 2,
    "icd_code": "A01",
    "name_english": "Typhoid and paratyphoid fevers",
    "chapter_code": "I"
  }
]
```

**Related Python Function:**
```python
from scripts.db_queries import DatabaseQueries

db = DatabaseQueries(client)
diseases = db.get_diseases_by_chapter('I', limit=10)
```

---

### 2. Get Disease by ICD Code

**Endpoint:** `GET /diseases?icd_code=eq.{code}`

Returns detailed information for a specific disease.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `icd_code` | string | ICD-10 code (e.g., `E11`, `I10`) |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `select` | string | `*` | Fields to return |

**Example Request:**
```bash
curl -X GET 'https://gbohehihcncmlcpyxomv.supabase.co/rest/v1/diseases?icd_code=eq.E11&select=*' \
  -H 'apikey: <your-api-key>'
```

**Example Response:**
```json
[
  {
    "id": 532,
    "icd_code": "E11",
    "name_english": "Type 2 diabetes mellitus",
    "name_german": "Diabetes mellitus Typ 2",
    "chapter_code": "IV",
    "granularity": "ICD",
    "prevalence_male": 0.0452,
    "prevalence_female": 0.0389,
    "prevalence_total": 0.0421,
    "vector_x": -0.234,
    "vector_y": 0.888,
    "vector_z": 0.409,
    "has_english_name": true,
    "has_3d_coordinates": true,
    "has_prevalence_data": true
  }
]
```

**Related Python Function:**
```python
disease = db.get_disease_by_code('E11')
```

---

### 3. Get Diseases by Chapter

**Endpoint:** `GET /diseases?chapter_code=eq.{chapter}`

Returns all diseases within a specific ICD-10 chapter.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `chapter` | string | Chapter code (e.g., `I`, `IX`, `X`) |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 100 | Maximum results |
| `order` | string | `icd_code.asc` | Sort order |

**Example Request:**
```bash
curl -X GET 'https://gbohehihcncmlcpyxomv.supabase.co/rest/v1/diseases?chapter_code=eq.IX&select=id,icd_code,name_english,prevalence_total' \
  -H 'apikey: <your-api-key>'
```

**Example Response:**
```json
[
  {
    "id": 301,
    "icd_code": "I10",
    "name_english": "Essential hypertension",
    "prevalence_total": 0.1823
  },
  {
    "id": 302,
    "icd_code": "I11",
    "name_english": "Hypertensive heart disease",
    "prevalence_total": 0.0156
  }
]
```

**ICD Chapter Codes Reference:**

| Code | Chapter Name |
|------|--------------|
| I | Infectious and parasitic diseases |
| II | Neoplasms |
| III | Blood and immune disorders |
| IV | Endocrine, nutritional and metabolic |
| V | Mental and behavioral disorders |
| VI | Nervous system |
| VII | Eye and adnexa |
| VIII | Ear and mastoid process |
| IX | Circulatory system |
| X | Respiratory system |
| XI | Digestive system |
| XII | Skin and subcutaneous tissue |
| XIII | Musculoskeletal and connective tissue |
| XIV | Genitourinary system |
| XV | Pregnancy and childbirth |
| XVI | Perinatal conditions |
| XVII | Congenital malformations |
| XVIII | Symptoms and abnormal findings |
| XIX | Injury, poisoning and external causes |
| XX | External causes of morbidity |
| XXI | Factors influencing health status |

---

### 4. Get Related Diseases

**Endpoint:** `GET /disease_relationships`

Returns diseases with highest comorbidity (ordered by odds ratio).

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `disease_1_id` | integer | - | Filter by source disease ID |
| `or` | string | - | Query both directions (see example) |
| `odds_ratio` | string | `gte.2.0` | Minimum odds ratio threshold |
| `order` | string | `odds_ratio.desc` | Sort by odds ratio |
| `limit` | integer | 50 | Maximum results |

**Example Request - Single Direction:**
```bash
curl -X GET 'https://gbohehihcncmlcpyxomv.supabase.co/rest/v1/disease_relationships?disease_1_id=eq.532&order=odds_ratio.desc&limit=10' \
  -H 'apikey: <your-api-key>'
```

**Example Request - Bidirectional:**
```bash
curl -X GET 'https://gbohehihcncmlcpyxomv.supabase.co/rest/v1/disease_relationships?or=(disease_1_id.eq.532,disease_2_id.eq.532)&order=odds_ratio.desc&limit=10' \
  -H 'apikey: <your-api-key>'
```

**Example Response:**
```json
[
  {
    "id": 5234,
    "disease_1_id": 532,
    "disease_2_id": 845,
    "odds_ratio": 12.45,
    "p_value": 0.000001,
    "patient_count_total": 15234,
    "relationship_strength": "very_strong",
    "icd_chapter_1": "IV",
    "icd_chapter_2": "IX"
  }
]
```

**Related Python Function:**
```python
related = db.get_related_diseases('E11', limit=10, bidirectional=True)
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `odds_ratio` | float | Association strength (higher = stronger) |
| `p_value` | float | Statistical significance (lower = more significant) |
| `relationship_strength` | string | Classification: extreme, very_strong, strong, moderate, weak |
| `patient_count_total` | integer | Total co-occurrences across all strata |

---

### 5. Get Network Data

**Endpoint:** `GET /diseases` + `GET /disease_relationships`

Returns complete network data (nodes and edges) for visualization.

**Nodes Request:**
```bash
curl -X GET 'https://gbohehihcncmlcpyxomv.supabase.co/rest/v1/diseases?has_3d_coordinates=eq.true&select=id,icd_code,name_english,chapter_code,vector_x,vector_y,vector_z,prevalence_total' \
  -H 'apikey: <your-api-key>'
```

**Edges Request:**
```bash
curl -X GET 'https://gbohehihcncmlcpyxomv.supabase.co/rest/v1/disease_relationships?odds_ratio=gte.5.0&order=odds_ratio.desc&limit=1000' \
  -H 'apikey: <your-api-key>'
```

**Related Python Function:**
```python
network = db.get_network_data(min_odds_ratio=5.0)
# Returns: { 'nodes': [...], 'edges': [...], 'metadata': {...} }
```

**Node Fields for Visualization:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique node ID |
| `icd_code` | string | Disease code (label) |
| `name_english` | string | Disease name |
| `chapter_code` | string | Color by chapter |
| `vector_x/y/z` | float | 3D position coordinates |
| `prevalence_total` | float | Node size scaling |

**Edge Fields for Visualization:**

| Field | Type | Description |
|-------|------|-------------|
| `disease_1_id` | integer | Source node ID |
| `disease_2_id` | integer | Target node ID |
| `odds_ratio` | float | Edge weight/thickness |
| `relationship_strength` | string | Edge color classification |

---

### 6. Get Prevalence with Filters

**Endpoint:** `GET /diseases?icd_code=eq.{code}`

Returns prevalence data for specific demographics.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `icd_code` | string | required | Disease ICD code |
| `select` | string | `*` | Specify prevalence fields |

**Example Request:**
```bash
# Get all prevalence data for a disease
curl -X GET 'https://gbohehihcncmlcpyxomv.supabase.co/rest/v1/diseases?icd_code=eq.E11&select=icd_code,name_english,prevalence_male,prevalence_female,prevalence_total' \
  -H 'apikey: <your-api-key>'
```

**Example Response:**
```json
[
  {
    "icd_code": "E11",
    "name_english": "Type 2 diabetes mellitus",
    "prevalence_male": 0.0452,
    "prevalence_female": 0.0389,
    "prevalence_total": 0.0421
  }
]
```

**Stratified Data (by sex/age/year):**

```bash
# Get stratified relationships with prevalence details
curl -X GET 'https://gbohehihcncmlcpyxomv.supabase.co/rest/v1/disease_relationships_stratified?disease_1_id=eq.532&sex=eq.Female&select=disease_2_name_en,odds_ratio,patient_count,age_group,year_range' \
  -H 'apikey: <your-api-key>'
```

**Related Python Function:**
```python
prevalence = db.get_prevalence_for_demographics('E11', sex='Female', age_group='70-79')
```

---

## Filter Operators

Supabase REST API supports these filter operators:

| Operator | Description | Example |
|----------|-------------|---------|
| `eq` | Equal | `?icd_code=eq.E11` |
| `neq` | Not equal | `?chapter_code=neq.I` |
| `gt` | Greater than | `?odds_ratio=gt.5.0` |
| `gte` | Greater than or equal | `?odds_ratio=gte.2.0` |
| `lt` | Less than | `?p_value=lt.0.05` |
| `lte` | Less than or equal | `?p_value=lte.0.01` |
| `like` | Pattern matching | `?name_english=like.*diabetes*` |
| `ilike` | Case-insensitive like | `?name_english=ilike.*diabetes*` |
| `in` | In array | `?chapter_code=in.(I,IX,X)` |
| `is` | IS NULL / TRUE / FALSE | `?has_3d_coordinates=is.true` |
| `or` | OR condition | `?or=(a.eq.1,b.eq.2)` |
| `and` | AND condition | `?and=(a.gte.1,b.lte.10)` |

---

## Error Handling

**HTTP Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid API key |
| 404 | Not Found |
| 429 | Rate Limited |
| 500 | Server Error |

**Error Response Format:**
```json
{
  "message": "Invalid filter column",
  "code": 400,
  "hint": "Check that the column name is correct"
}
```

---

## Rate Limiting

- Default: 100 requests per minute
- Burst: 10 requests per second
- Contact support to increase limits

---

## Python Integration

### Using Supabase Client

```python
from supabase import create_client

# Initialize
supabase = create_client(
    'https://gbohehihcncmlcpyxomv.supabase.co',
    '<your-anon-key>'
)

# Query diseases
response = supabase.table('diseases') \
    .select('*') \
    .eq('icd_code', 'E11') \
    .execute()

print(response.data)
```

### Using DatabaseQueries Module

```python
from scripts.db_queries import DatabaseQueries

# Initialize with Supabase client
db = DatabaseQueries(supabase)

# Query 1: Get disease by code
disease = db.get_disease_by_code('E11')

# Query 2: Get diseases by chapter
diseases = db.get_diseases_by_chapter('IX', limit=50)

# Query 3: Get related diseases
related = db.get_related_diseases('E11', limit=20)

# Query 4: Get network data
network = db.get_network_data(min_odds_ratio=5.0)

# Query 5: Get prevalence
prevalence = db.get_prevalence_for_demographics('E11', sex='Female')

# Utility: Search diseases
results = db.search_diseases('diabetes', limit=10)

# Utility: Get statistics
stats = db.get_disease_statistics()
```

---

## TypeScript Types

See `api/types.ts` for complete TypeScript definitions:

```typescript
// Key interfaces
interface Disease {
  id: number;
  icd_code: string;
  name_english: string | null;
  name_german: string | null;
  chapter_code: string | null;
  granularity: 'ICD' | 'Blocks' | 'Chronic' | null;
  prevalence_male: number | null;
  prevalence_female: number | null;
  prevalence_total: number | null;
  vector_x: number | null;
  vector_y: number | null;
  vector_z: number | null;
}

interface DiseaseRelationship {
  id: number;
  disease_1_id: number;
  disease_2_id: number;
  odds_ratio: number;
  p_value: number | null;
  patient_count_total: number | null;
  relationship_strength: string | null;
}

// Use with Supabase client
const { data, error } = await supabase
  .from('diseases')
  .select('*')
  .eq('icd_code', 'E11');
```

---

## Data Sources

- **Diseases:** 1,080 ICD codes (merged from 736 diseases_master + 1,080 disease_vectors_3d)
- **Relationships:** 9,232 aggregated comorbidity relationships
- **Stratified Relationships:** 74,901 detailed relationships by sex/age/year
- **ICD Chapters:** 21 standard ICD-10 chapters

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-30 | Initial API specification |

---

## Contact

- **Issues:** GitHub Issues
- **Project:** https://vis.csh.ac.at/comorbidity_networks/
- **Database:** https://gbohehihcncmlcpyxomv.supabase.co
