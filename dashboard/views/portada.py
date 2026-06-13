"""
Vista "El proyecto" (portada del dashboard).

Presenta el titulo del TFM, las cifras clave del corpus, el diagrama del
pipeline de 3 capas y las tarjetas de los bloques tematicos. Es una vista
estatica: no depende de los ficheros de cache.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import streamlit as st

from dashboard import charts, config, data_loader, theme  # noqa: F401

theme.inject_css()

# -- Hero -------------------------------------------------------------------------

theme.hero(
    "Clasificación automática de publicaciones de boletines oficiales",
    "Sistema de <b>clasificación multietiqueta</b> de publicaciones de boletines "
    "oficiales españoles mediante LLMs con <b>salida estructurada validada por "
    "esquema</b> (Pydantic AI).",
    "🌿",
)

# -- Cifras clave ---------------------------------------------------------------

theme.tarjetas_metricas(
    [
        ("65.201", "Publicaciones"),
        ("19", "Fuentes (18 oficiales + 1 local)"),
        ("5", "Bloques temáticos (B0–B4)"),
        ("0,975", "Macro F1 · mejor configuración B0"),
    ]
)
st.caption(
    "Fuentes: 18 boletines oficiales (BOE estatal + 17 autonómicos) y 2 locales "
    "(Madrid Ambiental y AAU). En el corpus de Q1 2025 aparecen 19, ya que AAU "
    "no tiene publicaciones en este periodo."
)

# -- Pipeline de 3 capas --------------------------------------------------------

theme.seccion("Arquitectura del pipeline")


_TEXTO = theme.paleta()["texto"]


def _tarjeta_capa(titulo: str, texto: str, color: str) -> str:
    """Tarjeta HTML de una capa del pipeline con el estilo .tarjeta del CSS global."""
    return (
        f'<div class="tarjeta" style="--acento:{color}">'
        f'<div style="color:{color}; font-family:\'Sora\',sans-serif; '
        f'font-weight:700; font-size:1rem; margin:0 0 .45rem;">{titulo}</div>'
        f'<div style="color:{_TEXTO}; font-size:.9rem; '
        f'line-height:1.5;">{texto}</div>'
        f"</div>"
    )


_FLECHA = (
    f'<div style="align-self:center; flex:0 0 auto; font-size:2.6rem; '
    f'font-weight:800; color:{config.COLOR_PRIMARIO};">&#8594;</div>'
)

CAPAS = [
    (
        "Capa 1 · Pre-procesamiento sin LLM",
        "N0 por <b>lookup del boletín</b> + N1 por <b>reglas léxicas de "
        "primer token</b> (89,6&nbsp;% de cobertura).",
    ),
    (
        "Capa 2 · Agente LLM con salida estructurada",
        "Esquema <b>Pydantic validado</b>, invariantes de negocio y "
        "<b>reintento automático</b> con el error de validación reinyectado.",
    ),
    (
        "Capa 3 · Evaluación",
        "Métricas <b>multietiqueta</b> sobre ground truth anotado "
        "(de 100 a 150 registros por bloque).",
    ),
]

_piezas_pipeline = []
for i, (titulo, texto) in enumerate(CAPAS):
    if i:
        _piezas_pipeline.append(_FLECHA)
    color = config.PALETA_VERDES[i % len(config.PALETA_VERDES)]
    _piezas_pipeline.append(_tarjeta_capa(titulo, texto, color))

st.markdown(
    f'<div class="fila-tarjetas">{"".join(_piezas_pipeline)}</div>',
    unsafe_allow_html=True,
)

st.info(
    "Los experimentos de la memoria se ejecutaron con modelos locales "
    "(Qwen 3.5 9B, Gemma 4 4B vía LM Studio). Esta demo usa proveedores en "
    "línea gratuitos para mostrar que la arquitectura es agnóstica al "
    "proveedor."
)

# -- Bloques tematicos ----------------------------------------------------------

theme.seccion("Bloques temáticos")

_piezas_bloques = []
for clave, bloque in config.BLOQUES.items():
    # Cada bloque con su color identitario (el mismo en TODA la app)
    color = config.COLORES_BLOQUE[clave]
    emoji = config.ICONOS_BLOQUE.get(clave, "🧩")
    _piezas_bloques.append(
        f'<div class="tarjeta" style="--acento:{color}">'
        f'<div class="icono">{emoji}</div>'
        f'<div style="color:{color}; font-family:\'Sora\',sans-serif; '
        f'font-weight:700; font-size:.95rem; margin:.3rem 0 .4rem;">'
        f'{bloque["nombre"]}</div>'
        f'<div style="color:{_TEXTO}; font-size:.82rem; '
        f'line-height:1.45;">{bloque["descripcion"]}</div>'
        f"</div>"
    )

st.markdown(
    f'<div class="fila-tarjetas">{"".join(_piezas_bloques)}</div>',
    unsafe_allow_html=True,
)
