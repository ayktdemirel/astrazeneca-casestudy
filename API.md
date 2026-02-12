# API.md — Connected Insights

This file defines the API contracts for:
- Required services (case study): Competitor, Insights, Notification
- Extensions: User Management (Auth/RACB), Crawler, Automation Tagging
- Cross-cutting standards: CorrelationId, auth headers, error format, status codes

---

## 1) Global API Standards (applies to ALL services)

### 1.1 CorrelationId (Traceability)
**Request header (optional):**
- `X-Correlation-Id: <uuid>`

**Response header (always):**
- `X-Correlation-Id: <uuid>`

**Behavior**
- If the client does not send `X-Correlation-Id`, the service generates a UUID.
- Services MUST propagate the same `X-Correlation-Id` when calling downstream services.
- Services MUST include `correlationId` in logs.
- Recommended: persist `correlationId` in `notification_history` and any async/event payloads.

---

### 1.2 Authorization (if enabled)
**Request header**
- `Authorization: Bearer <jwt>`

**Behavior**
- Missing/invalid token -> 401
- Insufficient role -> 403

---

### 1.3 Standard Status Codes
- 200 OK
- 201 Created
- 204 No Content
- 400 Bad Request (validation)
- 401 Unauthorized (missing/invalid token)
- 403 Forbidden (insufficient role)
- 404 Not Found
- 500 Internal Server Error

---

### 1.4 Standard Error Format
All error responses MUST follow:

~~~json
{
  "error": "string_code",
  "message": "human readable message",
  "details": { "optional": "object" }
}
~~~

Examples:

- 400 validation:
~~~json
{ "error": "validation_error", "message": "Missing required field: name" }
~~~

- 404 not found:
~~~json
{ "error": "not_found", "message": "Resource not found" }
~~~

- 401 unauthorized:
~~~json
{ "error": "unauthorized", "message": "Missing or invalid token" }
~~~

- 403 forbidden:
~~~json
{ "error": "forbidden", "message": "Insufficient role" }
~~~

---

### 1.5 Health Endpoint (all services)
**GET** `/health`  
Auth: none

**200**
~~~json
{
  "status": "ok",
  "service": "service-name",
  "time": "2026-02-08T00:00:00Z"
}
~~~

---

## 2) User Management Service (Extension)

### Roles
- `ADMIN`: full access + manage users
- `ANALYST`: create/write competitors/trials/insights
- `EXECUTIVE`: read competitors/insights, create subscriptions, read own notifications

---

### 2.1 POST /api/auth/login
Auth: none  
Headers:
- `X-Correlation-Id` (optional)

Request:
~~~json
{ "email": "exec@company.com", "password": "Passw0rd!" }
~~~

200:
~~~json
{
  "accessToken": "jwt...",
  "tokenType": "Bearer",
  "expiresIn": 3600,
  "user": { "id": "user-001", "email": "exec@company.com", "role": "EXECUTIVE" }
}
~~~

401:
~~~json
{ "error": "invalid_credentials", "message": "Invalid email or password" }
~~~

---

### 2.2 GET /api/users/me
Auth: any authenticated user  
Headers:
- `Authorization: Bearer <jwt>`
- `X-Correlation-Id` (optional)

200:
~~~json
{ "id": "user-001", "email": "exec@company.com", "role": "EXECUTIVE" }
~~~

401:
~~~json
{ "error": "unauthorized", "message": "Missing or invalid token" }
~~~

---

### 2.3 GET /api/users
Auth: ADMIN  
Headers:
- `Authorization: Bearer <jwt>`
- `X-Correlation-Id` (optional)

200:
~~~json
[
  { "id": "user-001", "email": "exec@company.com", "role": "EXECUTIVE", "isActive": true }
]
~~~

403:
~~~json
{ "error": "forbidden", "message": "Insufficient role" }
~~~

---

### 2.4 PATCH /api/users/{id}/role
Auth: ADMIN  
Headers:
- `Authorization: Bearer <jwt>`
- `X-Correlation-Id` (optional)

Request:
~~~json
{ "role": "ANALYST" }
~~~

