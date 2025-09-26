# TrackFlow Architecture & Data Flow

## System Overview
TrackFlow is a marketing attribution platform that integrates with Frappe CRM to track visitor journeys from first touch to conversion.

## Core Components Sequence Diagram

```mermaid
sequenceDiagram
    participant V as Visitor
    participant W as Website
    participant TF as TrackFlow App
    participant DB as Database
    participant CRM as Frappe CRM
    participant A as Analytics

    %% Campaign Setup Flow
    Note over CRM,TF: 1. Campaign Creation Flow
    CRM->>TF: Create Link Campaign
    TF->>DB: Store Campaign Data
    TF->>TF: Generate Tracked Links
    DB->>TF: Return Short URLs
    TF->>CRM: Campaign Ready

    %% Visitor Tracking Flow
    Note over V,A: 2. Visitor Journey Tracking
    V->>W: Click Marketing Link (r/abc123)
    W->>TF: Redirect Request
    TF->>DB: Log Click Event
    TF->>TF: Generate/Update Visitor ID
    TF->>DB: Create/Update Visitor Record
    TF->>DB: Create Click Event
    TF->>V: Redirect to Target URL
    
    %% Session Tracking
    V->>W: Browse Website
    W->>TF: Page View Events
    TF->>DB: Update Visitor Session
    TF->>DB: Log Page Views
    
    %% Lead Creation & Attribution
    Note over V,A: 3. Lead Creation & Attribution
    V->>CRM: Fill Contact Form
    CRM->>TF: Trigger Lead Creation Hook
    TF->>DB: Query Visitor History
    DB->>TF: Return Touch Points
    TF->>TF: Apply Attribution Model
    TF->>CRM: Update Lead with Attribution Data
    CRM->>DB: Store Lead with Source Data

    %% Deal Conversion
    Note over CRM,A: 4. Deal Conversion & ROI
    CRM->>TF: Deal Created/Won Hook
    TF->>DB: Calculate Attribution
    TF->>TF: Apply Attribution Rules
    TF->>CRM: Update Deal Attribution
    TF->>A: Generate Performance Metrics
```

## Data Flow Architecture

```mermaid
graph TD
    A[Marketing Campaigns] --> B[Link Generation]
    B --> C[Short URLs]
    C --> D[Visitor Clicks]
    
    D --> E[Visitor Identification]
    E --> F[Cookie/Session Tracking]
    F --> G[Page View Events]
    
    G --> H[Lead Forms]
    H --> I[CRM Lead Creation]
    I --> J[Attribution Calculation]
    
    J --> K[Touch Point Analysis]
    K --> L[Multi-Touch Attribution]
    L --> M[Campaign Performance]
    
    M --> N[Analytics Dashboard]
    N --> O[ROI Reports]
```

## Current Implementation Issues

### 1. TrackFlow Settings Problems
- **Issue**: JavaScript references non-existent fields
- **Root Cause**: Mismatch between DocType JSON schema and JavaScript form handlers
- **Impact**: Internal Server Error when accessing settings

### 2. Attribution Model Integration
- **Issue**: Multiple attribution models defined but integration incomplete
- **Status**: DocType exists but calculation logic needs implementation

### 3. CRM Integration Hooks
- **Issue**: Document event hooks reference methods that may not exist
- **Risk**: Lead creation failures, missing attribution data

### 4. API Endpoint Consistency
- **Issue**: JavaScript calls methods that don't exist in Python files
- **Impact**: Button functions fail, user experience broken

## Critical Path Dependencies

```mermaid
graph LR
    A[TrackFlow Settings] --> B[API Configuration]
    B --> C[Visitor Tracking]
    C --> D[Link Generation]
    D --> E[Click Events]
    E --> F[CRM Integration]
    F --> G[Attribution Models]
    G --> H[Analytics Reports]
```

## Fix Priority Matrix

| Component | Priority | Status | Dependencies |
|-----------|----------|---------|--------------|
| TrackFlow Settings | HIGH | 🔴 Broken | None |
| Internal IP Range | HIGH | 🟡 Partial | Settings |
| API Methods | HIGH | 🔴 Missing | Settings |
| Click Tracking | MEDIUM | 🟢 Working | Settings, IP Range |
| CRM Hooks | MEDIUM | 🟡 Untested | API Methods |
| Attribution Models | LOW | 🔴 Not Implemented | CRM Hooks |
| Analytics Reports | LOW | 🟡 Basic | Attribution Models |

## Recommended Fix Sequence

1. **Phase 1: Core Infrastructure**
   - ✅ Fix TrackFlow Settings DocType validation
   - ✅ Add missing API methods
   - ✅ Fix Internal IP Range validation
   - ⏳ Test Settings page functionality

2. **Phase 2: Integration Testing**
   - 🔄 Test CRM document hooks
   - 🔄 Validate link tracking flow
   - 🔄 Test visitor identification

3. **Phase 3: Attribution Engine**
   - ⏳ Implement attribution calculation logic
   - ⏳ Test multi-touch attribution models
   - ⏳ Validate ROI calculations

4. **Phase 4: Analytics & Reporting**
   - ⏳ Test analytics dashboard
   - ⏳ Validate campaign performance reports
   - ⏳ Test visitor journey analysis

## Technical Debt Items

1. **Code Quality**
   - Circular import issues in utils
   - Missing error handling in API endpoints
   - Inconsistent field naming conventions

2. **Database Schema**
   - Missing indexes for performance
   - No data retention policies
   - Foreign key constraints not enforced

3. **Security**
   - API key validation incomplete
   - GDPR compliance features partial
   - IP filtering not fully implemented

## Next Steps

1. Complete TrackFlow Settings stabilization
2. Implement comprehensive testing for each component
3. Add proper error logging and monitoring
4. Create integration test suite for CRM hooks
5. Implement attribution model calculation engine

---

*Generated: $(date)*
*Status: Work in Progress*