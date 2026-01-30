# Disease Relater API Documentation

## Overview

- **Base URL**: `/api`
- **Version**: 1.0.0
- **Format**: JSON
- **OpenAPI Docs**: `/docs` (development mode only)

The Disease Relater API provides access to comorbidity network data derived from 8.9 million Austrian hospital patients (1997-2014). It enables researchers and healthcare applications to query disease relationships, calculate personalized risk scores, and visualize comorbidity networks in 3D space.

## Features

- Query diseases by ICD-10 code
- Find related diseases by odds ratio
- Get network data for 3D visualization
- Access 3D disease coordinates
- Calculate personalized disease risk scores
- Filter by demographics (sex, age)

## Data Sources

- 1,080 ICD-10 diseases
- 9,232 aggregated relationships
- 74,901 stratified relationships
- 3D embeddings for network visualization

## Authentication

The API is currently open access with no authentication required. Rate limiting may be implemented in production.

## Endpoints

### Health Check

#### GET /api/health

Returns API health status and database connectivity information.

**Response**: `200 OK` | `503 Service Unavailable`

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": "2026-01-30T12:00:00Z",
  "uptime_seconds": 3600
}
```

**cURL Example**:
```bash
curl -X GET http://localhost:5000/api/health
```

---

#### GET /api/ready

Kubernetes-style readiness probe endpoint.

**Response**: `200 OK` | `503 Service Unavailable`

```json
{
  "status": "ready"
}
```

**cURL Example**:
```bash
curl -X GET http://localhost:5000/api/ready
```

---

#### GET /api/live

Kubernetes-style liveness probe endpoint.

**Response**: `200 OK` | `503 Service Unavailable`

```json
{
  "status": "alive"
}
```

**cURL Example**:
```bash
curl -X GET http://localhost:5000/api/live
```

---

### Diseases

#### GET /api/diseases

Get list of diseases with optional chapter filter and pagination.

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| chapter | string | No | - | Filter by ICD chapter code (e.g., IX, X) |
| limit | integer | No | 100 | Maximum results to return (1-1000) |
| offset | integer | No | 0 | Pagination offset (0+) |

**Response**: `200 OK`

```json
{
  "diseases": [
    {
      "id": 1,
      "icd_code": "E11",
      "name_english": "Type 2 diabetes mellitus",
      "name_german": "Diabetes mellitus Typ 2",
      "chapter_code": "IV",
      "chapter_name": "Endocrine, nutritional and metabolic diseases",
      "prevalence_male": 0.085,
      "prevalence_female": 0.068,
      "prevalence_total": 0.076,
      "vector_x": -0.234,
      "vector_y": 0.567,
      "vector_z": -0.123
    }
  ],
  "total": 1080
}
```

**cURL Example**:
```bash
# List all diseases
curl -X GET http://localhost:5000/api/diseases

# Filter by chapter with pagination
curl -X GET "http://localhost:5000/api/diseases?chapter=IX&limit=50&offset=0"
```

---

#### GET /api/diseases/{disease_id}

Get single disease by ID or ICD code.

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| disease_id | string | Yes | Numeric ID or ICD code (e.g., 'E11', 'I10') |

**Response**: `200 OK` | `404 Not Found`

```json
{
  "id": 1,
  "icd_code": "E11",
  "name_english": "Type 2 diabetes mellitus",
  "name_german": "Diabetes mellitus Typ 2",
  "chapter_code": "IV",
  "chapter_name": "Endocrine, nutritional and metabolic diseases",
  "prevalence_male": 0.085,
  "prevalence_female": 0.068,
  "prevalence_total": 0.076,
  "vector_x": -0.234,
  "vector_y": 0.567,
  "vector_z": -0.123
}
```

**cURL Example**:
```bash
# Get by ICD code
curl -X GET http://localhost:5000/api/diseases/E11

