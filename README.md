# 🛰️ M.O.N.I.T.O.R.

**Multiversal Ontology for Narrative Intelligence, Temporal Observation & Recording**

M.O.N.I.T.O.R. is a personal system for **worldbuilding and assisted narration** across multiple universes. It combines a **graph-first ontology**, **hybrid search (FTS + vectors)**, and **multi-agent orchestration** to generate, validate, and archive stories with strong continuity and provenance.

> Goal: make it easy to create and explore canon and “what-if” branches, while keeping timelines, relations, and evidence consistent.

M.O.N.I.T.O.R. is a local-first, multi-agent system for worldbuilding and assisted narration across multiple universes. It uses a harmonized graph-based ontology (Omniverse → Multiverse → Universe → Story → Scene) to model narrative continuity, facts, entities, and relations. The system supports hybrid search (full-text + vector), document ingestion, and branching for "what-if" scenarios. Agents (Orchestrator, Director, Librarian, Steward, Narrator, Critic, Personifier, Chat Host) orchestrate planning, evidence retrieval, validation, drafting, and critique. All canonical data is authored in YAML, with polyglot projections to databases for optimized querying and retrieval. The architecture is modular, with FastAPI backend, Streamlit frontend, and Dockerized services (Neo4j/Memgraph, Meilisearch, Qdrant/Weaviate, MinIO, Redis, Langfuse, ClickHouse).

---

## 🔭 Objectives

1. **Model multiverses coherently**: Omniverse → Multiverse → Universe → Story → Scene.
2. **Assist storytelling**: agents plan beats, retrieve evidence, maintain continuity, and draft text.
3. **Ensure continuity**: temporal graph + validations (axioms, archetype coverage, relation lifecycles).
4. **Enable “what-if” safely**: branch from scenes, isolate changes, promote back to canon with diffs.
5. **Run locally**: lightweight Streamlit UI, Dockerized services, minimal ops burden.

---

---

## 🧱 Core Concepts (Ontology)

* **Omniverse**: the app platform (agents, narrative engine, data, UI).
* **Multiverse**: a family of universes sharing a canonical axiom set and (optionally) a default rule system.
* **Universe**: concrete worldline; holds Entities, Relations, Stories, Scenes, Facts; inherits/overrides axioms.
* **Story**: narrative thread within a Universe; orders **Scenes** (narrative vs chronological).
* **Scene**: atomic unit with world time (and optional session time), participants, and location.
* **Axiom**: rule/tendency governing universes (e.g., “there exists at least one Spider-Totem bearer”).
* **Archetype**: reusable blueprint for entities (constraints on kind/tags/traits).
* **Entity**: character/place/object/org/concept in a Universe; may instantiate an Archetype.
* **Fact**: first-class, time-stamped event/assertion with participants and **provenance** (occurs-in Scene).
* **Relations**: inter-entity links (timeless, interval, or versioned with per-scene change logs).
* **ContextToken**: selects omniverse/multiverse/universe and time-ref; scopes reads/writes and agent runs.

* **Omniverse**: The entire application platform (agents, engine, data, UI).
* **Multiverse**: A family of universes sharing canonical axioms and (optionally) a default rule system.
* **Universe**: A concrete worldline; holds Entities, Relations, Stories, Scenes, Facts; inherits/overrides axioms.
* **Story**: A narrative thread within a Universe; orders Scenes (narrative/chronological/mixed).
* **Scene**: Atomic narrative unit with world time and optional session time, participants, and location.
* **Axiom**: Declarative rule/tendency governing universes; inherited/overridden.
* **Archetype**: Reusable blueprint for entities; constrains kind/tags/traits.
* **Entity**: Character/place/object/organization/concept in a Universe; may instantiate an Archetype.
* **Fact**: First-class, time-stamped event/assertion with participants and provenance (occurs-in Scene).
* **Relation**: Inter-entity link (timeless, interval, or versioned with per-scene change logs).
* **ContextToken**: Selects omniverse/multiverse/universe and time-ref; scopes reads/writes and agent runs.

