"""
Entrypoint del dashboard del TFM. Ejecutar desde la raiz del repo:

    uv run streamlit run dashboard/app.py
"""

import sys
from pathlib import Path

import streamlit as st

# Bootstrap de paths: el repo y src/ deben ser importables desde cualquier vista
REPO_ROOT = Path(__file__).resolve().parent.parent
for p in (str(REPO_ROOT), str(REPO_ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

st.set_page_config(
    page_title="Clasificador de Boletines Oficiales · TFM",
    page_icon="📋",
    layout="wide",
)

VIEWS = Path(__file__).parent / "views"

paginas = [
    st.Page(VIEWS / "portada.py", title="El proyecto", icon="🏠", default=True),
    st.Page(VIEWS / "explorador.py", title="Explorador del corpus", icon="🔍"),
    st.Page(VIEWS / "clasificador.py", title="Clasificador en vivo", icon="⚡"),
    st.Page(VIEWS / "resultados.py", title="Resultados experimentales", icon="📊"),
]

st.navigation(paginas).run()
