# MatchForge
> **Find opportunities that actually fit you.**

MatchForge is an explainable AI-powered opportunity discovery and recommendation platform built for candidates seeking software engineering roles and internships.

Unlike keyword-only job boards, MatchForge understands a candidate's background, preferences, and dealbreakers. It combines **dense vector retrieval**, **guarded conversational AI agent tools**, **persistent conversational memory**, and a **deterministic multi-factor ranking algorithm** with factual explanations.

---

## Key Highlights

- **Backend Architecture**: Python 3.12, Django 5.x, Django REST Framework, PostgreSQL / SQLite with vector storage, Redis caching, Celery async tasks.
- **Conversational AI Agent**: Multi-turn dialogue with guarded tool calling (`update_user_preferences`, `search_opportunities`, `compare_opportunities`, `get_user_profile`, `explain_recommendation`, `identify_skill_gaps`). Safe schema validation via Pydantic.
- **Persistent Conversational Memory**: Cross-session preference resolution that updates and versions preferences without duplicate contradictions, with a complete audit history.
- **Zero-Tolerance Hard Filters**: Immediate Boolean exclusion of unpaid internships, prohibited companies, or unwanted locations. The LLM is never allowed to override dealbreakers.
- **Deterministic Hybrid Ranking**: Reproducible 6-factor scoring formula:
  $$\text{Final Score} = 0.30 \times \text{Semantic} + 0.25 \times \text{Skill} + 0.15 \times \text{Role} + 0.10 \times \text{Exp} + 0.10 \times \text{Loc} + 0.10 \times \text{Pref}$$
- **AI Evaluation Benchmark Suite**: Empirical test runner measuring Precision@5, NDCG@5, MRR, and verifying a **0.00% dealbreaker violation rate** across 50 benchmark test cases.
- **Production UI**: Responsive Bootstrap 5 interface with Chart.js analytics, sidebars, toast alerts, and real-time chat.
- **100% Test Coverage**: 18 automated unit and integration tests passing out-of-the-box.

---

## System Architecture

```
[ Client Layer (Bootstrap 5, Vanilla JS, Chart.js) ]
                        │
                        ▼
[ Security & Middleware (WhiteNoise, SessionAuth, CSRF) ]
                        │
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
[ Accounts & Profiles ] [ AI Agent ]  [ Search & Rank ]
 - User profiles         - Tools       - Vector Cosine
 - Resume PDF Parser     - Gateway     - Hybrid Search
 - Skill Taxonomy        - Memory      - Multi-factor Formula
                        │
                        ▼
   [ PostgreSQL 16 + pgvector / SQLite Portable Fallback ]
   [ Redis 7 + Celery Task Queue with Synchronous Fallback ]
```

---

## Database ER Design

The database contains 13 relational entities:
1. `UserProfile`: Extends User with location, relocation willingness, and experience.
2. `CandidateResume`: Uploaded PDF resumes with SHA-256 deduplication and completeness metrics.
3. `ExtractedSkill`: Normalized technical proficiencies categorized by Language, Framework, Database, DevOps.
4. `Opportunity`: Core job/internship listing with work mode, compensation, and required skills.
5. `OpportunityEmbedding`: Vector representation for cosine similarity.
6. `UserPreference`: Candidate preferences with versioning and hard dealbreaker flags.
7. `PreferenceHistory`: Complete version audit log tracking conversational changes.
8. `Conversation`: Multi-turn conversational session.
9. `ChatMessage`: Turns with tool calls, results, and sender metadata.
10. `Recommendation`: Multi-factor calculated scores (0-100) and hard filter pass/fail flags.
11. `RecommendationExplanation`: Evidence-grounded explanations (matched/missing skills).
12. `SavedOpportunity`: Bookmarked opportunities.
13. `SearchHistory`: Audit log of search queries and performance.

---

## Getting Started

### Local Development Setup

1. **Activate Virtual Environment**:
   ```bash
   cd matchforge
   .\venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```

4. **Ingest Sample Opportunities & Precompute Embeddings**:
   ```bash
   python manage.py ingest_opportunities --count 350
   ```

5. **Run the Development Server**:
   ```bash
   python manage.py runserver
   ```
   Navigate to `http://127.0.0.1:8000/`.

---

## Running the Automated Test Suite

MatchForge includes 18 unit, integration, and benchmark tests:

```bash
python -m pytest
```

Expected output:
```
============================= 18 passed in 11.01s =============================
```

---

## Running with Docker Compose

To launch the complete production stack (PostgreSQL with pgvector, Redis, Celery, and Django Gunicorn):

```bash
docker-compose up --build
```

Access the application at `http://localhost:8000/`.

---

## Technical Documentation Directory

- **[System Architecture](docs/architecture.md)**: Deep dive into architectural boundaries, security, and data flow.
- **[REST API Reference](docs/api_documentation.md)**: Complete endpoint contracts, payloads, and HTTP status codes.
- **[Recommendation Engine](docs/recommendation_engine.md)**: Mathematical scoring formulas, normalizations, and hard filter mechanics.
- **[AI Agent & Guarded Tools](docs/ai_agent_design.md)**: Pydantic schemas, tool dispatchers, and stateful memory.
- **[Evaluation Benchmark Report](docs/evaluation_report.md)**: Precision, Recall, MRR, NDCG, and head-to-head retrieval comparison.

---

## Demonstration Workflow for Technical Interviews

1. **Candidate Onboarding**: Register a new user at `/register/` and inspect the initial dashboard.
2. **Resume Parsing**: Navigate to `/resume/` and upload a PDF resume. Observe the skill extraction taxonomy, completeness gauge, and experience estimation.
3. **Conversational Agent Turn**: Go to `/agent/` and type:
   > *"I want a remote backend internship using Python and Django. I don't want unpaid internships."*
4. **Inspect Persistent Memory**: Notice how the agent executes `update_user_preferences()`, flags `no_unpaid` as a dealbreaker, and retrieves matching roles. Visit `/preferences/` to inspect versioning and audit history.
5. **Conflict Resolution**: In `/agent/`, type:
   > *"I can now relocate to Bangalore for startup roles."*
   Notice that the existing preference was updated (version 2) rather than creating a duplicate.
6. **Review Ranked Recommendations**: Open `/recommendations/` to inspect the 6-factor scores and factual explanations. Confirm that all unpaid roles are strictly filtered out.
7. **Opportunity Comparison**: Select 2 or 3 opportunities and navigate to `/compare/` to view the side-by-side trade-off matrix.
8. **Skill Gap Analytics**: Open `/skill-gaps/` to inspect the market demand frequency chart.
9. **AI Evaluation Benchmark**: Open `/evaluations/` and click **Run Benchmark Suite Now** to trigger live evaluation across 50 ground truth queries and inspect NDCG, MRR, and the 0.00% dealbreaker violation rate.
