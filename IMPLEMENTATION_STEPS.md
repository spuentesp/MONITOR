# 🚀 M.O.N.I.T.O.R. — Implementation Sprints

**Multiversal Ontology for Narrative Intelligence, Temporal Observation & Recording**

This document expands and formalizes the step-by-step implementation tasks of each sprint.

---

## 🏁 Sprint 1 — Foundations & Infrastructure

**Objective:** Prepare foundational services and set up context handling system.

### Key Deliverables:

* A fully working Docker Compose stack.
* FastAPI project with placeholder endpoints.
* ContextToken schema with initial logic.

### Steps:

1. **Repository Initialization:**

   * Create Git repository.
   * Define base structure:

     * `/backend/` (FastAPI app)
     * `/frontend/` (Streamlit app)
     * `/docker/` (service configs)
     * `/docs/` (project documentation)

2. **Write `docker-compose.yml`** with services:

   * `neo4j` or `memgraph` (graph storage)
   * `opensearch` (FTS engine)
   * `qdrant` (vector store)
   * `minio` (object storage)
   * `redis` (state/queue/cache)
   * `clickhouse` (observability)

3. **Volumes & Networking:**

   * Add `volumes` per service to preserve data.
   * Expose ports and internal networking.
   * Add `.env` and bind secrets.

4. **Startup & Health Check:**

   * `docker compose up`
   * Use health checks or manual curl checks.
   * Test basic connectivity.

5. **FastAPI Skeleton:**

   * Add placeholder routes with `@router.get` / `@router.post` decorators:

     * `/contexts/switch`
     * `/entities`, `/facts`, `/notes`, `/ingest/file`, `/narrate`, `/universes/branch`

6. **Pydantic Schema: `ContextToken`**

   ```python
   class ContextToken(BaseModel):
       omniverse_id: str
       multiverse_id: str
       universe_id: str
       time_ref: Optional[str]
       mode: Literal['read', 'write', 'observe']
   ```

---

## 🏗️ Sprint 2 — Graph Model & Temporal Rules

**Objective:** Build the continuity and contradiction engine in Neo4j.

### Deliverables:

* Cypher schema and indexing strategies.
* CRUD APIs for entities, facts, participations.
* Basic continuity checker (Steward v1).

### Steps:

1. **Design Graph Schema:**

   * `(:Entity)` with `name`, `type`, `tags`
   * `(:Fact)` with `description`, `started_at`, `ended_at`, `canon_level`, `confidence`
   * `(:Participation)` to link `Entity` to `Fact` with `role`
   * `(:Source)` for citations
   * Relationships:

     * `[:HAS_ROLE]`
     * `[:SUPPORTED_BY]`
     * `[:CONTRADICTS]`

2. **Backend Endpoints:**

   * `/entities` → POST `name`, `type`
   * `/facts` → POST fact with time & meta
   * `/participations` → POST `entity_id`, `fact_id`, `role`

3. **Temporal Logic:**

   * Allow `null` start or end dates.
   * Compute overlaps between facts.
   * Add indexing strategies in Neo4j for time-based queries.

4. **Cypher Queries:**

   * Timeline of an entity:

     ```cypher
     MATCH (e:Entity {id: $id})-[:HAS_ROLE]->(p:Participation)-[:PART_OF]->(f:Fact)
     RETURN f ORDER BY f.started_at
     ```
   * Neighborhood map:

     ```cypher
     MATCH (e:Entity {id: $id})-[*1..$depth]-(related)
     RETURN DISTINCT related
     ```

5. **Steward v1 Logic:**

   * Contradiction checks:

     * Same entity in two places (facts with time overlaps).
     * Role conflicts.
     * Ally vs Adversary in same timeframe.

6. **Expose Validation Endpoint:**

   * `/facts/validate` triggers steward checks and returns contradictions.

---

## 📁 Sprint 3 — Document Ingestion & Notes

**Objective:** Ingest external documents and connect their data into the knowledge base.

### Deliverables:

* Ingest pipeline for text sources.
* Dual indexing: FTS (OpenSearch) + semantic (Qdrant).
* CRUD for notes.

### Steps:

1. **File Upload Endpoint:**

   * `/ingest/file` accepts `.pdf`, `.md`, `.html`
   * Store original file in MinIO under namespace by context

2. **Text Extraction Pipeline:**

   * Use Unstructured.io or Apache Tika
   * Output: structured chunks with page numbers or headings