> Full ontology details live in the canvas **“Ontology Model — Updated With Facts (v2)”**.

---

## 🗃️ Storage Mode: YAML‑first → Polyglot projections

**Authoring is YAML-first.** Databases are **derived projections** (indexes/caches) built from YAML. You **edit YAML**; background ingesters/syncers materialize projections in the polyglot backends.

**YAML source of truth (on disk):**

* `multiverse/axioms.yaml`, `multiverse/archetypes.yaml`
* `universes/<u>/meta.yaml`, `universes/<u>/entities.yaml`, `universes/<u>/facts.yaml`
* `universes/<u>/stories/<story>.yaml`
* `universes/<u>/relations.yaml`
* `annotations/*.yaml`, `assets/index.yaml`

**Projection services (read‑optimized):**

* **Neo4j/Memgraph** (Graph): universes, entities, relations, stories/scenes, **Facts**, axioms/archetypes, branches.
* **Meilisearch** (FTS): documents & notes with scoped metadata (universe/story/scene/type).
* **Qdrant/Weaviate** (Vectors): embeddings for semantic retrieval; filtered by universe/story/scene.
* **MinIO (S3):** PDFs/HTML/MD + derivatives (OCR text) referenced from YAML via URIs.
* **Redis:** cache, task queues, rate control.
* **Langfuse:** traces/metrics for AgentOps.

**Write policy**

* **Do not write directly** to DBs. Canonical writes go to YAML via API/CLI → **Steward** validates → ingesters update projections.
* Projections are **rebuildable** from YAML; DBs act as disposable caches/indexes.

---

## 🧠 Agent Roles

* **Orchestrator**: coordinates the end-to-end flow (planning → retrieval → validation → drafting → critique → persistence).
* **Director**: plans narrative beats given constraints (tone, tags, rating).
* **Librarian**: hybrid retrieval across Meilisearch (FTS) + Qdrant/Weaviate (vectors) and returns **citations**.
* **Steward**: validates continuity (axioms, archetype coverage, temporal overlaps, relation lifecycles).
* **Narrator**: drafts narrative text (co-pilot and auto-pilot modes).
* **Critic**: scores clarity, tone, coherence; suggests revisions.
* **Personifier** (optional): chats as NPCs; scene-level roleplay.
* **Chat Host**: user interface guardrails, ContextToken enforcement.

* **Orchestrator**: Coordinates the end-to-end flow (planning → retrieval → validation → drafting → critique → persistence).
* **Director**: Plans narrative beats given constraints (tone, tags, rating).
* **Librarian**: Hybrid retrieval across Meilisearch (FTS) + Qdrant/Weaviate (vectors); returns citations.
* **Steward**: Validates continuity (axioms, archetype coverage, temporal overlaps, relation lifecycles).
* **Narrator**: Drafts narrative text (co-pilot and auto-pilot modes).
* **Critic**: Scores clarity, tone, coherence; suggests revisions.
* **Personifier**: Chats as NPCs; scene-level roleplay.
* **Chat Host**: User interface guardrails, ContextToken enforcement.

Orchestration stack: **LangGraph** or **CrewAI** (pluggable).

---

## 🏗️ Architecture (Polyglot, Local-first)

**Frontend**

* **Streamlit**: context selector, narration console, evidence viewer, graph/timeline pane, branch manager, AgentOps dashboards.

**Backend**

* **FastAPI**: API gateway, ContextToken enforcement, agents orchestration endpoints.

**Data & Indexing**

