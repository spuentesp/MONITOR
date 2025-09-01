from pprint import pprint

from core.domain.evento import Evento
from core.domain.ficha import Ficha
from core.domain.historia import Historia
from core.domain.multiverso import Multiverso
from core.domain.omniverso import Omniverso
from core.domain.universo import Universo

# Crear ficha (una entidad en la historia)
ficha = Ficha(
    id="pj-001",
    nombre="Peter Parker",
    tipo="PJ",
    atributos={"fuerza": 12, "agilidad": 16},
    historia=[],
)

# Crear evento (vinculado a la historia y universo por ID)
evento = Evento(
    descripcion="Peter salva a un civil en Queens",
    tipo="narrativo",
    participantes=["pj-001"],
    universo_id="u-001",
    historia_id="h-001",
    orden=1,
)

# Crear historia
historia = Historia(
    id="h-001",
    titulo="El inicio del héroe",
    resumen="Peter comienza su camino como Spider-Man",
    eventos=[evento],
    fichas=[ficha],
)

# Crear universo
universo = Universo(
    id="u-001",
    nombre="Tierra-616",
    descripcion="Universo principal de Marvel",
    historias=[historia],
)

# Crear multiverso
multiverso = Multiverso(
    id="m-001",
    nombre="Marvel Multiverse",
    descripcion="Conjunto de universos relacionados a Marvel",
    universos=[universo],
)

# Crear omniverso
omniverso = Omniverso(id="omniverso-001", nombre="M.O.N.I.T.O.R.", multiversos=[multiverso])

# Mostrar resultado
print("=== Omniverso serializado ===")
pprint(omniverso.model_dump(mode="json"))