3. **Indexing Steps:**

   * **OpenSearch**: create index per context
   * **Qdrant**: embed each chunk (with context metadata)

     ```json
     {
       "omniverse": "alpha",
       "multiverse": "001",
       "universe": "default",
       "doc_id": "avengers_manual",
       "chunk": 7,
       "text": "..."
     }
     ```

4. **Notes System:**

   * Endpoint `/notes` → CRUD for user notes
   * Store in OpenSearch
   * Optional: embed in Qdrant if semantic recall is needed

5. **Librarian Agent:**

   * Query FTS + semantic DBs
   * Combine & rerank top hits
   * Return citations (source + page + confidence)

# 📐 M.O.N.I.T.O.R. — Sprint 2: Graph Model & Temporal Rules

**Goal:** Model continuity and facts in the graph database (Neo4j or Memgraph), enabling temporal reasoning and contradiction detection.

---

## 🧠 Conceptual Model

### 📦 Nodes:

* `Entity`: a person, object, place, or abstract concept.
* `Fact`: a piece of information or event that occurred.
* `Participation`: role-based connection between entity and fact.
* `Source`: a document or external input that supports a fact.

### 🔗 Relationships:

* `(:Entity)-[:PARTICIPATED_AS {role}]->(:Fact)`
* `(:Fact)-[:SUPPORTED_BY]->(:Source)`
* `(:Fact)-[:CONTRADICTS]->(:Fact)` (bidirectional when applicable)

---

## 📅 Temporal Attributes on Facts:

* `started_at`: ISO datetime or timestamp (required)
* `ended_at`: optional end time (null if ongoing)
* `canon_level`: float (0.0–1.0) — how "official" this fact is
* `confidence`: float (0.0–1.0) — belief in the fact's accuracy

---

## ⚙️ Endpoints to Implement

### 1. `POST /entities`

* Input: `{ name, type }`
* Action: creates `(:Entity)` node

### 2. `POST /facts`

* Input: `{ description, started_at, ended_at, canon_level, confidence }`
* Action: creates `(:Fact)` node

### 3. `POST /participations`

* Input: `{ fact_id, entity_id, role }`
* Action: creates relationship with `:PARTICIPATED_AS {role}`

---

## 🔍 Cypher Queries to Build

### A. Timeline for an Entity:

```cypher
MATCH (e:Entity {id: $entityId})-[:PARTICIPATED_AS]->(f:Fact)
RETURN f ORDER BY f.started_at ASC
```

### B. Neighborhood / Relation Map:

```cypher
MATCH (e:Entity {id: $entityId})-[*1..$depth]-(n)
RETURN n
```

### C. Contradiction Finder:

```cypher
MATCH (f1:Fact)-[:PARTICIPATED_AS]->(e:Entity)<-[:PARTICIPATED_AS]-(f2:Fact)
WHERE f1 <> f2 AND abs(duration.between(f1.started_at, f2.started_at).hours) < 1
  AND f1.location <> f2.location
RETURN f1, f2, e
```

---

## 🛡️ Steward v1 — Validations

The **Steward Agent** will:

* Detect spatial/temporal contradictions:

  * Same entity in two places at the same time.
  * Overlapping facts with conflicting claims.

* Detect identity conflict:

  * Two entities with overlapping names or roles but distinct histories.

* Raise canonical conflicts:

  * If a low-confidence fact contradicts a high-canon-level one.

### Example Output:

```json
{
  "conflict_type": "temporal_overlap",
  "entity": "Peter Parker",
  "facts": ["at Oscorp", "fighting Rhino"],
  "overlap": true,
  "recommendation": "Review timestamps or downgrade one fact"
}
```

---

## 🌐 API Validation Endpoint

### `POST /facts/validate`

* Input: JSON with new fact and participations
* Output: validation results from the Steward

This will ensure **no fact enters the database unvalidated**.

# 📑 Sprint 3 — Document Ingestion & Notes

**Goal:** Ingest, extract, index, and cite external knowledge for use in narratives and fact-checking.

---

## 📁 1. Ingestion Service Setup

### 🔹 Endpoints

* `POST /ingest/file`

  * Accepts files (PDF, Markdown, HTML).
  * Metadata required: `omniverse_id`, `multiverse_id`, `universe_id`, `doc_type`, `source_name`, `source_date`.

### 🔹 Storage

* Store raw files in **MinIO** under bucket `documents`.
* Path pattern: `omniverse_id/multiverse_id/universe_id/{doc_id}.{ext}`

### 🔹 Tasks

* Add FastAPI file upload handler.
* Generate a UUID for each `doc_id`.
* Store metadata in Neo4j as node `Document`:

  ```
  (:Document {doc_id, source_name, source_date, type, path})
  ```