200:
~~~json
{ "id": "user-001", "role": "ANALYST" }
~~~

400:
~~~json
{ "error": "validation_error", "message": "Invalid role" }
~~~

404:
~~~json
{ "error": "not_found", "message": "User not found" }
~~~

---

## 3) Competitor Service (Required)

### 3.1 POST /api/competitors
Auth (recommended):
- ANALYST or ADMIN

Headers:
- `Authorization: Bearer <jwt>` (if enabled)
- `X-Correlation-Id` (optional)

Request:
~~~json
{
  "name": "CompanyX Pharma",
  "therapeuticAreas": ["Oncology", "Cardiovascular"],
  "headquarters": "Basel, Switzerland",
  "activeDrugs": 12,
  "pipelineDrugs": 45
}
~~~

201:
~~~json
{
  "id": "comp-001",
  "name": "CompanyX Pharma",
  "therapeuticAreas": ["Oncology", "Cardiovascular"],
  "headquarters": "Basel, Switzerland",
  "activeDrugs": 12,
  "pipelineDrugs": 45,
  "createdAt": "2026-02-08T00:00:00Z"
}
~~~

400:
~~~json
{ "error": "validation_error", "message": "Missing required field: name" }
~~~

401/403: per Global API Standards.

---

### 3.2 GET /api/competitors
Auth (recommended):
- EXECUTIVE / ANALYST / ADMIN

Headers:
- `Authorization: Bearer <jwt>` (if enabled)
- `X-Correlation-Id` (optional)

200:
~~~json
[
  {
    "id": "comp-001",
    "name": "CompanyX Pharma",
    "therapeuticAreas": ["Oncology"],
    "headquarters": "Basel, Switzerland"
  }
]
~~~

---

### 3.3 GET /api/competitors/{id}
Auth (recommended):
- EXECUTIVE / ANALYST / ADMIN

Headers:
- `Authorization: Bearer <jwt>` (if enabled)
- `X-Correlation-Id` (optional)

200:
~~~json
{
  "id": "comp-001",
  "name": "CompanyX Pharma",
  "therapeuticAreas": ["Oncology", "Cardiovascular"],
  "headquarters": "Basel, Switzerland",
  "activeDrugs": 12,
  "pipelineDrugs": 45
}
~~~

404:
~~~json
{ "error": "not_found", "message": "Competitor not found" }
~~~

---

### 3.4 POST /api/competitors/{id}/trials
Auth (recommended):
- ANALYST or ADMIN

Headers:
- `Authorization: Bearer <jwt>` (if enabled)
- `X-Correlation-Id` (optional)

Request:
~~~json
{
  "trialId": "NCT12345678",
  "drugName": "DrugX-200",
  "phase": "Phase 3",
  "indication": "Non-small cell lung cancer",
  "status": "Active, recruiting",
  "startDate": "2024-01-15",
  "estimatedCompletion": "2026-12-31",
  "enrollmentTarget": 450
}
~~~

201:
~~~json
{
  "id": "trial-001",
  "competitorId": "comp-001",
  "trialId": "NCT12345678",
  "drugName": "DrugX-200",
  "phase": "Phase 3",
  "indication": "Non-small cell lung cancer",
  "status": "Active, recruiting",
  "startDate": "2024-01-15",
  "estimatedCompletion": "2026-12-31",
  "enrollmentTarget": 450
}
~~~

400:
~~~json
{ "error": "validation_error", "message": "Missing required field: trialId" }
~~~

404:
~~~json
{ "error": "not_found", "message": "Competitor not found" }
~~~

---

## 4) Insights Service (Required)

### 4.1 POST /api/insights
Auth (recommended):
- ANALYST or ADMIN

Headers:
- `Authorization: Bearer <jwt>` (if enabled)
- `X-Correlation-Id` (optional)

