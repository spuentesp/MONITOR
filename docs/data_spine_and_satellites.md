# Data Architecture — Graph Spine + Satellites

This document defines the “Graph spine + satellites” model used by MONITOR. It is a guardrail: what each store MUST contain, MUST NOT contain, and how they reference each other. Treat this as the contract for persistence and retrieval.

## TL;DR
- One truth per concern: graph for logic/continuity; documents for text; vectors for recall; objects for media.
- Cross-reference everything via IDs; do not double-write facts/relations.
- Promotion path: subjective note → reviewed → objective Fact in graph with provenance.

## Stores and responsibilities

### Neo4j — Graph Spine (authoritative)
- Authoritative for:
  - Identities: EntidadAxiomatica (axiomatic), EntidadConcreta (concrete)
  - All relationships: ALLY_OF, ENEMY_OF, DERIVES_FROM, PARTICIPO_EN/“participated-in”, OCCURS_IN, etc.
  - Objective Facts/Events with temporal attributes: started_at, ended_at, state tags, canon/confidence.
  - Continuity constraints and role/condition tags.
- Why: continuity checks, timeline queries, branching, promotion/diff are graph-native.
- Provenance: Facts can be SUPPORTED_BY → :Source nodes that reference documents or media.

### MongoDB — Narrative & Notes Satellites
- Authoritative for:
  - Session logs (turns), story text (scenes, recaps), GM notes/annotations.
  - Subjective character memory (static/dynamic/perspective-specific).
  - Lightweight configs; document metadata (including MinIO keys).
- Not authoritative for: Entities, Facts, Relations, Continuity — keep only IDs that point to Neo4j.
- Cross-links: every document carries graph IDs to pivot back (universe_id, historia_id/story_id, scene_id, entity_id, fact_id, source_id as applicable).

### Qdrant — Semantic Index
- Contents: embeddings of doc chunks, scene chunks, character-memory entries.
- Payload: includes the same graph IDs (and Mongo document IDs) so a semantic hit can be resolved back to Neo4j/Mongo.
- Derived only: never author here.

### OpenSearch (optional) — Full-text Index
- Contents: same chunks used for Qdrant, indexed for BM25; optional facets/filters.
- Derived only: never author here.

### MinIO — Binary Store
- Contents: PDFs, images, audio, etc.
- Links: Mongo document holds the MinIO key; Neo4j :Source nodes reference that document when used as evidence for a Fact.

## Write flows (single-writer rule by concern)
- Facts / Entities / Relations → write to Neo4j ONLY.
  - If a Mongo record needs these, store their IDs; do not duplicate structure or properties.
- Text / Turns / Notes / Subjective Memory → write to Mongo ONLY.
  - If later promoted to objective truth, create Neo4j :Fact and connect SUPPORTED_BY → :Source referencing the Mongo document.
- Indexes (Qdrant/OpenSearch) → derived from Mongo/Neo4j/MinIO via pipelines; never the other way around.

## Read flows (resolution order)
- Continuity/relations/timeline questions → Neo4j (truth).
- Narrative recall / session context → Mongo (turns/text) + Qdrant/OpenSearch for fuzzy retrieval.
- Evidence/source files → Mongo document metadata → MinIO object; if used as canon, confirm via Neo4j :Source links.

## Where each thing “really” lives
- Entities (axiomatic/concrete): Neo4j (authoritative).
- Facts/Events (objective, temporal): Neo4j (authoritative) with SUPPORTED_BY → :Source.
- Relations & state/tags (roles, conditions, alliances): Neo4j (edges/properties).
- Story text, session turns, GM notes, subjective character memory: Mongo.
- Semantic recall of docs/scenes/memory: Qdrant (payload carries graph + doc IDs).
- Full-text (optional): OpenSearch (derived).
- Binaries: MinIO (referenced by Mongo; sources referenced by Neo4j :Source).

## ID contract (cross-store)
- Use stable IDs and propagate as payload metadata:
  - universe_id, story_id (a.k.a. historia_id), scene_id
  - entity_id, fact_id, relation_id (when applicable)
  - source_id (Neo4j :Source) and doc_id (Mongo _id) for provenance
  - turn_id for session entries
- Mongo documents MUST include relevant graph IDs to pivot back to Neo4j.
- Qdrant/OpenSearch payloads MUST include both graph IDs and doc_id for resolution.

## Promotion path (subjective → objective)
1) A note/memory/scene text is authored in Mongo.
2) Steward/Resolve decide to promote: create a Neo4j :Fact with temporal attrs.
3) Link SUPPORTED_BY → :Source that references the Mongo document and/or MinIO asset.
4) Re-index derived stores.

## Guardrails (MUST / MUST NOT)
- Neo4j MUST be the only writer for Entities, Facts, Relations, Continuity.
- Mongo MUST NOT duplicate graph edges/properties; store IDs only.
- Qdrant/OpenSearch MUST be derived; writes here MUST NOT be considered authoritative.
- All stores MUST carry sufficient IDs to pivot across layers.
- Branching/retcon operations MUST occur in Neo4j first; Mongo records link to the chosen branch via IDs.

## Hooks in the current flow
- LangGraph flow already delegates:
  - Queries/relations/facts via `query_tool` and records via `recorder_tool` (Neo4j authority).
  - Narrative draft/turns live in the application layer and are suitable for Mongo persistence.
  - Resolve-before-recorder gating ensures only vetted deltas reach the spine on autopilot.

## Acceptance checklist
- Given a created Entity/Fact in Neo4j, a Mongo record referencing it by ID can resolve back and pass integrity checks.
- A promoted Mongo note yields a Neo4j :Fact with SUPPORTED_BY → :Source; provenance resolvable to MinIO if binary exists.
- No double-write of edges: relationship edits happen only in Neo4j; Mongo holds references.
- Derived indexes can be rebuilt deterministically from Mongo/Neo4j/MinIO.

## FAQ
- Why not store prose in the graph? Because prose is schemaless and evolves quickly; we keep the graph for logical structure and continuity, not raw text.
- Why a single-writer rule? To avoid drift and complex reconciliation; it simplifies invariants and promotion logic.