* Connect to `Fact` nodes via `(:Fact)-[:SUPPORTED_BY]->(:Document)` later during fact creation.

---

## 🧠 2. Text Extraction Pipeline

### 🔹 Libraries

* Prefer `Unstructured` for flexibility. Fallback to Apache Tika for legacy formats.
* Extracted fields: `title`, `author`, `date`, `text`, `sections/pages`.

### 🔹 Preprocessing

* Chunk by:

  * Markdown headers.
  * PDF pages.
  * HTML sections.
* Clean special characters, extract timestamps if available.

### 🔹 Output Format

```json
{
  "doc_id": "uuid",
  "chunks": [
    {
      "chunk_id": "doc_id#1",
      "text": "...",
      "section": "Background",
      "page": 1
    },
    ...
  ]
}
```

---

## 🧭 3. Indexing

### 🔹 OpenSearch

* Index `chunk_id`, `text`, `metadata`.
* Mapping:

```json
{
  "omniverse_id": "string",
  "multiverse_id": "string",
  "universe_id": "string",
  "doc_id": "string",
  "page": "integer",
  "section": "string"
}
```

* Index: `docs-text`

### 🔹 Qdrant

* Use sentence embeddings (e.g., `all-MiniLM-L6-v2`).
* Store vector with same metadata as OpenSearch.
* Collection name: `doc-embeddings`

---

## ✏️ 4. Notes & User Annotations

### 🔹 Endpoints

* `POST /notes`: Create note
* `GET /notes`: List notes by context
* `PUT /notes/{note_id}`
* `DELETE /notes/{note_id}`

### 🔹 Storage

* Store raw note in OpenSearch.
* Optional: embed text into Qdrant for semantic retrieval.
* Connect notes to documents and entities if possible.

### 🔹 Metadata

* `note_id`, `author`, `created_at`, `doc_id?`, `entity_id?`, `text`

---

## 🧑‍🏫 5. Librarian Agent

### 🔹 Responsibilities

* Query OpenSearch (full-text) and Qdrant (semantic).
* Combine and rank results.
* Generate citation JSONs:

```json
{
  "quote": "...",
  "doc_id": "...",
  "page": 3,
  "section": "Origins",
  "link": "/viewer/..."
}
```

### 🔹 Query Flow

1. Receive input query or narrative request.
2. Perform hybrid search (FTS + Vector).
3. Filter by universe context.
4. Deduplicate and rank results.
5. Return citations to Narrator or Director agents.

---

## ✅ Completion Criteria

* Documents can be uploaded and parsed.
* Metadata + raw files stored in MinIO and Neo4j.
* Text chunks indexed in OpenSearch and Qdrant.
* Notes can be created and retrieved.
* Librarian agent operational with hybrid search and citation output.

# ✍️ Sprint 4 — Multi-Agent Orchestration

**Goal:** Implement co-pilot and auto-pilot workflows.

---

## 🔄 Overview

This sprint introduces LangGraph (or an equivalent orchestration framework such as CrewAI or LiteLLM Agents) to manage multi-agent workflows. The system will allow users to request assistance via a **co-pilot** (user-in-the-loop) or **auto-pilot** (fully automated) mode for generating narratives, branching timelines, or worldbuilding scenarios.

Agents will collaborate following a pre-defined state machine with checkpoints for planning, continuity validation, and quality control.

---

## 📆 Tasks

### 1. **Install & Configure LangGraph / CrewAI / Orchestrator**

* Add dependency to the chosen orchestration framework.
* Create a base graph or task flow engine to manage agent transitions.
* Create a reusable module to:

  * Register agents.
  * Define state transitions.
  * Enforce guardrails.

### 2. **Define Agent Roles and State Machine**

Define the main workflow as a directed graph with the following states:

| State        | Description                                      | Agent     |
| ------------ | ------------------------------------------------ | --------- |
| `plan`       | Generates narrative beats or tasks               | Director  |
| `evidence`   | Retrieves citations from vector & fulltext index | Librarian |
| `continuity` | Validates against graph contradictions           | Steward   |
| `draft`      | Writes the output (story, recap, etc.)           | Narrator  |
| `critique`   | Evaluates quality: tone, coherence, logic        | Critic    |
| `persist`    | Saves story, embeddings, citations, graph edges  | Recorder  |

Transitions:

* `plan → evidence → continuity → draft → critique → persist`
* If critique fails: loop back to `draft`
* All agents emit logs for traceability

