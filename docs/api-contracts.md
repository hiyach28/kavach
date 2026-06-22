# API Contracts

This is the single source of truth for the frontend-backend integration. Do not deviate from these schemas.

## Generic Response Wrappers

**Success:**
```json
{
  "success": true,
  "data": { ... }
}
```

**Error:**
```json
{
  "success": false,
  "error": "Human readable error message",
  "detail": { ... } // Optional context
}
```

---

## 1. FraudScope

### `POST /api/classify`
Classifies a raw text input for fraud.

**Request:**
```json
{
  "raw_text": "Call from CBI officer regarding your Aadhaar..."
}
```

**Response (Success):**
```json
{
  "success": true,
  "data": {
    "case_id": 123,
    "audit_id": "uuid-string",
    "fraud_type": "digital_arrest",
    "risk_score": 85,
    "confidence": 0.92,
    "verdict": "Likely digital arrest fraud.",
    "reporting_portal": "https://cybercrime.gov.in",
    "status": "classified",
    "red_flags": [
      {
        "flag_id": "AUTH_IMP",
        "category": "critical",
        "evidence": "CBI officer",
        "explanation": "Impersonating law enforcement"
      }
    ]
  }
}
```

### `GET /api/cases/{id}`
Retrieve a specific case by ID.

**Response (Success):** Same `data` object as `POST /api/classify`.

---

## 2. NetworkX

### `GET /api/graph`
Returns the D3.js compatible graph data.

**Response (Success):**
```json
{
  "success": true,
  "data": {
    "nodes": [
      {
        "id": "case_123",
        "label": "Case 123",
        "group": "campaign_1",
        "degree": 3,
        "fraud_type": "digital_arrest"
      }
    ],
    "links": [
      {
        "source": "case_123",
        "target": "case_124",
        "type": "shared_infra"
      }
    ],
    "campaigns": [
      {
        "id": 1,
        "label": "Campaign A",
        "case_count": 5,
        "total_estimated_loss": 500000
      }
    ]
  }
}
```

---

## 3. CrimeMap

### `GET /api/districts`
Returns stats for the choropleth map.

**Response (Success):**
```json
{
  "success": true,
  "data": [
    {
      "name": "Mumbai",
      "priority_score": 85.5,
      "complaint_count": 120,
      "estimated_loss": 5000000,
      "active_campaigns": 2,
      "trend": "rising"
    }
  ]
}
```

### `GET /api/districts/{name}/summary`
Retrieve detailed summary for a district tooltip.

**Response (Success):**
```json
{
  "success": true,
  "data": {
    "name": "Mumbai",
    "state": "Maharashtra",
    "priority_score": 85.5,
    "complaint_count": 120,
    "estimated_loss": 5000000,
    "active_campaigns": 2,
    "top_fraud_types": ["digital_arrest", "investment_fraud"],
    "trend": "rising"
  }
}
```
