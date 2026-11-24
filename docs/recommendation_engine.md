# MatchForge Recommendation & Ranking Engine

## 1. Algorithmic Overview

MatchForge does not rely on random or opaque match numbers. Recommendations are computed via a **two-phase deterministic pipeline**:

```
[ Active Opportunity Corpus ]
             │
             ▼
[ Phase 1: Hard Filter Gate (Boolean Dealbreaker Exclusion) ]
 ├── Unpaid prohibited? (no_unpaid == True and job.is_unpaid == True) -> EXCLUDE
 ├── Excluded companies? (company in prohibited_companies) -> EXCLUDE
 ├── Excluded locations? (location in excluded_locations and not Remote) -> EXCLUDE
 └── Required work mode mismatch? -> EXCLUDE
             │
             ▼ Surviving Candidates
[ Phase 2: Normalized Multi-Factor Weighted Scoring ]
 ├── Semantic Similarity (30%)
 ├── Skill Overlap (25%)
 ├── Role Title Relevance (15%)
 ├── Experience Compatibility (10%)
 ├── Location Compatibility (10%)
 └── Preference Compatibility (10%)
             │
             ▼
[ Grounded Explanation Generation & Output Ranking ]
```

---

## 2. Mathematical Formulation

Every factor is strictly normalized to $0 \le S \le 100$:

$$\text{Final Score} = 0.30 S_{\text{semantic}} + 0.25 S_{\text{skill}} + 0.15 S_{\text{role}} + 0.10 S_{\text{experience}} + 0.10 S_{\text{location}} + 0.10 S_{\text{preference}}$$

### A. Semantic Similarity ($S_{\text{semantic}}$, 30%)
Cosine similarity between normalized vector representations of candidate profile/resume $\vec{u}$ and opportunity description $\vec{v}$:

$$S_{\text{semantic}} = \max\left(0, \frac{\vec{u} \cdot \vec{v}}{\|\vec{u}\| \|\vec{v}\|}\right) \times 100$$

### B. Skill Overlap ($S_{\text{skill}}$, 25%)
Weighted intersection over required skills ($R$) and preferred skills ($P$) relative to candidate skills ($C$):

$$S_{\text{skill}} = \left(0.75 \times \frac{|C \cap R|}{\max(1, |R|)} + 0.25 \times \frac{|C \cap P|}{\max(1, |P|)}\right) \times 100$$

### C. Role Title Relevance ($S_{\text{role}}$, 15%)
Token-overlap ratio between candidate headline/target roles and job title.

### D. Experience Compatibility ($S_{\text{experience}}$, 10%)
- If candidate months $E_{\text{cand}} \ge E_{\text{req\_min}} \rightarrow 100.0$
- If $E_{\text{cand}} < E_{\text{req\_min}} \rightarrow \max\left(0.0, 100.0 - 20 \times \frac{E_{\text{req\_min}} - E_{\text{cand}}}{6}\right)$

### E. Location Compatibility ($S_{\text{location}}$, 10%)
- Remote role: $100.0$
- Same city as candidate: $100.0$
- Relocation allowed: $75.0$
- Incompatible location: $25.0$

### F. Soft Preference Compatibility ($S_{\text{preference}}$, 10%)
Evaluates non-dealbreaker soft alignment such as startup preference, domain interest, and stipend satisfaction.

---

## 3. Grounded Explanation Generation

Explanations are synthesized purely from computed match evidence (`matched_skills`, `missing_skills`, `preference_matches`, `potential_concerns`). This guarantees **zero hallucinations**: the explanation reflects the exact numerical score factors.
