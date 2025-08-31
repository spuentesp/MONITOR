# 🧠 Arquitectura Conceptual del Omniverso Narrativo

Este documento describe los niveles conceptuales del sistema narrativo, su relación con la estructura de datos y los objetivos de modularidad, escalabilidad y personalización.

---

## 🌌 Niveles del Omniverso

| Nivel | Descripción | Entidades clave | Soporte técnico |
|-------|-------------|------------------|-----------------|
| **Omniverso** | La plataforma completa. Coordina agentes, motores, memorias y front-end. | `agents`, `narrative-core`, `memory-orchestrator` | FastAPI, Python, múltiples DBs |
| **Multiverso** | Conjunto de universos conectados o separados, con reglas propias | `universos` (PostgreSQL) | `universo_id`, `sistema_id` |
| **Universo** | Un mundo coherente: cronología, reglas, personajes | `fichas`, `eventos`, `assets`, `historiales` | PostgreSQL + Mongo + Vector DB |
| **Historia** | Línea de eventos narrativos (campaña, crónica, one-shot) | `sesiones`, `notas`, `resúmenes` | MongoDB (`historias`, `sessions`) |
| **Escena** | Evento individual narrado: diálogo, combate, descubrimiento | `eventos`, `logs`, `turnos` | MongoDB / realtime buffer |

---

## 🗃️ Estructura de Datos y Bases

| Base de Datos | Uso Principal | Datos que contiene | Scope |
|---------------|---------------|---------------------|-------|
| **PostgreSQL** | Metadatos estructurados | `universos`, `sistemas`, `fichas`, `tags`, `eventos` | Multiverso / Universo |
| **MongoDB** | Narrativa dinámica y semiestructurada | `sesiones`, `logs`, `notas`, `resúmenes` | Historia / Escena |
| **Vector DB (Weaviate/Chroma)** | Recuperación semántica de contexto | `memoria`, `embeddings`, `anotaciones` | Por universo o historia |
| **MinIO/S3** | Almacenamiento multimedia y versiones | `snapshots`, `imágenes`, `backups` | Assets globales |

---

## 🧩 Modularidad y Aislamiento

Cada universo puede tener:
- Reglas y sistemas distintos
- Bases de datos vectoriales aisladas (`namespace`)
- Estilos narrativos independientes (PG13, Mature, +18)
- Acceso separado para agentes o usuarios

---

## 🧬 Diagrama Mermaid

```mermaid
graph TD
  A["Omniverso: Plataforma Principal"]
  A --> B["Multiverso: Conjunto de Universos"]

  B --> C1["Universo: marvel-616"]
  B --> C2["Universo: noir-neo"]
  B --> C3["Universo: guerra-roja-02"]

  C1 --> D1["Historias (MongoDB)"]
  C1 --> D2["Fichas / Eventos (PostgreSQL)"]
  C1 --> D3["Embeddings / Contexto (VectorDB)"]
  C1 --> D4["Assets Multimedia (MinIO / S3)"]

  D1 --> E1["Sesión 01"]
  D1 --> E2["Sesión 02"]

  A --> X["Narrative Engine"]
  A --> Y["Memory Orchestrator"]
  A --> Z["Agentes IA"]

  subgraph "Infraestructura por universo"
    D1
    D2
    D3
    D4
  end


