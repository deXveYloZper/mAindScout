# mAIndScout API Documentation

## Overview

The mAIndScout API is a comprehensive recruitment platform that provides AI-powered candidate matching, job management, and company profiling capabilities. This document describes the enhanced API endpoints with full CRUD operations, pagination, filtering, and search functionality.

## Base URL

```
http://localhost:8000
```

## Authentication

The API uses JWT-based authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### Authentication Endpoints

#### Register User
```http
POST /auth/register
```

#### Login
```http
POST /auth/login
```

#### Get Current User
```http
GET /auth/me
```

## API Endpoints

### Health Check

#### Get Service Health
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "services": {
    "mongodb": "healthy",
    "qdrant": "healthy",
    "neo4j": "healthy",
    "authentication": "healthy"
  }
}
```

### Candidates

#### Create Candidate
```http
POST /api/v1/candidates/
```

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "phone_number": "+1234567890",
  "skills": ["Python", "React", "MongoDB"],
  "experience_years": 5.0,
  "current_role": "Senior Software Engineer",
  "current_company": "Tech Corp",
  "location": "San Francisco, CA",
  "work_experience": [
    {
      "company": "Tech Corp",
      "title": "Senior Software Engineer",
      "start_date": "2022-01-01",
      "end_date": "present",
      "responsibilities": ["Lead development team", "Architect solutions"]
    }
  ]
}
```

