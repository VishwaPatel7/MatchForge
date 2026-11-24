# MatchForge System Architecture Specification

## 1. High-Level Architecture Overview

MatchForge is an explainable AI-powered opportunity discovery and recommendation platform designed for candidate-opportunity alignment. Unlike traditional keyword-only applicant tracking or job search tools, MatchForge implements a hybrid architecture:

```
[ Client Layer (Bootstrap 5 + Vanilla JS + Chart.js) ]
                     │  (HTTP / REST APIs)
                     ▼
[ Security & Middleware (WhiteNoise, SessionAuth, CSRF, Rate Limiting) ]
                     │
     ┌───────────────┼───────────────┐
     ▼               ▼               ▼
[ Domain Apps ] [ AI Agent ]  [ Search & Rank ]
 - accounts      - orchestrator - vector_service
 - profiles      - tools (safe) - hybrid_search
 - resumes       - llm_gateway  - ranker (formula)
 - preferences   - schemas      - explainer
                     │
     ┌───────────────┴───────────────┐
     ▼                               ▼
[ PostgreSQL / SQLite ]      [ Background Queue ]
 - 13 Relational Tables      - Celery Worker
 - Cosine Vector Indices     - Redis Broker / Eager
```

---

## 2. Architectural Principles & Isolation Guarantees

### A. Non-Destructive Guarded Tool Execution
The LLM never generates direct SQL, ORM queries, or database mutations. All mutations occur through strictly validated Pydantic schemas in `apps.ai_agent.tools.GuardedToolDispatcher`.

### B. Two-Phase Deterministic Recommendation Gate
1. **Phase 1: Zero-Tolerance Hard Filters**: If an opportunity violates any active dealbreaker (e.g. unpaid work, prohibited companies, excluded locations), it is excluded immediately. The LLM is never allowed to override a hard filter.
2. **Phase 2: Multi-Factor Scoring**: Surviving opportunities are scored using a normalized 6-factor mathematical equation. Scores are reproducible and evidence-grounded.

### C. Persistent Memory & Conflict Resolution
Preferences persist across sessions in `UserPreference`. When a user updates a preference (e.g. changing work mode from "Remote" to "Bangalore Hybrid"), the engine updates the existing record, increments the version, and appends an audit record to `PreferenceHistory` rather than producing conflicting duplicates.

### D. Dual-Path Vector & Hybrid Retrieval
- Dense Semantic Search: Cosine similarity over normalized embeddings.
- Sparse Keyword Search: Full-text token matching across title, company, description, and required skills.
- Hybrid Retrieval: Weighted Reciprocal Rank Fusion ($0.6 \times \text{Semantic} + 0.4 \times \text{Keyword}$) ensures robust retrieval even when wording drifts.