# Get by numeric ID
curl -X GET http://localhost:5000/api/diseases/1
```

---

#### GET /api/diseases/{disease_id}/related

Get diseases related to specified disease, ordered by odds ratio.

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| disease_id | string | Yes | Numeric ID or ICD code |

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| limit | integer | No | 50 | Maximum results (1-1000) |
| min_odds_ratio | float | No | 1.5 | Minimum odds ratio threshold (>0) |

**Response**: `200 OK` | `404 Not Found`

```json
[
  {
    "id": 45,
    "icd_code": "I10",
    "name_english": "Essential hypertension",
    "name_german": "Essentielle Hypertonie",
    "chapter_code": "IX",
    "odds_ratio": 2.34,
    "p_value": 0.001,
    "relationship_strength": "moderate",
    "patient_count_total": 15234
  }
]
```

**cURL Example**:
```bash
# Get related diseases for diabetes
curl -X GET http://localhost:5000/api/diseases/E11/related

# With custom limit and odds ratio
curl -X GET "http://localhost:5000/api/diseases/E11/related?limit=20&min_odds_ratio=2.0"
```

---

#### GET /api/diseases/search/{search_term}

Search diseases by name or ICD code.

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| search_term | string | Yes | Search string (min 2 characters) |

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| limit | integer | No | 20 | Maximum results (1-100) |

**Response**: `200 OK` | `400 Bad Request`

```json
[
  {
    "id": 1,
    "icd_code": "E11",
    "name_english": "Type 2 diabetes mellitus",
    "name_german": "Diabetes mellitus Typ 2",
    "chapter_code": "IV",
    "chapter_name": "Endocrine, nutritional and metabolic diseases",
    "prevalence_total": 0.076
  }
]
```

**cURL Example**:
```bash
curl -X GET "http://localhost:5000/api/diseases/search/diabetes?limit=10"
```

---

### Network

#### GET /api/network

Get network data with nodes and edges for 3D visualization.

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| min_odds_ratio | float | No | 1.5 | Minimum odds ratio for edges (>0) |
| max_edges | integer | No | - | Maximum edges to return (1-10000) |
| chapter_filter | string | No | - | Filter by ICD chapter |

**Response**: `200 OK`

```json
{
  "nodes": [
    {
      "id": 1,
      "icd_code": "E11",
      "name_english": "Type 2 diabetes mellitus",
      "name_german": "Diabetes mellitus Typ 2",
      "chapter_code": "IV",
      "vector_x": -0.234,
      "vector_y": 0.567,
      "vector_z": -0.123,
      "prevalence_total": 0.076
    }
  ],
  "edges": [
    {
      "source": 1,
      "target": 45,
      "source_icd": "E11",
      "target_icd": "I10",
      "source_name": "Type 2 diabetes mellitus",
      "target_name": "Essential hypertension",
      "odds_ratio": 2.34,
      "p_value": 0.001,
      "relationship_strength": "moderate",
      "patient_count_total": 15234
    }
  ],
  "metadata": {
    "min_odds_ratio": 1.5,
    "chapter_filter": null,
    "total_nodes": 850,
    "total_edges": 3200
  }
}
```

**cURL Example**:
```bash
# Get full network
curl -X GET http://localhost:5000/api/network

# Filter by chapter
curl -X GET "http://localhost:5000/api/network?chapter_filter=IX&min_odds_ratio=2.0"

