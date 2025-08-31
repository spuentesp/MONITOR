# 🎮 Diseño Formal del Subsistema de Sistemas de Rol para el Narrador Automático

## 🎯 Objetivo General

Permitir que el narrador automático integre e interprete diversos sistemas de rol (como PbtA, D\&D 5e, Fate, etc.), asociados a universos o historias específicas. Esto habilita el uso de tiradas, stats, condiciones y progresiones coherentes con la ficción, permitiendo:

* Resoluciones automatizadas de tiradas.
* Control de puntos de vida, recursos y condiciones.
* Seguimiento de progresión y niveles.
* Creación de personajes asistida por narrativa.
* Adaptación flexible a diferentes lógicas de éxito (completo, parcial, fracaso).
* Tiradas enfrentadas, críticos y modificaciones dinámicas.

## 🧱 Fundamentos del Diseño

### 🛏️ Herencia Multinivel

* **Multiverso** define un sistema base por defecto.
* **Universo** puede sobrescribir el sistema del multiverso.
* **Historia** puede sobrescribir el sistema del universo.
* Herencia clara, basada en profundidad narrativa (de general a particular).

### 🧩 Modularidad y Extensibilidad

* Formato serializable en YAML o JSON.
* Carga dinámica por parte del narrador automático.
* Separación entre definición (schema) e instancias cargadas.
* Fácil integración de nuevos sistemas mediante archivos autodescriptivos.

---

## 📘 Especificación de Componentes

### 📌 `system`

```yaml
name: string
version: string
description: string
dice_pool: ["d4", "d6", "d8", "d10", "d12", "d20", "d100"]
stats: [Stat]
resources: [Resource]
conditions: [Condition]
tags: [Tag]
actions: [Action]
roll_mechanic: RollMechanic
resolution_rules: [ResolutionRule]
progression: ProgressionSystem
character_creation: CharacterCreation
critical_rules: CriticalRules
metadata: dict
```

### 📊 `Stat`

```yaml
name: string
abbr: string
range: [min, max]
default: int
derived: bool
formula: string?
```

### 🔋 `Resource`

```yaml
name: string
type: ["counter", "track", "slot", "custom"]
min: int
max: int | "variable"
replenishment: string?
```

### 🍿 `Tag`

```yaml
name: string
type: ["trait", "equipment", "perk", "custom"]
description: string
effect: string?
```

### ☕️ `Condition`

```yaml
name: string
duration: string
effect: string
```

### 🧽 `Action`

```yaml
name: string
type: ["basic", "combat", "move", "custom"]
trigger: string
roll: string?
tags: [string]
```

### 🎲 `RollMechanic`

```yaml
base_roll: string
target_type: ["fixed", "vs_opponent", "lookup"]
target_value: string?
modifier_sources: [string]
```

### ✅ `ResolutionRule`

```yaml
range: string  # e.g., "10-12"
outcome: string  # e.g., "success", "partial", "failure"
effects:
  - type: string
    target: string
    value: any
```

### 📈 `ProgressionSystem`

```yaml
type: ["level", "xp", "milestone", "none"]
max_level: int
gains:
  - level: int
    stat_increase: dict
    resource_max: dict
    new_actions: [string]
```

### 📃 `CharacterCreation`

```yaml
methods: ["point_buy", "random_roll", "template", "narrative"]
default_stats: dict
starting_tags: [string]
starting_conditions: [string]
choices:
  - question: string
    affects: ["stats", "resources", "tags"]
    options:
      - label: string
        value: dict
```

### ✨ `CriticalRules`

```yaml
critical_success: ["natural_20", "double_6"]
critical_failure: ["natural_1", "snake_eyes"]
critical_effects:
  success: string
  failure: string
```

---

Este diseño permite representar de forma estructurada y extensible cualquier sistema de rol compatible con el motor del narrador automático. A través de esta abstracción, los universos y escenarios podrán definir mecánicas específicas sin romper la coherencia del sistema general.

Es posible incorporar automatizaciones como:

* Monitoreo de tiradas por historia.
* Tiradas enfrentadas entre personajes.
* Adaptación narrativa en base a resultados de tiradas.
* Interpretación de condiciones especiales y efectos persistentes.

La estructura es lo suficientemente amplia como para modelar desde sistemas ligeros (PbtA, FATE) hasta complejos (5e, GURPS).
