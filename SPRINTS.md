# 🛰️ M.O.N.I.T.O.R. — Sprint Plan

**Multiversal Ontology for Narrative Intelligence, Temporal Observation & Recording**

Development is organized into **6 sprints (weekly)** with clear deliverables, acceptance criteria, and KPIs.

---

## 🏁 Sprint 1 — Foundations & Infrastructure
**Goal:** stand up base services and context system.  

- Deliverables: Docker Compose (Neo4j, OpenSearch, Qdrant, MinIO, Redis, ClickHouse), `Context Token`, FastAPI stubs.  
- Acceptance: services respond to healthchecks; endpoints reject missing tokens.  
- KPIs: boot < 5 min, 0 data leaks across omniverses.  

---

## 🏗️ Sprint 2 — Graph Model & Temporal Rules
**Goal:** model continuity and n-ary facts in Neo4j.  

- Deliverables: entities, facts, participations, sources; Cypher queries; Steward v1 rules.  
- Acceptance: timeline/relations respect `time_ref`; Steward flags issues.  
- KPIs: p95 Cypher ≤ 300 ms, ≤10% false positives/negatives.  

---

## 📑 Sprint 3 — Documents & Notes
**Goal:** ingest, index, and cite external knowledge.  

- Deliverables: MinIO→extraction→OpenSearch/Qdrant pipeline; notes with backlinks; Librarian integration.  
- Acceptance: PDFs searchable in FTS+vector; evidence returns citations.  
- KPIs: p95 FTS < 500 ms, vector < 350 ms, ≥95% docs with context metadata.  

---

## ✍️ Sprint 4 — Multi-Agent Orchestration
**Goal:** implement co-pilot and auto-pilot workflows.  

- Deliverables: LangGraph/CrewAI flows; agent roles (Director, Librarian, Steward, Narrator, Critic, Chat Host); guardrails.  
- Acceptance: co-pilot produces outline, evidence, warnings, draft, critique; auto-pilot produces text + 2 options.  
- KPIs: ≥80% narratives with ≥2 citations; Steward warnings ≤0.3 per narrative.  

---

## 🌿 Sprint 5 — What-If Branches
**Goal:** create and manage alternate universes.  

- Deliverables: branch endpoint; isolated indexing per `universe_id`; promote with diffs.  
- Acceptance: branch narratives do not contaminate parent; diffs view works.  
- KPIs: branch creation < 2 s; 0 data leaks across universes.  

---

## 📊 Sprint 6 — AgentOps & Observability
**Goal:** measure quality and performance of agents.  

- Deliverables: ClickHouse traces; Streamlit dashboard with KPIs; alerts.  
- Acceptance: dashboard shows metrics per universe; basic alerts active.  
- KPIs: p95 narrative < 3 s (no RAG) / < 7 s (with RAG); coherence ≥ 0.8; ≥80% narratives with ≥2 citations.  

---

# ✅ Final Outcome
After 6 sprints, M.O.N.I.T.O.R. provides:
- Local infrastructure with Docker Compose.  
- Graph model with temporal continuity.  
- Document ingestion and notes with citations.  
- Multi-agent orchestration for narrative generation.  
- Isolated what-if universes with promotion controls.  
- Full Streamlit dashboard for context, narratives, evidence, graphs, branches, and metrics.  
# 🛰️ M.O.N.I.T.O.R. — Sprint Plan

**Multiversal Ontology for Narrative Intelligence, Temporal Observation & Recording**

Development is organized into **6 sprints (weekly)** with clear deliverables, acceptance criteria, and KPIs.

---

## 🏁 Sprint 1 — Foundations & Infrastructure
**Goal:** stand up base services and context system.  

- **Deliverables**: Docker Compose (Neo4j, Meilisearch, Qdrant, MinIO, Redis, Postgres + Langfuse, Tika), `Context Token`, FastAPI stubs.  
- **Acceptance**: services respond to healthchecks; endpoints reject missing tokens.  
- **KPIs**: boot < 5 min, 0 data leaks across omniverses.  

---

## 🏗️ Sprint 2 — Graph Model & Temporal Rules
**Goal:** model continuity and n-ary facts in Neo4j.  

- **Deliverables**: entities, facts, participations, sources; Cypher queries; Steward v1 rules.  
- **Acceptance**: timeline/relations respect `time_ref`; Steward flags issues.  
- **KPIs**: p95 Cypher ≤ 300 ms, ≤10% false positives/negatives.  

---

## 📑 Sprint 3 — Documents & Notes
**Goal:** ingest, index, and cite external knowledge.  

- **Deliverables**: MinIO → extraction via Tika → Meilisearch/Qdrant pipeline; notes with backlinks; Librarian integration.  
- **Acceptance**: PDFs searchable in FTS + vector; evidence returns citations.  
- **KPIs**: p95 Meilisearch < 200 ms, Qdrant < 350 ms, ≥95% docs with context metadata.  

---

## ✍️ Sprint 4 — Multi-Agent Orchestration
**Goal:** implement co-pilot and auto-pilot workflows.  

- **Deliverables**: LangGraph/CrewAI flows; agent roles (Director, Librarian, Steward, Narrator, Critic, Chat Host); guardrails.  
- **Acceptance**: co-pilot produces outline, evidence, warnings, draft, critique; auto-pilot produces text + 2 options.  
- **KPIs**: ≥80% narratives with ≥2 citations; Steward warnings ≤0.3 per narrative.  

---

## 🌿 Sprint 5 — What-If Branches
**Goal:** create and manage alternate universes.  

- **Deliverables**: branch endpoint; isolated indexing per `universe_id`; promote with diffs.  
- **Acceptance**: branch narratives do not contaminate parent; diffs view works.  
- **KPIs**: branch creation < 2 s; 0 data leaks across universes.  

---

## 📊 Sprint 6 — AgentOps & Observability
**Goal:** measure quality and performance of agents.  

- **Deliverables**: Langfuse traces via Postgres; Streamlit dashboard with KPIs; alerts.  
- **Acceptance**: dashboard shows metrics per universe; basic alerts active.  
- **KPIs**: p95 narrative < 3 s (no RAG) / < 7 s (with RAG); coherence ≥ 0.8; ≥80% narratives with ≥2 citations.  

---

# ✅ Final Outcome
After 6 sprints, M.O.N.I.T.O.R. provides:
- Local infrastructure with Docker Compose.  
- Graph model with temporal continuity.  
- Document ingestion and notes with citations.  
- Multi-agent orchestration for narrative generation.  
- Isolated what-if universes with promotion controls.  
- Full Streamlit dashboard for context, narratives, evidence, graphs, branches, and metrics.  