* **Neo4j/Memgraph** (Graph DB): universes, entities, relations, scenes, **Facts**, axioms/archetypes, branches.
* **Meilisearch** (FTS): documents & notes with scoped metadata (universe/story/scene/type).
* **Qdrant or Weaviate** (Vector DB): embeddings for semantic retrieval; filters by universe/story/scene.
* **MinIO (S3)**: PDFs/HTML/MD + derivatives (e.g., OCR text).
* **Redis**: cache, task queues, rate-control.
* **Langfuse**: traces, metrics, evaluation hooks (latency, token usage, coherence proxies).
* **Apache Tika** (ingestion): text extraction → chunking → embedding → FTS/vector indexing.

**Data & Indexing Stack**

* **Neo4j/Memgraph**: Graph DB for universes, entities, relations, scenes, Facts, axioms/archetypes, branches.
* **Meilisearch**: Full-text search for documents & notes with scoped metadata.
* **Qdrant/Weaviate**: Vector DB for semantic retrieval; filters by universe/story/scene.
* **MinIO (S3)**: Storage for PDFs/HTML/MD + derivatives (OCR text).
* **Redis**: Cache, task queues, rate control.
* **Langfuse**: Traces, metrics, evaluation hooks.
* **ClickHouse**: Analytics/traces (used for AgentOps dashboard).
* **Apache Tika**: Text extraction for ingestion pipeline.

**Models (pluggable)**

* **LLMs**: any OpenAI-compatible or local model (quality↔cost configurable).
* **Embeddings**: instruct/ctx-length-friendly models for robust RAG (local or API).
* **Safety/tone**: optional classifiers for rating (PG-13, Mature, +18) at Story scope.

---

## 🔁 High-Level Flow

1. **Context**: user selects omniverse/multiverse/universe (+ optional time-ref).
2. **Plan** (Director): produce beats within constraints (tone, rating, system of rules if attached).
3. **Retrieve** (Librarian): hybrid search FTS+vector; return **evidence + citations**.
4. **Validate** (Steward): axioms, archetypes, temporal/relational consistency; warnings if needed.
5. **Draft** (Narrator) → **Critique** (Critic) → optional **Revise**.
6. **Persist**: narrative, Facts, relation deltas; index to FTS & vectors with scoped metadata.
7. **Branching** (optional): branch **from a Scene**; isolate changes; compare **diffs**; promote to canon.

---

## 🧪 Primary Use Cases

* **GM campaign manager (DM workflow):** track sessions, scenes, PCs/NPCs, rules/stats lookups, dice logs, and session summaries. Persist updates as **Facts**, entity state changes, and relation deltas tied to Scenes; auto‑index notes for retrieval.
* **Solo / 1‑on‑1 runtime with dice systems:** run scene‑by‑scene narration using a selected YAML rule system (e.g., PbtA, D\&D 3.5, City of Mist). Manage character sheets/resources, perform rolls (success/partial/failure, contested checks, crits), and carry memory across Scenes/Stories.
* **Assisted narration:** co-pilot outlines beats and drafts scenes with evidence-backed details.
* **Continuity checks:** ensure events and relations don’t violate canon or timelines.
* **What-if exploration:** branch from key scenes, simulate consequences, compare and selectively promote.
* **Knowledge-backed storytelling:** import PDFs/notes, cite sources in output, link to graph entities and scenes.
* **NPC conversations** (optional): run scene-bound dialogue with memory tied to entities and Facts.

> Both GM and Solo modes rely on the **rules YAML** (stats/resources/roll mechanics) and produce auditable **Facts** and **RelationState** changes with Scene provenance.

---

## 🛠️ Components & Responsibilities

* **Narrative Engine**: YAML loaders (systems of rules), scene/story ordering policies, relation lifecycle helpers, fact/scene provenance guards.
* **Steward**: invariants (DAGs for NEXT\_\* chains, contiguous sequence indices, non-overlapping intervals), axiom coverage, archetype constraints, fact-backed transitions.
* **Search Indexer**: Tika extraction → chunking → embeddings → Meilisearch/Qdrant with (omniverse/multiverse/universe/story/scene/type) metadata.
* **AgentOps**: Langfuse traces per phase (plan/evidence/continuity/draft/critique/persist); Streamlit dashboard.
* **Branch Manager**: DERIVES\_FROM lineage, typed diffs (new Facts, relation changes, state edits).

