# MatchForge REST API Reference (v1)

Base URL: `/api/v1/`

All endpoints return JSON responses. Protected endpoints require either an active Django session or HTTP Basic / Token headers.

---

## 1. Authentication & Profiles

### `POST /api/v1/auth/register/`
Create a new candidate user account and associated profile.
- **Payload:**
  ```json
  {
    "username": "candidate_alex",
    "email": "alex@example.com",
    "password": "SecurePassword123!",
    "full_name": "Alex Sharma",
    "current_location": "Bangalore"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "status": "success",
    "message": "User registered and logged in successfully.",
    "user": { "id": "uuid...", "username": "candidate_alex", "email": "alex@example.com" }
  }
  ```

### `POST /api/v1/auth/login/`
Authenticate existing candidate and establish session.
- **Payload:** `{ "username": "...", "password": "..." }`

### `POST /api/v1/auth/logout/`
Invalidate candidate session.

### `GET /api/v1/profile/` | `PUT /api/v1/profile/`
Retrieve or update candidate headline, bio, experience months, current city, and relocation willingness.

---

## 2. Resumes & Intelligence

### `POST /api/v1/resumes/upload/`
Upload candidate PDF resume (multipart form, key: `resume`, max 5MB).
- Extracts text via PyPDF, normalizes technical skills against taxonomy, estimates experience, and computes completeness score.
- **Response (201 Created):**
  ```json
  {
    "status": "success",
    "resume": {
      "id": "uuid...",
      "file_name": "resume.pdf",
      "completeness_score": 85.0,
      "extracted_skills": [
        { "name": "Python", "category": "LANGUAGE", "proficiency_level": 4 }
      ]
    }
  }
  ```

### `GET /api/v1/resumes/latest/`
Retrieve active resume extractions.

---

## 3. Opportunities & Search

### `GET /api/v1/opportunities/`
List active opportunities with optional query filters: `?work_mode=Remote&employment_type=Internship&no_unpaid=true`.

### `POST /api/v1/opportunities/search/`
Hybrid search combining vector cosine embeddings and keyword matching.
- **Payload:**
  ```json
  {
    "query": "scalable backend startup internship",
    "filters": { "work_mode": "Remote", "no_unpaid": true },
    "limit": 10
  }
  ```

### `POST /api/v1/opportunities/compare/`
Side-by-side comparison of 2 to 4 opportunities.
- **Payload:** `{ "opportunity_ids": ["uuid1", "uuid2"] }`

### `POST /api/v1/opportunities/{id}/save/`
Toggle bookmark on an opportunity.

---

## 4. Recommendations & Explainability

### `POST /api/v1/recommendations/generate/`
Triggers deterministic hybrid ranking across active opportunities.

### `GET /api/v1/recommendations/`
Returns ranked opportunities for logged-in candidate with overall score, factor sub-scores, and dealbreaker flags.

### `GET /api/v1/recommendations/{id}/explanation/`
Returns grounded factual evidence: matched skills, missing skills, preference alignment, and natural language summary.

### `GET /api/v1/analytics/skill-gaps/`
Returns candidate's missing skills ranked by market demand frequency in matching opportunities.

---

## 5. Conversational AI Agent

### `POST /api/v1/agent/conversations/`
Create a new conversation session.

### `POST /api/v1/agent/conversations/{id}/messages/`
Send a natural language message to the agent.
- Agent extracts desires, executes guarded tools, resolves preference updates, and returns the response:
- **Response (200 OK):**
  ```json
  {
    "conversation_id": "uuid...",
    "message": "I've updated your persistent preferences: work_mode: Remote; strict no-unpaid dealbreaker enabled.",
    "tool_calls_executed": 1,
    "tool_results": [...],
    "active_preferences": { "no_unpaid": true, "work_mode": ["Remote"] },
    "engine": "deterministic_nlp_fallback"
  }
  ```

---

## 6. Evaluations

### `POST /api/v1/evaluations/run/`
Runs the 50-item benchmark suite and returns Precision@K, Recall@K, MRR, NDCG@K, and Dealbreaker Violation Rate.

### `GET /api/v1/evaluations/latest/`
Retrieves latest benchmark results.
