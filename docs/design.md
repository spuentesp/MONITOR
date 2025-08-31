# M.O.N.I.T.O.R. — Design Extensions & Integration Addendum (v2, EN)

> **Scope:** This document is **not** part of the ontology. It defines **design extension points** (interfaces, contracts, states) so the MVP is not blocked, without implementing them yet: **ACL, Media/Assets, Agent Integration, Annotations, Search/Discovery, Metadata Evolution, Workflow States, Templates**. It includes minimal YAML/JSON contracts and validation rules.

---

## 1) Design Principles

* **Separation of concerns:** The **ontology** models the narrative world; this addendum models **governance & operations**.
* **Contracts‑first:** Add **optional fields** and **minimal endpoints** that won’t break the MVP.
* **Secure multi‑tenancy:** Every resource resolves via `ContextToken` and `universe_id`.
* **Auditability:** Every relevant mutation must be traceable (who, when, why).

---

## 2) Users & Permissions (Minimal ACL)

**Goal:** read/write control at **Universe** level (optionally **Story**).

**Contract (universe meta YAML):**

```yaml
# universes/earth_616/meta.yaml
schema_version: 1
owner_id: "user:sebas"
acl:
  visibility: "private"   # private|shared|public
  readers: ["user:sebas"]
  writers: ["user:sebas"]
```

**Rules:**

* Backend rejects writes if the `subject` is not in `writers`.
* `visibility=public` allows unauthenticated reads (optional later).
* **Invariant:** all writes require a valid `ContextToken`.

**Future (post‑MVP):** RBAC roles, orgs/teams, Story/Scene/Asset‑level permissions.

---

## 3) Media / Asset Management

**Goal:** reference **PDFs, images, audio, video** with **provenance**.

**Contract (asset index):**

```yaml
# assets/index.yaml
- id: asset-001
  uri: "s3://omniverse/u616/spider-obit.pdf"
  media_type: "application/pdf"
  sha256: "..."
  created_at: "2025-08-31T12:00:00Z"
  linked_to:
    - { type: "Fact", id: "fact-aunt-may-status" }
    - { type: "Entity", id: "ent-aunt-may" }
```

**Policies:** de‑dupe by `sha256`; renditions recorded as `asset-001:thumb`, `asset-001:text`.

**Future:** auto derivatives (OCR/Tika → text), rights/licensing, expiration.

---

## 4) Agent Integration (Narrator, Critic, etc.)

**Goal:** record **invocations** and **effects**, framework‑agnostic.

**Contract (agent run):**

```yaml
# ops/agent_runs.yaml
- run_id: "run-0001"
  agent: "Narrator"
  context_token: { omniverse_id: "omni", multiverse_id: "mv1", universe_id: "u616", mode: "copilot" }
  inputs: { prompt: "Times Square scene…" }
  outputs: { story_id: "spider-saga", scenes_added: 1, draft_tokens: 512 }
  links:
    produced_facts: ["fact-roxxon-explosion"]
    updated_entities: ["ent-peter-616"]
  trace_id: "langfuse:abc123"
  started_at: "2025-08-31T12:00:00Z"
  ended_at:   "2025-08-31T12:00:04Z"
```

**Rules:** idempotency by `run_id`; **writes** go through **Steward** validation before persistence.

**Future:** queues/retries, back‑pressure, human approval policies.

---

## 5) Annotations (non‑canonical comments/meta)

**Goal:** allow comments, TODOs, questions, critiques **without touching canonical data**.

**Contract:**

```yaml
# annotations/index.yaml
- id: note-001
  target: { type: "Scene", id: "sc-002" }
  author: "user:sebas"
  kind: "comment"       # comment|todo|critique|question
  text: "Review antagonist motivation."
  status: "open"         # open|resolved
  created_at: "2025-08-31T12:00:00Z"
```

**Rules:** optional threading via `parent_id`; does not participate in canonical validations.

---

## 6) Search & Discovery (FTS + Vectors)

**Goal:** define the **indexing map** for Meilisearch (FTS) and Qdrant (vectors).

**Mapping contract:**

