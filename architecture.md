# Architecture.md — Bluestock Mutual Fund Analytics

## 1. Architecture Goal

The platform is designed as a layered analytics system rather than a single dashboard script.

The architecture separates:

- presentation,
- API,
- business logic,
- persistence,
- ETL,
- analytics,
- data,
- reporting.

---

## 2. System Context

```mermaid
flowchart TB
    User[Investor / Analyst / Business User]

    User --> Web[Web Frontend]
    User --> Dashboard[Streamlit Analytics Dashboard]

    Web --> API[FastAPI REST API]
    Dashboard --> Data[Processed Analytics Data]
    Dashboard --> API

    API --> Services[Service Layer]
    Services --> Repo[Repository Layer]
    Repo --> DB[(PostgreSQL / SQLite)]

    ETL[ETL Pipeline] --> DB
    ETL --> Processed[Processed CSV]
    Raw[Raw Mutual Fund Data] --> ETL

    Services --> Analytics[Analytics Engine]
    Analytics --> Risk[Risk Analytics]
    Analytics --> Portfolio[Portfolio Optimization]
    Analytics --> MC[Monte Carlo Simulation]

    Risk --> Reports[Reports]
    Portfolio --> Reports
    MC --> Reports
```

---

## 3. High-Level Layers

### Presentation Layer

```text
frontend/
dashboard/
```

Responsibilities:

- navigation;
- filters;
- KPI presentation;
- charts;
- user interactions;
- download controls;
- responsive presentation.

The frontend should not own financial calculations.

---

### API Layer

```text
backend/app/api/
```

FastAPI endpoints expose application capabilities.

The API is responsible for:

- request validation;
- authentication/authorization when introduced;
- HTTP status handling;
- response serialization;
- routing requests to services.

---

### Service Layer

```text
backend/app/services/
```

This is the application/business layer.

Examples:

- fund discovery;
- dashboard summary;
- portfolio optimization;
- recommendations;
- simulation orchestration.

Business decisions should live here instead of being duplicated in route handlers.

---

### Repository / Database Layer

```text
backend/app/database/
backend/app/core/database.py
sql/
```

Responsibilities:

- ORM models;
- repositories;
- persistence;
- schema constraints;
- database queries;
- indexes.

---

### Analytics Layer

```text
backend/app/analytics/
backend/app/machine_learning/
scripts/
notebooks/
```

Responsibilities:

- return calculations;
- risk metrics;
- portfolio analytics;
- simulations;
- predictive/ML experiments.

---

## 4. Data Architecture

The database follows a normalized design centered on `fund_master`.

```mermaid
erDiagram
    FUND_MASTER ||--o{ NAV_HISTORY : has
    FUND_MASTER ||--|| SCHEME_PERFORMANCE : has
    FUND_MASTER ||--o{ INVESTOR_TRANSACTIONS : receives
    FUND_MASTER ||--o{ PORTFOLIO_HOLDINGS : contains

    FUND_MASTER {
        bigint amfi_code PK
        string fund_house
        string scheme_name
        string category
        string sub_category
        string plan
        date launch_date
        string benchmark
        decimal expense_ratio_pct
        decimal exit_load_pct
        int min_sip_amount
        string risk_category
    }

    NAV_HISTORY {
        bigint nav_id PK
        bigint amfi_code FK
        date nav_date
        decimal nav
    }

    SCHEME_PERFORMANCE {
        bigint amfi_code PK,FK
        decimal return_1yr_pct
        decimal return_3yr_pct
        decimal alpha
        decimal beta
        decimal sharpe_ratio
        decimal sortino_ratio
        decimal std_dev_ann_pct
        decimal max_drawdown_pct
        decimal aum_crore
    }

    INVESTOR_TRANSACTIONS {
        bigint transaction_id PK
        bigint amfi_code FK
        date transaction_date
        decimal amount
    }

    PORTFOLIO_HOLDINGS {
        bigint holding_id PK
        bigint amfi_code FK
        decimal units
        decimal market_value
    }
```

