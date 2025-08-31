# 🛰️ M.O.N.I.T.O.R.

**Multiversal Ontology for Narrative Intelligence, Temporal Observation & Recording**

M.O.N.I.T.O.R. is a personal system for managing worlds, universes, and stories.  
It uses **intelligent agents** and **polyglot persistence** to narrate, validate, and archive multiversal knowledge — ensuring continuity across timelines and enabling safe exploration of “what-if” branches.

---

## 🎯 Objectives

1. **Manage multiple narrative universes** (canon and what-if) within a personal omniverse.  
2. **Assist storytelling** with agents that consult documents, notes, and canonical facts.  
3. **Maintain continuity and coherence** through temporal graph validation.  
4. **Run locally** with a lightweight Streamlit front end.  

---

## 🗂️ Architecture of Data

- **Neo4j/Memgraph (Graph DB):** n-ary facts, temporal relations, identities, branches.  
- **Meilisearch (FTS):** lightweight full-text search for documents and notes.  
- **Qdrant (Vector DB):** embeddings for semantic retrieval (RAG).  
- **MinIO (S3):** storage for PDFs, HTML, Markdown, and derivatives.  
- **Redis:** cache, queues, and flow control.  
- **Langfuse (+ Postgres):** observability, tracing, and AgentOps metrics.  
- **Tika:** document parsing and text extraction for ingestion.  

---

## 🤖 Agents and Roles

- **Orchestrator:** coordinates agents and workflows (LangGraph/CrewAI).  
- **Director:** plans narrative beats.  
- **Librarian:** retrieves evidence and citations.  
- **Steward:** validates continuity and temporal consistency.  
- **Narrator:** drafts narrative text.  
- **Critic:** evaluates clarity, tone, and coherence.  
- **Chat Host:** interfaces with the user and enforces context.  

---

## 🔄 Core Workflow

1. **Context selection** → `Context Token` (omniverse, multiverse, universe, time_ref, mode).  
2. **Narration** → orchestrator activates agents → beats → evidence → validation → draft → critique.  
3. **Persistence** → narrative stored in Meilisearch/Qdrant; proposed facts in Neo4j.  
4. **What-if** → branch creation (subgraph) and optional promotion to canon.  
5. **Queries** → timeline, relationships, evidence.  
6. **Observability** → latency, coherence, and citation metrics in Langfuse, shown in the Streamlit dashboard.  

---

## 🖥️ Streamlit Frontend

- **Context**: choose omniverse/multiverse/universe/branch.  
- **Narration Console**: prompt, beats, evidence, warnings, draft, actions.  
- **Evidence & Notes**: hybrid search, note editor with backlinks.  
- **Graph & Timeline**: visualize temporal relations and entity neighborhoods.  
- **What-If Manager**: branch list, diffs, promotion to canon.  
- **AgentOps**: metrics of quality and performance.  

---

## 🚀 Development Plan

1. **Foundations**: infra, context tokens, API stubs.  
2. **Graph model**: entities, facts, temporal rules.  
3. **Documents & notes**: ingestion, indexing, embeddings.  
4. **Multi-agent orchestration**: co-pilot and auto-pilot flows.  
5. **What-if branches**: isolation and promotion.  
6. **AgentOps**: traces, metrics, Streamlit dashboards.  

---

## 💰 Costs and Scalability

- **Local (PC, 16–32 GB RAM):** $15–50/month (LLM APIs).  
- **Hybrid (VM for Meilisearch or Langfuse):** $20–50/month.  
- **Full cloud (8 vCPU/32 GB):** $75–200+/month.  

---

## ✅ Value

- **Structured multiverse memory** with graph + temporal validation.  
- **Agent-assisted storytelling** with traceable citations.  
- **Safe branching** with what-if universes.  
- **Lightweight front end** for personal use.  