```yaml
# search/map.yaml
- doc_id: "doc-fact-aunt-may-status"
  source: { type: "Fact", id: "fact-aunt-may-status" }
  indexes: ["fts", "vector"]
  text_ptr: "extracted://assets/asset-001:text"   # optional if derived from Asset
  metadata:
    omniverse_id: "omni"
    multiverse_id: "mv1"
    universe_id: "u616"
    story_id: "spider-saga"
    scene_id: "sc-028"
    tags: ["death", "obituary"]
```

**FTS (Meilisearch):**

* Indexed fields: `title`, `body`, `metadata.*`
* Facets: `universe_id`, `story_id`, `scene_id`, `type`

**Vectors (Qdrant):**

* `embedding` of `body` with **scoping metadata** for filters.

**Hybrid search:** dual query, fuse by **recency/coverage/citation**.

---

## 7) Metadata Evolution (versioning & taxonomy)

**Goal:** change schema/taxonomy without breaking data.

**Rules:**

* Every YAML file begins with `schema_version`.
* Taxonomy (tags, relation roles, fact types) versioned in `taxonomy/version.yaml`.
* Declarative migrations: `migrations/2025-09-xx_*.yaml` with transforms.

**Example:**

```yaml
schema_version: 2
migrations_applied: ["2025-09-02_tags_rename_spiderling->spiderling_v2"]
```

---

## 8) Creation/Approval Workflow

**Goal:** working states for key resources.

**Contract (optional field):**

```yaml
workflow:
  status: "draft"     # draft|review|approved|locked
  by: "user:sebas"
  at: "2025-08-31T12:00:00Z"
```

**Policies:**

* `locked` prevents mutations except by admins.
* Promotion to `approved` requires passing **Steward** with no critical errors.

---

## 9) Templates (Templates ≠ Archetypes)

**Goal:** reusable patterns for **Story/Scene/Entity**, independent of archetypes.

**Contract:**

```yaml
# templates/story.yaml
- id: "three-act"
  kind: "story"
  slots: ["setup","confrontation","resolution"]
  constraints: { min_scenes: 3 }

# templates/scene.yaml
- id: "investigation"
  kind: "scene"
  checklist: ["hook","clue","complication"]
```

**Use:** `story.instantiated_from = "three-act"` (optional).

---

## 10) Minimal Endpoints (aligned to contracts)

* `GET /universes/{u}/meta` → includes `acl`, `workflow`, `schema_version`.
* `POST /annotations` → create non‑canonical annotation.
* `GET /search` → hybrid FTS + vector with `universe_id` filters.
* `POST /ops/agent-runs` → register a run; optional `trace_id`.
* `GET /assets/{id}` → return metadata; access governed by ACL.

---

## 11) Validations (Steward + API)

* **ContextToken is required** for all mutations.
* **ACL**: `writers` required for writes; visibility honors `public|shared|private`.
* **Schema**: known `schema_version`; otherwise warn/suggest migration.
* **Search map** coherence: `source.id` must exist in the graph.
* **Agent runs** idempotent by `run_id`.

---

## 12) Roadmap (when to activate)

* **Sprint 1:** `schema_version`, `acl.visibility`, required `ContextToken`.
* **Sprint 3:** `search/map.yaml`, asset intake & basic extraction.
* **Sprint 4:** `ops/agent_runs.yaml`, traces & effect logging.
* **Sprint 5:** annotations (branch review & diffs).
* **Post‑MVP:** templates, RBAC, richer media & governance policies.

---

## 13) Risks & Mitigations

* **Early coupling:** keep fields **optional** with safe defaults.
* **Tenant leakage:** validate `universe_id` on every read/write.
* **Taxonomy drift:** versioning + declarative migrations.
* **Search load:** indexing queues with retry & backoff.

---

## 14) Adoption Checklist (½–1 day)

* Add `schema_version` to all existing YAMLs.
* Create `universes/*/meta.yaml` with minimal `acl`.
* Seeds: 1 `asset`, 1 `annotation`, 1 `agent_run`.
* Stub endpoints: `GET /search` and `POST /ops/agent-runs` (idempotent).
* Basic Steward validation: `ContextToken` + `acl` + `schema_version`.