# Limit edges
curl -X GET "http://localhost:5000/api/network?max_edges=1000"
```

---

### Chapters

#### GET /api/chapters

Get all ICD chapters with disease counts.

**Response**: `200 OK`

```json
[
  {
    "chapter_code": "I",
    "chapter_name": "Certain infectious and parasitic diseases",
    "disease_count": 87,
    "avg_prevalence": 0.034
  },
  {
    "chapter_code": "IX",
    "chapter_name": "Diseases of the circulatory system",
    "disease_count": 156,
    "avg_prevalence": 0.142
  }
]
```

**cURL Example**:
```bash
curl -X GET http://localhost:5000/api/chapters
```

---

### Risk Calculation

#### POST /api/calculate-risk

Calculate personalized disease risk scores based on existing conditions and demographics.

**Request Body**: `application/json`

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

**Request Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| age | integer | Yes | Age in years (1-120) |
| gender | string | Yes | "male" or "female" |
| bmi | float | Yes | Body Mass Index (10-60) |
| existing_conditions | array | Yes | List of ICD-10 codes (1-50 items) |
| exercise_level | string | Yes | "sedentary", "light", "moderate", or "active" |
| smoking | boolean | Yes | Current smoking status |

**Response**: `200 OK` | `400 Bad Request` | `500 Internal Server Error`

```json
{
  "risk_scores": [
    {
      "disease_id": "N18",
      "disease_name": "Chronic kidney disease",
      "risk": 0.72,
      "level": "high",
      "contributing_factors": ["existing:E11", "existing:I10"]
    },
    {
      "disease_id": "E78",
      "disease_name": "Disorders of lipoprotein metabolism",
      "risk": 0.45,
      "level": "moderate",
      "contributing_factors": ["existing:E11", "demographic:male"]
    }
  ],
  "user_position": {
    "x": -0.145,
    "y": 0.398,
    "z": -0.067
  },
  "total_conditions_analyzed": 2,
  "analysis_metadata": {
    "calculation_timestamp": "2026-01-30T12:00:00Z",
    "model_version": "1.0.0"
  }
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:5000/api/calculate-risk \
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

---

## Error Codes

| Code | Type | Description |
|------|------|-------------|
| 400 | VALIDATION_ERROR | Invalid request parameters or ICD codes |
| 404 | NOT_FOUND | Resource not found (disease, endpoint) |
| 422 | VALIDATION_ERROR | Pydantic validation failed (malformed JSON, wrong types) |
| 500 | INTERNAL_ERROR | Server error - please try again later |
| 503 | SERVICE_UNAVAILABLE | Database unavailable or service unhealthy |

### Error Response Format

All error responses follow this consistent format:

```json
{
  "error": {
    "type": "ValidationError",
    "message": "Invalid request parameters",
    "details": {
      "field": "age",
      "value": 150,
      "error": "age must be between 1 and 120"
    },
    "status_code": 400
  }
}
```

### Validation Error Example (422)

```json
{
  "error": {
    "type": "ValidationError",
    "message": "Request validation failed",
    "details": {
      "errors": [
        {
          "field": "existing_conditions",
          "message": "At least one existing condition is required",
          "type": "value_error"
        }
      ]
    },
    "status_code": 422
  }
}
```

### Not Found Error Example (404)

```json
{
  "error": {
    "type": "NotFoundError",
    "message": "Disease not found: INVALID",
    "details": {},
    "status_code": 404
  }
}
```

### Internal Server Error Example (500)

```json
{
  "error": {
    "type": "InternalServerError",
    "message": "An internal server error occurred",
    "details": {},
    "status_code": 500
  }
}
```

**Note**: In debug mode (`DEBUG=true`), internal server errors may include additional debug information in the `details` field.

---

## Validation Rules

### ICD-10 Codes
- Format: Letter + 2 digits + optional decimal (e.g., `E11`, `E11.9`, `I10`)
- Length: 3-7 characters
- Case insensitive

### Chapter Codes
- Format: Roman numerals I-XXI or single letters (e.g., `IX`, `X`, `I`)
- Case insensitive

### Search Terms
- Minimum length: 2 characters
- Maximum length: 100 characters
- Searches both English and German names plus ICD codes

### Odds Ratio
- Must be >= 1.0 for meaningful associations
- Must be positive (> 0)

### Pagination
- Limit: 1-1000 (default: 100)
- Offset: 0+ (default: 0)

### Risk Calculation Request
- **Age**: 1-120 years (required integer)
- **BMI**: 10.0-60.0 (required float)
- **Gender**: "male" or "female" (required)
- **Exercise Level**: "sedentary", "light", "moderate", or "active" (required)
- **Smoking**: true or false (required boolean)
- **Existing Conditions**: 1-50 valid ICD-10 codes (required array)

---

## Rate Limiting

Rate limiting is active: **100 requests/minute per IP address**.

When the rate limit is exceeded, the API returns:
- **Status Code**: `429 Too Many Requests`
- **Response**: Error message indicating rate limit exceeded
- **Retry-After**: Header indicating when to retry

---

## CORS

The API supports Cross-Origin Resource Sharing (CORS) for browser-based applications. Allowed origins can be configured via environment variables.

---

## Contact

- **Name**: Disease Relater Team
- **Email**: support@disease-relater.example.com
- **Issues**: https://github.com/anomalyco/disease-relater/issues

## License

MIT License - see LICENSE file for details.
