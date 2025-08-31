# 🧠 Glosario y Terminología Central del Proyecto Narrativo

## 🌌 Omniverso
**Definición:** La aplicación completa. Contiene todos los subsistemas: motor narrativo, agentes, UI, almacenamiento, etc.

- Es la entidad macro donde existen todos los multiversos.
- Controla la lógica de sesión, almacenamiento, configuración de usuarios, y agentes activos.

## 🌐 Multiverso
**Definición:** Un conjunto coherente de universos que comparten reglas narrativas, un sistema de rol base y un estilo general.

- Se le asigna un sistema de rol por defecto.
- Puede representar una franquicia, ambientación o conjunto de historias conectadas.
- Ejemplo: "Multiverso Marvel" o "Mundos de Lovecraft".

## 🌍 Universo
**Definición:** Un mundo dentro de un multiverso, con sus propias reglas específicas, personajes y tono.

- Puede sobrescribir el sistema de rol del multiverso.
- Tiene continuidad interna.
- Ejemplo: "Tierra-616" dentro del Multiverso Marvel.

## 📖 Historia
**Definición:** Una narración específica dentro de un universo, como una campaña o sesión.

- Puede tener un sistema propio si desea reglas distintas (e.g., un one-shot con otras reglas).
- Puede contener líneas de tiempo, registros de eventos, progresiones, y tiradas.

---

## 🧠 Narrative Engine (Motor Narrativo)
**Definición:** El núcleo lógico que permite generar, expandir, y estructurar historias con base en reglas narrativas y de juego.

- Lee YAMLs de sistemas de rol para interpretar tiradas, condiciones, progresión, etc.
- Ejecuta lógica narrativa, seguimiento de eventos y control de consistencia.
- Permite generación narrativa a partir de eventos, prompts, fichas y acciones.

---

## 🤖 Agentes
Sistema modular de asistentes IA que cumplen funciones específicas dentro del Omniverso.

### 🎙️ `Narrador`
- Agente principal de generación de historia.
- Responde como director de juego, narrador omnisciente o escritor.
- Interpreta reglas del sistema YAML.

### 🧾 `Archivista`
- Controla línea de tiempo, fichas, y consistencia interna.
- Responde preguntas sobre el pasado narrativo.
- Ayuda a organizar eventos y relaciones.

### 🎭 `Personificador`
- Permite encarnar NPCs y simular interacciones conversacionales.
- Útil para roleo, escenas sociales o interrogatorios.

### ⚙️ `Asistente`
- Ayuda práctica para el usuario: cargar fichas, gestionar YAMLs, agendar sesiones, organizar escenas.
- Puede ayudarte a construir sistemas de rol o validar reglas.

---

## 🎲 Sistemas de Rol (Role Systems)
**Definición:** Conjuntos de reglas que controlan cómo se resuelven acciones, progresan personajes y se estructuran escenas.

- Declarados como archivos YAML.
- Tienen componentes como:
  - `stats`, `resources`, `tags`, `conditions`
  - `roll_mechanic`, `resolution_rules`, `progression_system`
- Asociables a multiversos, universos o historias específicas.

---

## 🧰 YAML de Sistema de Rol
Esquema formal que representa reglas de sistemas como PbtA, D&D 3.5, City of Mist, etc. 

- Definido en forma estructurada.
- Cargado automáticamente por el motor narrativo según la historia.
- Permite resolución de tiradas, checks, progresiones, condiciones y reglas especiales.

