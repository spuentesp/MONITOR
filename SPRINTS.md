# 🛰️ M.O.N.I.T.O.R. — Sprint Plan

**Multiversal Ontology for Narrative Intelligence, Temporal Observation & Recording**

Development is organized into **6 sprints (weekly)** with clear deliverables, acceptance criteria, and KPIs.

---

Update (2025-09-01)
- Ontology aligned and implemented: Omniverse, Multiverse, Universe, Arc, Story, Scene, Axiom, Archetype, Entity, Fact, RelationState, System, Sheet; core edges implemented (HAS_ARC, HAS_STORY, HAS_SCENE, BELONGS_TO, HAS_SHEET, OCCURS_IN, PARTICIPATES_AS, REL_STATE_FOR, APPEARS_IN, REFERS_TO, APPLIES_TO).
- YAML-first authoring solidified: example multiverse fixture, strict loader, validations/tests (10/10 passing).
- Persistence: Neo4j 5 via Docker Compose with constraints bootstrap; end-to-end projection from YAML working.
- Configuration: no hardcoded creds/paths; .env-based settings; sample scaffolds in YAML; CLI commands for bootstrap/projection and scaffolded init.
- Projector: property sanitization for Neo4j primitives; Cypher fixes; appears_in edges from scene participants.

## 🏁 Sprint 1 — Foundations & Persistence (✅ Completed)
**Goal:** establish domain, YAML flow, and graph persistence.  

- **Deliverables**:
	- Domain models (EN) and ontology containers wired (Axiom, Archetype, Fact, RelationState, System, Sheet).
	- YAML loader + comprehensive example fixture; integrity/reference tests.
	- Docker Compose: Neo4j 5 Community with APOC; constraints bootstrap command.
	- CLI: `neo4j-bootstrap`, `project-from-yaml`, `init-multiverse --scaffold`.
	- .env-based config; `.env.example`; no hardcoded credentials/URIs; scaffolds decoupled from code.
	- Projector upserts all nodes/edges with property sanitization; Cypher validated.
- **Acceptance**:
	- Tests: 10/10 pass; YAML loads into domain with relations.
	- Projection: example YAML imports successfully; expected node/edge counts present.
- **KPIs**:
	- Setup < 5 min; projection completes without errors; config via env-only.

---

## 🏗️ Sprint 2 — Graph Model & Temporal Rules
**Goal:** model continuity and n-ary facts in Neo4j.  

- **Deliverables**: finalize query library (counts, traversals), indexing helpers; provenance on relation states; optional `USES_SYSTEM` edges; integration tests against live DB.  
- **Acceptance**: timeline/relations consistent; Cypher library returns expected results on sample graph.  
- **KPIs**: p95 Cypher ≤ 300 ms on core traversals.  

---

## 📑 Sprint 3 — Documents & Notes
**Goal:** ingest, index, and cite external knowledge.  

- **Deliverables**: MinIO → extraction via Tika → Meilisearch/Qdrant pipeline; notes with backlinks; Librarian integration.  
- **Acceptance**: PDFs searchable in FTS + vector; evidence returns citations.  
- **KPIs**: p95 Meilisearch < 200 ms, Qdrant < 350 ms, ≥95% docs with context metadata.  

---

## ✍️ Sprint 4 — Multi-Agent Orchestration
**Goal:** implement co-pilot and auto-pilot workflows.  

**Deliverables**: LangChain (LangGraph) flows — preferred — with optional CrewAI pathways; agent roles (Director, Librarian, Steward, Narrator, Critic, Chat Host); guardrails.  
See `docs/narrative_engine.md` for the consolidated engine design.
- **Acceptance**: co-pilot produces outline, evidence, warnings, draft, critique; auto-pilot produces text + 2 options.  
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