---

## 5. ETL Architecture

```mermaid
flowchart LR
    A[Raw CSV] --> B[Extract]
    B --> C[Transform]
    C --> D[Clean]
    D --> E[Validate]
    E --> F[Load]
    F --> G[(Database)]
    D --> H[Processed CSV]
    G --> I[Analytics]
    H --> I
```

### ETL responsibilities

**Extract**

Read source datasets.

**Transform**

- standardize column names;
- convert dates;
- normalize categories;
- prepare numeric fields.

**Clean**

- handle missing values;
- remove duplicates;
- resolve invalid records;
- prepare NAV calendars.

**Validate**

- referential integrity;
- uniqueness;
- numeric constraints;
- required fields.

**Load**

Insert validated data into database tables.

---

## 6. Request Lifecycle

```mermaid
sequenceDiagram
    actor U as User
    participant UI as Frontend
    participant API as FastAPI
    participant S as Service
    participant R as Repository
    participant DB as Database

    U->>UI: Select fund / filter
    UI->>API: GET /fund/{amfi_code}
    API->>S: Request fund details
    S->>R: Query scheme
    R->>DB: SELECT ...
    DB-->>R: Fund record
    R-->>S: Domain data
    S-->>API: Response model
    API-->>UI: JSON
    UI-->>U: Render fund profile
```

---

## 7. Analytics Pipeline

```mermaid
flowchart LR
    NAV[NAV History]
    BENCH[Benchmark Data]
    RF[Risk-Free Rate]

    NAV --> RETURNS[Daily Returns]
    BENCH --> RETURNS

    RETURNS --> PERF[Performance Metrics]
    RETURNS --> RISK[Risk Metrics]
    RETURNS --> COV[Covariance Matrix]

    RF --> PERF
    RF --> RISK

    PERF --> SCORE[Fund Scorecard]
    RISK --> SCORE

    COV --> MARKOWITZ[Markowitz Optimizer]
    PERF --> MARKOWITZ

    PERF --> MC[Monte Carlo Inputs]
    RISK --> MC

    SCORE --> UI[Dashboard]
    MARKOWITZ --> UI
    MC --> UI
```

---

## 8. Deployment Architecture

```mermaid
flowchart TB
    Browser[User Browser]

    subgraph App["Application Environment"]
        Frontend[Static Frontend]
        API[FastAPI]
        Streamlit[Streamlit Dashboard]
        DB[(Database)]
    end

    Browser --> Frontend
    Browser --> Streamlit
    Frontend --> API
    Streamlit --> DB
    API --> DB

    subgraph Data["Data Processing"]
        ETL[ETL Jobs]
        Analytics[Analytics Jobs]
    end

    ETL --> DB
    DB --> Analytics
    Analytics --> DB
```

The repository already contains Docker support, CI workflow files, a FastAPI backend and a Streamlit dashboard. Production deployment should keep secrets/configuration outside source control and restrict permissive CORS settings.

---

## 9. Architectural Principles

### Single source of truth

Fund identifiers and core fund metadata should originate from `fund_master`.

### Thin controllers

API routes should orchestrate, not contain large analytical algorithms.

### Reusable analytics

Risk/performance calculations should be reusable by:

- API;
- dashboard;
- reports;
- notebooks;
- scheduled jobs.

### Explainability

Every important metric should have a human-readable definition in the UI.

### Observability

Logging should capture:

- startup;
- ETL execution;
- failures;
- validation errors;
- important service events.

---

## 10. Future Scalability

A future production version can evolve toward:

```text
Object Storage
     ↓
ETL / Data Jobs
     ↓
PostgreSQL
     ↓
Caching Layer
     ↓
FastAPI
     ↓
Web App
```

Potential additions:

- authentication;
- user portfolios;
- saved watchlists;
- asynchronous jobs;
- Redis caching;
- background ETL scheduling;
- cloud object storage;
- monitoring/metrics;
- audit trails.