#### Get All Candidates (with pagination and filtering)
```http
GET /api/v1/candidates/?page=1&size=20&search=python&skills=Python,React&location=San Francisco&experience_min=3&experience_max=10&sort_by=created_at&sort_order=desc
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `size` (int): Items per page (default: 20, max: 100)
- `search` (string): Search query
- `skills` (string): Comma-separated skills to filter by
- `location` (string): Location filter
- `experience_min` (float): Minimum experience years
- `experience_max` (float): Maximum experience years
- `sort_by` (string): Sort field (default: created_at)
- `sort_order` (string): Sort order - asc/desc (default: desc)

**Response:**
```json
{
  "items": [
    {
      "id": "507f1f77bcf86cd799439011",
      "name": "John Doe",
      "email": "john.doe@example.com",
      "skills": ["Python", "React", "MongoDB"],
      "experience_years": 5.0,
      "current_role": "Senior Software Engineer",
      "location": "San Francisco, CA",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "size": 20,
  "pages": 8,
  "has_next": true,
  "has_prev": false
}
```

#### Get Candidate by ID
```http
GET /api/v1/candidates/{candidate_id}
```

#### Update Candidate
```http
PUT /api/v1/candidates/{candidate_id}
```

#### Delete Candidate
```http
DELETE /api/v1/candidates/{candidate_id}
```

#### Bulk Create Candidates
```http
POST /api/v1/candidates/bulk
```

**Request Body:**
```json
[
  {
    "name": "Jane Smith",
    "email": "jane.smith@example.com",
    "skills": ["Java", "Spring", "PostgreSQL"]
  },
  {
    "name": "Bob Johnson",
    "email": "bob.johnson@example.com",
    "skills": ["JavaScript", "Node.js", "Express"]
  }
]
```

### Jobs

#### Create Job
```http
POST /api/v1/jobs/
```

**Request Body:**
```json
{
  "title": "Senior Software Engineer",
  "description": "We are looking for a senior software engineer...",
  "required_skills": ["Python", "React", "MongoDB"],
  "good_to_have_skills": ["Docker", "Kubernetes"],
  "experience_level": "senior-level",
  "experience_years": "5+",
  "location": "San Francisco, CA",
  "company_name": "Tech Corp",
  "job_type": "Full-time",
  "salary_range": "$120,000 - $180,000",
  "employment_type": "permanent"
}
```

#### Get All Jobs (with pagination and filtering)
```http
GET /api/v1/jobs/?page=1&size=20&search=software engineer&company=Tech Corp&location=San Francisco&experience_level=senior-level&job_type=Full-time&sort_by=created_at&sort_order=desc
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `size` (int): Items per page (default: 20, max: 100)
- `search` (string): Search query
- `company` (string): Company name filter
- `location` (string): Location filter
- `experience_level` (string): Experience level filter
- `job_type` (string): Job type filter
- `sort_by` (string): Sort field (default: created_at)
- `sort_order` (string): Sort order - asc/desc (default: desc)

#### Get Job by ID
```http
GET /api/v1/jobs/{job_id}
```

#### Update Job
```http
PUT /api/v1/jobs/{job_id}
```

#### Delete Job
```http
DELETE /api/v1/jobs/{job_id}
```

### Companies

#### Create Company
```http
POST /api/v1/companies/
```

**Request Body:**
```json
{
  "company_name": "Tech Corp",
  "company_description": "Leading technology company...",
  "industry": ["Technology", "Software Development"],
  "website": "https://techcorp.com",
  "location": ["San Francisco, CA", "New York, NY"],
  "company_type": "Private",
  "company_size": "201-500",
  "tech_stack": [
    {
      "technology": "Python",
      "type": "backend",
      "level": "primary"
    },
    {
      "technology": "React",
      "type": "frontend",
      "level": "primary"
    }
  ]
}
```

#### Get All Companies (with pagination and filtering)
```http
GET /api/v1/companies/?page=1&size=20&search=tech&industry=Technology&location=San Francisco&company_size=201-500&company_type=Private&sort_by=created_at&sort_order=desc
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `size` (int): Items per page (default: 20, max: 100)
- `search` (string): Search query
- `industry` (string): Industry filter
- `location` (string): Location filter
- `company_size` (string): Company size filter
- `company_type` (string): Company type filter
- `sort_by` (string): Sort field (default: created_at)
- `sort_order` (string): Sort order - asc/desc (default: desc)

#### Get Company by ID
```http
GET /api/v1/companies/{company_id}
```

#### Update Company
```http
PUT /api/v1/companies/{company_id}
```

#### Delete Company
```http
DELETE /api/v1/companies/{company_id}
```

### Statistics

#### Get Platform Statistics
```http
GET /api/v1/stats/
```

**Response:**
```json
{
  "total_candidates": 1500,
  "total_jobs": 250,
  "total_companies": 100,
  "total_matches": 5000,
  "last_updated": "2024-01-01T00:00:00Z"
}
```

### File Upload

#### Upload Job Description or Candidate Profile
```http
POST /upload/upload
```

**Form Data:**
- `file`: PDF, DOCX, or TXT file
- `file_type`: "job_description" or "candidate_profile"

### Legacy Endpoints

#### Create Job Description (Legacy)
```http
POST /job-descriptions/
```

#### Match Candidates (Legacy)
```http
POST /candidates/match
```

#### Get Matched Candidates (Legacy)
```http
GET /candidates/match/{job_id}
```

## Error Responses

### Standard Error Format
```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "code": "ERROR_CODE"
}
```

### Common HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service unavailable

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Authentication endpoints**: 10 requests/minute
- **CRUD operations**: 10-30 requests/minute (varies by operation)
- **File uploads**: No limit (resource-intensive)
- **Statistics**: 10 requests/minute
- **Health checks**: No limit

## Pagination

All list endpoints support pagination with the following parameters:

- `page`: Page number (1-based)
- `size`: Items per page (1-100)

Response includes pagination metadata:
- `total`: Total number of items
- `pages`: Total number of pages
- `has_next`: Whether there's a next page
- `has_prev`: Whether there's a previous page

## Search and Filtering

### Text Search
Use the `search` parameter for full-text search across relevant fields.

### Filtering
Each entity type supports specific filters:

**Candidates:**
- `skills`: Comma-separated skill list
- `location`: Location string
- `experience_min/max`: Experience range

**Jobs:**
- `company`: Company name
- `location`: Location string
- `experience_level`: Experience level
- `job_type`: Job type

**Companies:**
- `industry`: Industry name
- `location`: Location string
- `company_size`: Company size
- `company_type`: Company type

### Sorting
All endpoints support sorting with:
- `sort_by`: Field to sort by
- `sort_order`: "asc" or "desc"

## Data Models

### Candidate Profile
```json
{
  "id": "string",
  "name": "string",
  "email": "string",
  "phone_number": "string",
  "skills": ["string"],
  "standardized_skills": ["string"],
  "experience_years": "float",
  "current_role": "string",
  "current_company": "string",
  "location": "string",
  "work_experience": [
    {
      "company": "string",
      "title": "string",
      "start_date": "string",
      "end_date": "string",
      "responsibilities": ["string"]
    }
  ],
  "created_at": "datetime"
}
```

### Job Description
```json
{
  "id": "string",
  "title": "string",
  "description": "string",
  "required_skills": ["string"],
  "good_to_have_skills": ["string"],
  "experience_level": "string",
  "experience_years": "string",
  "location": "string",
  "company_name": "string",
  "job_type": "string",
  "salary_range": "string",
  "employment_type": "string",
  "created_at": "datetime"
}
```

### Company Profile
```json
{
  "id": "string",
  "company_name": "string",
  "company_description": "string",
  "industry": ["string"],
  "website": "string",
  "location": ["string"],
  "company_type": "string",
  "company_size": "string",
  "tech_stack": [
    {
      "technology": "string",
      "type": "string",
      "level": "string"
    }
  ],
  "created_at": "datetime"
}
```

## SDKs and Libraries

### Python
```python
import requests

# Base URL
BASE_URL = "http://localhost:8000"

# Authentication
def login(email, password):
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email,
        "password": password
    })
    return response.json()["access_token"]

# Get candidates
def get_candidates(token, page=1, size=20):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/v1/candidates/",
        headers=headers,
        params={"page": page, "size": size}
    )
    return response.json()
```

### JavaScript/Node.js
```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000';

// Authentication
async function login(email, password) {
    const response = await axios.post(`${BASE_URL}/auth/login`, {
        email,
        password
    });
    return response.data.access_token;
}

// Get candidates
async function getCandidates(token, page = 1, size = 20) {
    const response = await axios.get(`${BASE_URL}/api/v1/candidates/`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { page, size }
    });
    return response.data;
}
```

## Best Practices

1. **Authentication**: Always include the JWT token in the Authorization header
2. **Rate Limiting**: Respect rate limits and implement exponential backoff
3. **Pagination**: Use pagination for large datasets
4. **Error Handling**: Implement proper error handling for all API calls
5. **Caching**: Cache frequently accessed data when appropriate
6. **Validation**: Validate data before sending to the API
7. **Logging**: Log API interactions for debugging and monitoring

## Support

For API support and questions:
- Email: support@maindscout.com
- Documentation: https://docs.maindscout.com
- GitHub Issues: https://github.com/maindscout/api-issues 