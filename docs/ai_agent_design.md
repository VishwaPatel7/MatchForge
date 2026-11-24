# Conversational AI Agent & Guarded Tool Architecture

## 1. Agent Architecture

MatchForge includes a conversational AI assistant that extracts user career preferences, enforces constraints, and executes backend services through guarded tool calling.

```
Candidate: "I want a remote backend internship using Python and Django. No unpaid work."
                             │
                             ▼
              [ Conversational Agent Orchestrator ]
                             │
                             ▼
                    [ LLM / NLP Gateway ]
                             │  (Emits Tool Calls)
                             ▼
                 [ Guarded Tool Dispatcher ]
    ┌────────────────────────┼────────────────────────┐
    ▼                        ▼                        ▼
update_user_preferences() search_opportunities() identify_skill_gaps()
    │                        │                        │
    ▼                        ▼                        ▼
[ PreferenceManager ]  [ HybridSearchService ]  [ SkillGapAnalyzer ]
(Detects updates,      (Applies hard filters)  (Aggregates market demand)
 increments version)
```

---

## 2. Registered Tool Specifications

1. `update_user_preferences(preferred_roles, preferred_skills, work_mode, no_unpaid, preferred_locations, excluded_locations)`
   - Updates persistent preferences. Detects conflicts and records versions in `PreferenceHistory`.
2. `search_opportunities(query, work_mode, location, exclude_unpaid, limit)`
   - Hybrid semantic and keyword opportunity search.
3. `compare_opportunities(opportunity_ids)`
   - Multi-opportunity trade-off analysis.
4. `get_user_profile(include_resume)`
   - Retrieves active candidate profile and skills.
5. `explain_recommendation(opportunity_id)`
   - Grounded score breakdown and skill match evidence.
6. `identify_skill_gaps(target_role)`
   - Analyzes missing skills required by top matching opportunities.

---

## 3. Dual-Engine Execution Strategy

1. **LLM Provider Mode**: When `OPENAI_API_KEY` is present, uses `gpt-4o-mini` with native function calling.
2. **Deterministic Offline Fallback**: When no API key is provided, uses `DeterministicNLPEngine` with regex and taxonomy matching to extract preferences and execute tools with zero network latency and 100% reliability.