Request:
~~~json
{
  "title": "CompanyX advances to Phase 3 in NSCLC",
  "description": "CompanyX Pharma initiated Phase 3 trial for DrugX-200...",
  "category": "Clinical Trial Update",
  "therapeuticArea": "Oncology",
  "competitorId": "comp-001",
  "impactLevel": "High",
  "relevanceScore": null,
  "source": "ClinicalTrials.gov",
  "publishedDate": "2024-01-15",
  "sourceDocumentId": "doc-123"
}
~~~

**Relevance scoring rule**
- If `relevanceScore` is missing or null:
  - `High -> 9`
  - `Medium -> 6`
  - `Low -> 3`

201:
~~~json
{
  "id": "insight-001",
  "title": "CompanyX advances to Phase 3 in NSCLC",
  "description": "CompanyX Pharma initiated Phase 3 trial for DrugX-200...",
  "category": "Clinical Trial Update",
  "therapeuticArea": "Oncology",
  "competitorId": "comp-001",
  "impactLevel": "High",
  "relevanceScore": 9,
  "source": "ClinicalTrials.gov",
  "publishedDate": "2024-01-15",
  "sourceDocumentId": "doc-123",
  "createdAt": "2026-02-08T00:00:00Z"
}
~~~

400:
~~~json
{ "error": "validation_error", "message": "Missing required field: title" }
~~~

---

### 4.2 GET /api/insights?therapeuticArea=&competitorId=
Auth (recommended):
- EXECUTIVE / ANALYST / ADMIN

Headers:
- `Authorization: Bearer <jwt>` (if enabled)
- `X-Correlation-Id` (optional)

Query params (optional):
- `therapeuticArea` (string)
- `competitorId` (string)

200:
~~~json
[
  {
    "id": "insight-001",
    "title": "CompanyX advances...",
    "therapeuticArea": "Oncology",
    "competitorId": "comp-001",
    "impactLevel": "High",
    "relevanceScore": 9
  }
]
~~~

---

### 4.3 GET /api/insights/{id}
Auth (recommended):
- EXECUTIVE / ANALYST / ADMIN

Headers:
- `Authorization: Bearer <jwt>` (if enabled)
- `X-Correlation-Id` (optional)

200:
~~~json
{
  "id": "insight-001",
  "title": "CompanyX advances to Phase 3 in NSCLC",
  "description": "CompanyX Pharma initiated Phase 3 trial for DrugX-200...",
  "category": "Clinical Trial Update",
  "therapeuticArea": "Oncology",
  "competitorId": "comp-001",
  "impactLevel": "High",
  "relevanceScore": 9,
  "source": "ClinicalTrials.gov",
  "publishedDate": "2024-01-15",
  "sourceDocumentId": "doc-123",
  "createdAt": "2026-02-08T00:00:00Z"
}
~~~

404:
~~~json
{ "error": "not_found", "message": "Insight not found" }
~~~

---

### 4.4 DELETE /api/insights/{id}
Auth (recommended):
- ADMIN (or ANALYST+ADMIN if you decide)

Headers:
- `Authorization: Bearer <jwt>` (if enabled)
- `X-Correlation-Id` (optional)

204: no body

404:
~~~json
{ "error": "not_found", "message": "Insight not found" }
~~~

---

## 5) Notification Service (Required + Enhanced)

### 5.1 POST /api/subscriptions
Auth (recommended):
- any authenticated user

Headers:
- `Authorization: Bearer <jwt>` (if enabled)
- `X-Correlation-Id` (optional)

Request:
~~~json
{
  "therapeuticAreas": ["Oncology"],
  "competitorIds": ["comp-001"],
  "channels": ["console"]
}
~~~

201:
~~~json
{
  "id": "sub-001",
  "userId": "user-001",
  "therapeuticAreas": ["Oncology"],
  "competitorIds": ["comp-001"],
  "channels": ["console"],
  "createdAt": "2026-02-08T00:00:00Z"
}
~~~

400:
~~~json
{ "error": "validation_error", "message": "At least one preference is required" }
~~~

---

### 5.2 GET /api/subscriptions
Auth (recommended):
- ADMIN (or implement "own only")

Headers:
- `Authorization: Bearer <jwt>` (if enabled)
- `X-Correlation-Id` (optional)

