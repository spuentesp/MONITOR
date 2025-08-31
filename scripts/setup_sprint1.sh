#!/bin/bash

# Crear la raíz del proyecto

# 1. Core
mkdir -p core/engine core/agents core/loaders core/domain core/interfaces

touch core/engine/narrative_engine.py
touch core/engine/event_handler.py

touch core/agents/base.py
touch core/agents/narrador.py
touch core/agents/archivista.py
touch core/agents/personificador.py

touch core/loaders/role_system_loader.py
touch core/loaders/history_loader.py
touch core/loaders/schema_validator.py

touch core/domain/omniverso.py
touch core/domain/multiverso.py
touch core/domain/universo.py
touch core/domain/historia.py

touch core/interfaces/cli_interface.py
touch core/interfaces/api_interface.py

# 2. Systems
mkdir -p systems
touch systems/pbta.yaml
touch systems/dnd35.yaml
touch systems/city_of_mist.yaml

# 3. Stories
mkdir -p stories/historia_1/fichas
touch stories/historia_1/config.yaml
touch stories/historia_1/eventos.log
touch stories/historia_1/fichas/peter.yaml
touch stories/historia_1/fichas/rogue.yaml

# 4. Memory (para el futuro)
mkdir -p memory/agents_memory memory/universe_notes
touch memory/timeline.json

# 5. Tests
mkdir -p tests
touch tests/test_engine.py
touch tests/test_agent_narrador.py
touch tests/test_yaml_loader.py

# 6. Scripts
mkdir -p scripts
touch scripts/run_example.py

# 7. Otros archivos raíz
touch requirements.txt
touch README.md

echo "✅ Proyecto 'MONITOR' inicializado con éxito."