### 3. **Implement Agent Prompts and Behaviors**

Each agent gets a structured prompt template:

* **Director**

  * Input: user request + current context
  * Output: list of `beats` or `objectives`
  * Example prompt: *"You are a story director. Given the following universe and characters, produce a list of plot beats for the next scene."*

* **Librarian**

  * Searches OpenSearch (FTS) and Qdrant (vector)
  * Returns citations (ID, source, relevance)
  * Optional: embeds missing documents

* **Steward**

  * Checks temporal/logical contradictions in Neo4j
  * Flags violations: same entity in two places, canon conflicts, etc.

* **Narrator**

  * Writes final text
  * Conditions: must cite sources, follow beats

* **Critic**

  * Scoring: clarity, tone, coherence
  * Feedback for Narrator if score < threshold

* **Recorder**

  * Stores:

    * Story in OpenSearch
    * Embeddings in Qdrant
    * Facts or events in Neo4j

### 4. **Implement Entry Points**

Create two API routes:

* `/narrate?mode=copilot` — requires user approval before `persist`
* `/narrate?mode=autopilot` — full automation

Each route initializes LangGraph (or equivalent) with:

* ContextToken (from prior sprints)
* Input prompt or user query
* Callback functions for logging/tracing

### 5. **Add Guardrails**

* Narrator **cannot** write directly to Neo4j
* Steward must approve any fact persistence
* Critic must pass quality threshold before Recorder is triggered
* Fail-safe fallback: manual review if multiple agents disagree

---

## ✅ Deliverables

* LangGraph (or CrewAI/LiteLLM) workflow file
* Agent prompt templates
* API endpoints integrated with FastAPI
* Tracing log format per agent
* Agent test suite (unit + integration)

# 🌿 Sprint 5 — What-If Branches (Canvas Form)

**Objective:** Safely manage alternate universe branches for speculative narrative exploration.

---

## 🌟 Purpose

Enable isolated scenario experimentation via universe branching and promotion, while ensuring continuity integrity.

---

## 🧱 Core Components

| Component  | Role Description                               |
| ---------- | ---------------------------------------------- |
| Neo4j      | Holds subgraphs identified by `universe_id`.   |
| OpenSearch | Indexes texts with universe context.           |
| Qdrant     | Stores embeddings scoped per universe.         |
| FastAPI    | Exposes endpoints for branching and promotion. |
| Streamlit  | Provides visual universe management interface. |

---

## 🛠️ Implementation Steps

### 1. Endpoint: `/universes/branch`

* **Method:** `POST`
* **Request Body:**

```json
{
  "parent_universe_id": "u-001",
  "branch_name": "Rogue-never-leaves-Xavier",
  "author": "Sebas"
}
```

* **Behavior:**

  * Copies parent metadata
  * Assigns new `universe_id` (e.g. `u-001-b1`)
  * Duplicates Neo4j subgraph

* **Cypher Example:**

```cypher
MATCH (n {universe_id: 'u-001'})-[:RELATED_TO*0..]->(m)
WITH collect(distinct m) AS nodes
UNWIND nodes AS node
CALL {
  WITH node
  CREATE (copy:NodeType { ...node.props, universe_id: 'u-001-b1' })
}
RETURN count(*)
```

---

### 2. Update Indexing Pipelines

* Add `universe_id` metadata to all document, note, and embedding entries:

```json
{
  "text": "Alternate timeline event",
  "universe_id": "u-001-b1",
  "source": "notes/rogue-alt.txt"
}
```

---

### 3. Endpoint: `/universes/promote`

* **Method:** `POST`
* **Request Body:**

```json
{
  "branch_id": "u-001-b1",
  "parent_id": "u-001",
  "approved_by": "CriticAgent",
  "reason": "Narrative coherence approved"
}
```

* **Behavior:**

  * Diff analysis between parent and branch
  * Optional node merge or overwrite
  * Canonical `universe_id` update

---

### 4. Streamlit Visual Interface

* Universe & Branch Overview

  * Table: universe ID, branch ID, authors, created date
* Diff Viewer

  * Show added facts, modified entities, conflicting notes
* Promote Branch Button

  * Validates via `StewardAgent`

---

## 🔐 Rules & Safeguards

* One active branch per universe until resolved
* All branches require metadata (author, reason, origin)
* Promotion only allowed if `StewardAgent` confirms logical consistency

---

## 📊 Metrics (KPIs)

| Metric                     | Target         |
| -------------------------- | -------------- |
| Branch creation time       | < 2 seconds    |
| Promotion latency          | < 4 seconds    |
| Data leak across universes | Zero tolerance |

