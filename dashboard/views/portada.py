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

from dashboard import charts, config, data_loader  # noqa: F401

# -- Titulo y descripcion -------------------------------------------------------

st.title("Clasificación automática de publicaciones de boletines oficiales")
st.markdown(
    "Sistema de **clasificación multietiqueta** de publicaciones de boletines "
    "oficiales españoles mediante LLMs con **salida estructurada validada por "
    "esquema** (Pydantic AI)."
)

# -- Cifras clave ---------------------------------------------------------------

c1, c2, c3, c4 = st.columns(4)
c1.metric("Publicaciones", "65.201")
c2.metric("Fuentes", "19")
c3.metric("Bloques temáticos", "6 (B0–B5)")
c4.metric("Macro F1 (mejor configuración B0)", "0,975")

st.divider()

# -- Pipeline de 3 capas --------------------------------------------------------

st.subheader("Arquitectura del pipeline")


def _caja_capa(titulo: str, texto: str, color: str) -> str:
    """Tarjeta HTML de una capa del pipeline usando la paleta de config."""
    return f"""
    <div style="
        border: 2px solid {color};
        border-top: 8px solid {color};
        border-radius: 12px;
        background-color: {config.COLOR_FONDO};
        padding: 14px 16px;
        min-height: 215px;
    ">
        <div style="
            color: {color};
            font-weight: 700;
            font-size: 1.0rem;
            margin-bottom: 8px;
        ">{titulo}</div>
        <div style="
            color: {config.COLOR_TEXTO};
            font-size: 0.9rem;
            line-height: 1.45;
        ">{texto}</div>
    </div>
    """


_FLECHA = f"""
    <div style="
        text-align: center;
        font-size: 2.2rem;
        color: {config.COLOR_PRIMARIO};
        padding-top: 90px;
    ">→</div>
"""

CAPAS = [
    (
        "Capa 1 · Pre-procesamiento sin LLM",
        "N0 por <b>lookup del boletín</b> + N1 por <b>reglas léxicas de "
        "primer token</b> (89,6&nbsp;% de cobertura).",
        config.PALETA_AZULES[0],
    ),
    (
        "Capa 2 · Agente LLM con salida estructurada",
        "Esquema <b>Pydantic validado</b>, invariantes de negocio y "
        "<b>reintento automático</b> con el error de validación reinyectado.",
        config.PALETA_AZULES[1],
    ),
    (
        "Capa 3 · Evaluación",
        "Métricas <b>multietiqueta</b> sobre ground truth anotado "
        "(150 registros por bloque).",
        config.PALETA_AZULES[2],
    ),
]

col_c1, col_f1, col_c2, col_f2, col_c3 = st.columns([10, 1, 10, 1, 10])
for col, (titulo, texto, color) in zip((col_c1, col_c2, col_c3), CAPAS):
    col.markdown(_caja_capa(titulo, texto, color), unsafe_allow_html=True)
for col in (col_f1, col_f2):
    col.markdown(_FLECHA, unsafe_allow_html=True)

st.info(
    "Los experimentos de la memoria se ejecutaron con modelos locales "
    "(Qwen 3.5 9B, Gemma 4 4B vía LM Studio). Esta demo usa proveedores en "
    "línea gratuitos para mostrar que la arquitectura es agnóstica al "
    "proveedor."
)

st.divider()

# -- Bloques tematicos ----------------------------------------------------------

st.subheader("Bloques temáticos")

cols_bloques = st.columns(5)
for col, (clave, bloque), color in zip(
    cols_bloques,
    config.BLOQUES.items(),
    config.PALETA_CATEGORICA,
):
    col.markdown(
        f"""
        <div style="
            border: 1px solid {color};
            border-left: 6px solid {color};
            border-radius: 10px;
            background-color: {config.COLOR_FONDO};
            padding: 12px 14px;
            min-height: 170px;
        ">
            <div style="
                color: {color};
                font-weight: 700;
                font-size: 0.95rem;
                margin-bottom: 6px;
            ">{bloque["nombre"]}</div>
            <div style="
                color: {config.COLOR_TEXTO};
                font-size: 0.82rem;
                line-height: 1.4;
            ">{bloque["descripcion"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