---

## 🧰 Getting Started (local)

> Minimal outline — adapt to your environment.

1. **Prereqs**: Docker & Docker Compose, Python 3.11+.
2. **Clone repo** & copy example env: `.env.example → .env` (LLM keys optional).
3. **Start services**: `docker compose up -d` (Neo4j/Memgraph, Meilisearch, Qdrant/Weaviate, MinIO, Redis, Langfuse).
4. **Backend**: `uvicorn backend.main:app --reload` (FastAPI).
5. **Frontend**: `streamlit run frontend/Home.py`.
6. **Open**: Streamlit UI → select context → try **co-pilot** narration.

> Ingestion: upload a PDF/MD/HTML **or edit YAML**; the pipeline extracts/loads, chunks, embeds, and indexes to FTS & vectors with proper scoping.

---

## 🔒 Governance & Ops (lightweight, opt-in)

See **Design Extensions & Integration Addendum (EN)** for:

* Minimal **ACL** (universe meta YAML),
* **Annotations** (non-canonical notes),
* **Agent run** logs (framework-agnostic),
* **Search map** contract (FTS/vector),
* **Schema/taxonomy versioning** and migrations,
* **Workflow states**: draft/review/approved/locked.

See **Design Extensions & Integration Addendum (EN)** for:

* **ACL**: Universe-level access control (owner, readers, writers, visibility).
* **Annotations**: Non-canonical comments, TODOs, critiques, questions.
* **Agent run** logs (framework-agnostic).
* **Search map** contract (FTS/vector).
* **Schema/Taxonomy Versioning**: Managed via schema_version and migrations.
* **Workflow States**: draft, review, approved, locked.

---

## 🧭 Roadmap (Sprints Summary)

1. **Foundations**: containers, ContextToken, API stubs.
2. **Graph model**: entities, relations, scenes, **Facts**, temporal rules (Steward v1).
3. **Docs & notes**: ingestion → FTS + vectors; citations; note editor with backlinks.
4. **Multi-agent orchestration**: co-pilot/auto-pilot flows with guardrails.
5. **What-if branches**: isolation, diffs, promotion to canon.
6. **AgentOps**: Langfuse traces + Streamlit dashboards (latency, coherence, citations).

1. **Foundations**: containers, ContextToken, API stubs.
2. **Graph model**: entities, relations, scenes, Facts, temporal rules (Steward v1).
3. **Docs & notes**: ingestion → FTS + vectors; citations; note editor with backlinks.
4. **Multi-agent orchestration**: co-pilot/auto-pilot flows with guardrails.
5. **What-if branches**: isolation, diffs, promotion to canon (DERIVES_FROM, branch diffs).
6. **AgentOps**: Langfuse traces + Streamlit dashboards (latency, coherence, citations).

---

## 📄 License

**PolyForm Noncommercial 1.0.0** — free for personal and non-commercial use; commercial use requires a separate license.
(Include the full license text in `LICENSE`.)

---

## 🙌 Who is this for?

* **Worldbuilders / GMs** who want canonical, searchable universes and story assistance.
* **AI practitioners** exploring **state-of-the-art RAG + multi-agent** architectures with graph memory and provenance.
* **Writers** interested in consistent, evidence-backed narrative generation and safe “what-if” ideation.

---

## 📎 References (internal)

* **Ontology**: *Ontology Model — Updated With Facts (v2)*
* **Design addendum**: *M.O.N.I.T.O.R. — Design Extensions & Integration Addendum (EN)*
* **Narrative Engine**: `docs/narrative_engine.md` (consolidated design)

> Tip: Start small. Create one Universe, one Story with a few Scenes, edit YAML or ingest two documents, and let the co-pilot draft a scene. Then add a what-if branch and compare diffs.
