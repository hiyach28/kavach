# Feature Status

Tracks the end-to-end implementation status of every module feature.

## Definitions
- **Design:** Contract created, schemas defined.
- **Mocked:** Frontend using mock responses.
- **Backend:** Endpoint implemented and tested.
- **Integrated:** Frontend connected to live backend endpoint.

## 1. FraudScope
| Feature | Status | Notes |
|---------|--------|-------|
| 1.1 POST /classify | Integrated | Contract defined and wired |
| 1.2 De-identification | Integrated | Regex masking functional |
| 1.3 Result Card UI | Integrated | |

## 2. NetworkX
| Feature | Status | Notes |
|---------|--------|-------|
| 2.1 Seed mock data | Integrated | |
| 2.2 GET /graph | Integrated | Contract defined and wired |
| 2.3 Clustering logic | Integrated | Louvain algorithm working |
| 2.4 Graph UI | Integrated | D3 ForceGraph fully stabilized |

## 3. CrimeMap
| Feature | Status | Notes |
|---------|--------|-------|
| 3.1 GET /districts | Integrated | Contract defined and wired |
| 3.2 Choropleth UI | Integrated | |
| 3.3 Priority Scoring | Integrated | Dynamic and static scoring merged |
| 3.4 Tooltip UI | Integrated | Nested case view implemented |