200:
~~~json
[
  {
    "id": "sub-001",
    "userId": "user-001",
    "therapeuticAreas": ["Oncology"],
    "competitorIds": ["comp-001"],
    "channels": ["console"]
  }
]
~~~

---

### 5.3 POST /api/notifications/send
Auth (recommended):
- ADMIN/SYSTEM

Headers:
- `Authorization: Bearer <jwt>` (if enabled)
- `X-Correlation-Id` (optional)

Request:
~~~json
{ "insightId": "insight-001", "subscriptionId": "sub-001" }
~~~

200:
~~~json
{ "notificationId": "notif-001", "status": "SENT" }
~~~

404 (missing insight/subscription):
~~~json
{ "error": "not_found", "message": "Insight or subscription not found" }
~~~

---

### 5.4 GET /api/notifications  (History)
Auth (recommended):
- ADMIN

Headers:
- `Authorization: Bearer <jwt>` (if enabled)
- `X-Correlation-Id` (optional)

200:
~~~json
[
  {
    "id": "notif-001",
    "userId": "user-001",
    "subscriptionId": "sub-001",
    "insightId": "insight-001",
    "status": "SENT",
    "sentAt": "2026-02-08T00:00:00Z",
    "correlationId": "0d6a...a21"
  }
]
~~~

---

### 5.5 GET /api/notifications/me  (Enhanced)
Auth (recommended):
- any authenticated user

Headers:
- `Authorization: Bearer <jwt>` (if enabled)
- `X-Correlation-Id` (optional)

200:
~~~json
[
  {
    "id": "notif-001",
    "insightId": "insight-001",
    "status": "SENT",
    "sentAt": "2026-02-08T00:00:00Z",
    "read": false,
    "correlationId": "0d6a...a21"
  }
]
~~~

---

### 5.6 PATCH /api/notifications/{id}/read  (Optional)
Auth (recommended):
- owner or ADMIN

Headers:
- `Authorization: Bearer <jwt>` (if enabled)
- `X-Correlation-Id` (optional)

Request:
~~~json
{ "read": true }
~~~

200:
~~~json
{ "id": "notif-001", "read": true }
~~~

404:
~~~json
{ "error": "not_found", "message": "Notification not found" }
~~~

---

## 6) Crawler Service (Extension)

### 6.1 POST /api/crawl/jobs
Auth (recommended):
- ADMIN/SYSTEM

Headers:
- `Authorization: Bearer <jwt>` (if enabled)
- `X-Correlation-Id` (optional)

Request:
~~~json
{ "source": "ClinicalTrials", "query": "CompanyX Pharma", "schedule": "0 */6 * * *", "enabled": true }
~~~

201:
~~~json
{ "id": "job-001", "source": "ClinicalTrials", "query": "CompanyX Pharma", "schedule": "0 */6 * * *", "enabled": true }
~~~

---

### 6.2 GET /api/crawl/jobs
Auth (recommended):
- ADMIN/SYSTEM

Headers:
- `Authorization: Bearer <jwt>` (if enabled)
- `X-Correlation-Id` (optional)

200:
~~~json
[
  { "id": "job-001", "source": "ClinicalTrials", "query": "CompanyX Pharma", "schedule": "0 */6 * * *", "enabled": true }
]
~~~

---

### 6.3 POST /api/crawl/run
Auth (recommended):
- ADMIN/SYSTEM

Headers:
- `Authorization: Bearer <jwt>` (if enabled)
- `X-Correlation-Id` (optional)

Request:
~~~json
{ "jobId": "job-001" }
~~~

200:
~~~json
{ "runId": "run-001", "status": "STARTED" }
~~~

---

### 6.4 GET /api/crawl/documents
Auth (recommended):
- ADMIN/SYSTEM

Headers:
- `Authorization: Bearer <jwt>` (if enabled)
- `X-Correlation-Id` (optional)

200:
~~~json
[
  { "id": "doc-123", "source": "ClinicalTrials", "externalId": "NCT12345678", "publishedDate": "2024-01-15", "title": "Trial update..." }
]
~~~

---