---

## 📦 Deliverables Summary

### API Endpoints

* ✅ `POST /universes/branch` — Create speculative universe
* ✅ `POST /universes/promote` — Canonicalize branch if valid
* ✅ `GET /universes/list` — Universe and branch listings

### Core Scripts & Utilities

* ✅ `diff_engine.py` — Fact-level comparison between universes
* ✅ `universe_utils.py` — Utility functions for cloning graphs and managing IDs
* ✅ `scripts/debug_branch_graphs.py` — Helper script to visually compare subgraphs

### Frontend

* ✅ `Streamlit` UI — Visual branch manager with creation, diff, and promotion tools

### Metadata & Indexing

* ✅ `universe_id` added to every search, index and query pipeline

### Testing & Docs

* ✅ `tests/test_branching.py` — Unit tests for branch and promote behavior
* ✅ `docs/universe_versioning.md` — Developer guide on managing alternate timelines

# 🌀 Sprint 6 — Multiverse Agents & Specialized Roles (Canvas Form)

**Objective:** Deploy and orchestrate specialized agents for narrative evaluation, generation, and maintenance across universes.

---

## 🌟 Purpose

Introduce multi-agent capabilities to assess, enrich, and manage narrative branches, ensuring modular intelligence and robust editorial control.

---

## 🧠 Key Agents & Roles

| Agent         | Purpose                                                     |
| ------------- | ----------------------------------------------------------- |
| NarratorAgent | Generates and extends storylines within a given universe.   |
| CriticAgent   | Evaluates coherence, pacing, tone, and continuity.          |
| StewardAgent  | Governs canonization, checks for paradoxes and conflicts.   |
| SynthAgent    | Aggregates alternate branches into meta-narratives.         |
| OracleAgent   | Predicts likely outcomes of storylines based on prior data. |

---

## 🛠️ Implementation Steps

### 1. Agent Registration & Metadata

* Each agent is declared via a config YAML or registry class:

```yaml
- id: narrator
  class: agents.NarratorAgent
  capabilities: [generate, rewrite]
  allowed_universes: ["*"]
```

---

### 2. Core Interfaces

* `Agent.run(task: AgentTask) -> AgentResponse`
* `AgentTask`:

```json
{
  "task_type": "evaluate",
  "universe_id": "u-001-b1",
  "input_text": "Rogue joins SHIELD in 2008...",
  "metadata": { "source": "branch_notes/rogue-shield.txt" }
}
```

* `AgentResponse` includes flags, scores, suggested edits.

---

### 3. Orchestrator Layer

* Accepts a `TaskRequest`
* Assigns to appropriate agent(s) based on routing rules
* Collates results, applies voting/consensus if needed

```json
{
  "task": "evaluate",
  "targets": ["CriticAgent", "StewardAgent"],
  "payload": { ... }
}
```

---

### 4. Integration with Streamlit

* Assign agents to universe or branch
* Display evaluations, flags, and suggestions inline
* Manual override by human editors if needed

---

## 🛡️ Safeguards & Governance

* Only `StewardAgent` can allow promotion
* Agents cannot self-promote or modify universes
* Audit log tracks all agent actions and justifications

---

## 🧪 Testing & Evaluation

| Test Case                       | Description                                    |
| ------------------------------- | ---------------------------------------------- |
| `test_coherence_check.py`       | Ensures CriticAgent flags inconsistent events  |
| `test_branch_voting.py`         | Orchestrator selects correct agent consensus   |
| `test_generator_constraints.py` | Verifies NarratorAgent respects branch history |

---

## 📦 Deliverables Summary

### Agents

* ✅ `NarratorAgent` — Story generator within universe
* ✅ `CriticAgent` — Quality assurance and narrative evaluation
* ✅ `StewardAgent` — Guardian of canon and consistency
* ✅ `OracleAgent` — Forecast possible evolutions
* ✅ `SynthAgent` — Merges or summarizes divergent timelines

### Utilities & Infra

* ✅ `agent_interface.py` — Common agent class & datatypes
* ✅ `orchestrator.py` — Task router and aggregator
* ✅ `agent_registry.yaml` — Config for allowed agents and capabilities

### Frontend

* ✅ Streamlit agent dashboard for viewing results, flags, decisions

### Docs & Tests

* ✅ `docs/agents.md` — Developer guide for building and registering agents
* ✅ `tests/test_agents/*.py` — Unit tests for each agent’s behavior and responses



