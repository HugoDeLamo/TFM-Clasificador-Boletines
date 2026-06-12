"""
Vista "Clasificador en vivo" (pagina estrella del dashboard).

Escenifica el pipeline jerarquico completo sobre una descripcion real:
N0 (ambito, lookup) -> N1 (tipo de acto, reglas) -> LLM (bloque tematico).
Sin claves de API funciona en modo demo sirviendo los resultados
precalculados de la galeria de ejemplos.
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import streamlit as st

from dashboard import config, data_loader, charts, llm
from clasificador.agent import (
    get_ambito,
    inferir_act_type,
    preprocess_description,
    _N1_MAP,
)

# Colores que la especificacion de esta vista fija explicitamente
# (badge de relevancia y chip de lista vacia); el resto sale de config.
_VERDE_RELEVANTE = config.COLOR_BADGE_RELEVANTE
_GRIS_CHIP = config.COLOR_CHIP_VACIO


# -- Helpers --------------------------------------------------------------------

def _chip(texto: str, color: str) -> str:
    return (
        f'<span style="background:{color};color:white;border-radius:12px;'
        f'padding:3px 12px;margin:4px;display:inline-block;'
        f'font-size:0.85rem;">{texto}</span>'
    )


def _resultado_cacheado(descripcion: str) -> dict | None:
    """Resultado precalculado si la descripcion coincide EXACTAMENTE con un ejemplo."""
    for ejemplo in config.GALERIA_EJEMPLOS:
        if ejemplo["description"] == descripcion:
            return data_loader.load_ejemplos_cacheados().get(ejemplo["id"])
    return None


def _render_resultado(resultado: dict) -> None:
    """Render 100% generico sobre output_dict: no se nombran campos de listas."""
    out = resultado.get("output_dict") or {}
    col_main, col_gauge = st.columns([3, 1])

    with col_main:
        # Badge de relevancia
        if "is_relevant" in out:
            if out["is_relevant"]:
                color, texto = _VERDE_RELEVANTE, "RELEVANTE"
            else:
                color, texto = config.COLOR_DESTACADO, "NO RELEVANTE"
            st.markdown(
                f'<div style="background:{color};color:white;padding:10px 22px;'
                f'border-radius:10px;display:inline-block;font-size:1.25rem;'
                f'font-weight:700;letter-spacing:1px;">{texto}</div>',
                unsafe_allow_html=True,
            )

        # Cada campo cuyo valor sea una lista -> chips (indice global de color)
        n_paleta = len(config.PALETA_CATEGORICA)
        chip_idx = 0
        for campo, valor in out.items():
            if not isinstance(valor, list):
                continue
            st.caption(campo)
            if valor:
                html = ""
                for v in valor:
                    html += _chip(str(v), config.PALETA_CATEGORICA[chip_idx % n_paleta])
                    chip_idx += 1
                st.markdown(html, unsafe_allow_html=True)
            else:
                st.markdown(_chip("-", _GRIS_CHIP), unsafe_allow_html=True)

        # act_type como chip individual (si existe)
        if out.get("act_type") is not None:
            st.caption("act_type")
            st.markdown(
                _chip(str(out["act_type"]), config.PALETA_CATEGORICA[chip_idx % n_paleta]),
                unsafe_allow_html=True,
            )

    with col_gauge:
        conf = out.get("confidence")
        if isinstance(conf, (int, float)):
            st.plotly_chart(charts.fig_gauge_confianza(float(conf)))

    if out.get("reasoning"):
        st.info(f"💬 {out['reasoning']}")

    # Pie discreto: modelo + latencia, o el origen del cache
    if resultado.get("latencia_s") is not None:
        st.caption(
            f"Modelo: {resultado.get('modelo', 'desconocido')} · "
            f"latencia: {resultado['latencia_s']} s"
        )
    else:
        partes = [
            str(resultado.get("modelo") or "").strip(),
            str(resultado.get("origen") or "").strip(),
        ]
        st.caption(" · ".join(p for p in partes if p))


# -- Cabecera --------------------------------------------------------------------

st.title("Clasificador en vivo")
st.caption(
    "Pipeline jerárquico completo sobre cualquier descripción de boletín oficial: "
    "N0 (ámbito, lookup) → N1 (tipo de acto, reglas de primer token) → "
    "LLM (clasificación multietiqueta del bloque temático con Pydantic AI)."
)

modo_demo = not llm.hay_api_keys()
if modo_demo:
    st.warning(
        "Modo demo sin clasificación en vivo: no hay claves de API en st.secrets. "
        "Los ejemplos de la galería devuelven su resultado precalculado."
    )
    if not data_loader.load_ejemplos_cacheados():
        st.warning(
            "Falta el cache de ejemplos precalculados (dashboard/cache/). "
            'Ejecuta "uv run python -m dashboard.precompute" para generarlo.'
        )

# -- Selector de bloque y version --------------------------------------------------

bloques_ids = list(config.BLOQUES.keys())
st.session_state.setdefault("clasificador_bloque", bloques_ids[0])

col_bloque, col_version = st.columns([3, 1])
with col_bloque:
    bloque = st.radio(
        "Bloque temático",
        bloques_ids,
        horizontal=True,
        format_func=lambda k: config.BLOQUES[k]["nombre"],
        key="clasificador_bloque",
    )
    st.caption(config.BLOQUES[bloque]["descripcion"])
with col_version:
    versiones = llm.versiones_de(bloque)
    defecto = llm.version_por_defecto(bloque)
    version = st.selectbox(
        "Versión del prompt",
        versiones,
        index=versiones.index(defecto),
        key=f"clasificador_version_{bloque}",
    )

# -- Galeria de ejemplos -----------------------------------------------------------

st.markdown("**Galería de ejemplos** (casos reales del ground truth)")

_TITULOS_EJEMPLOS = {e["id"]: e["titulo"] for e in config.GALERIA_EJEMPLOS}


def _aplicar_ejemplo() -> None:
    sel = st.session_state.get("clasificador_galeria")
    if not sel:
        return
    ejemplo = next(e for e in config.GALERIA_EJEMPLOS if e["id"] == sel)
    st.session_state["clasificar_descripcion"] = ejemplo["description"]
    st.session_state["clasificar_bulletin"] = ejemplo["bulletin"]
    st.session_state["clasificador_bloque"] = ejemplo["bloque"]
    st.session_state["ejemplo_activo"] = ejemplo["id"]


if hasattr(st, "pills"):
    st.pills(
        "Galería de ejemplos",
        options=list(_TITULOS_EJEMPLOS),
        format_func=_TITULOS_EJEMPLOS.get,
        selection_mode="single",
        key="clasificador_galeria",
        on_change=_aplicar_ejemplo,
        label_visibility="collapsed",
    )
else:  # fallback para versiones de Streamlit sin st.pills
    cols_galeria = st.columns(len(_TITULOS_EJEMPLOS))
    for col, (ej_id, titulo) in zip(cols_galeria, _TITULOS_EJEMPLOS.items()):
        def _seleccionar(ej_id: str = ej_id) -> None:
            st.session_state["clasificador_galeria"] = ej_id
            _aplicar_ejemplo()

        col.button(titulo, key=f"clasificador_btn_{ej_id}", on_click=_seleccionar)

# -- Formulario --------------------------------------------------------------------

st.session_state.setdefault("clasificar_descripcion", "")
st.session_state.setdefault("clasificar_bulletin", config.BOLETINES[0])

descripcion = st.text_area(
    "Descripción de la publicación",
    height=140,
    key="clasificar_descripcion",
    placeholder="Pega aquí el texto de una publicación o elige un ejemplo de la galería...",
)
col_boletin, col_boton = st.columns([2, 1], vertical_alignment="bottom")
with col_boletin:
    bulletin = st.selectbox(
        "Boletín de origen",
        config.BOLETINES,
        format_func=lambda b: config.NOMBRE_BOLETIN.get(b, b),
        key="clasificar_bulletin",
    )
with col_boton:
    clasificar_click = st.button("Clasificar", type="primary")

# -- Pipeline ----------------------------------------------------------------------

if clasificar_click:
    if not descripcion.strip():
        st.session_state["clasificador_resultado"] = None
        st.warning("Escribe o selecciona una descripción antes de clasificar.")
    else:
        resultado = None
        with st.status("Ejecutando pipeline...", expanded=True) as status:
            # Paso N0: ambito por lookup del boletin
            ambito = get_ambito(bulletin)
            st.write(f"**N0 · Ámbito**: {ambito} (lookup sin LLM)")
            time.sleep(0.4)

            # Paso N1: tipo de acto por reglas de primer token
            act = inferir_act_type(descripcion, bulletin)
            texto = preprocess_description(descripcion, bulletin).lower().strip()
            patron = next((p for p, _t in _N1_MAP if texto.startswith(p)), None)
            if patron is not None:
                st.write(
                    f'**N1 · Tipo de acto**: {act.value} '
                    f'(regla de primer token disparada: "{patron}")'
                )
            else:
                st.write(
                    f"**N1 · Tipo de acto**: {act.value} "
                    f"(ninguna regla coincide: cae en OTROS, como el 10,4 % del corpus)"
                )
            time.sleep(0.4)

            # Paso LLM: clasificacion del bloque tematico
            nombre_bloque = config.BLOQUES[bloque]["nombre"]
            if not modo_demo:
                st.write(
                    f"**LLM · {nombre_bloque}** (prompt {version}): "
                    "llamando a la cadena de modelos..."
                )
                try:
                    resultado = llm.clasificar(bloque, version, descripcion, bulletin)
                    st.write(
                        f"Respuesta de `{resultado['modelo']}` "
                        f"en {resultado['latencia_s']} s."
                    )
                    status.update(
                        label="Pipeline completado", state="complete", expanded=False
                    )
                except Exception as e:
                    resultado = _resultado_cacheado(descripcion)
                    if resultado is not None:
                        st.write(
                            "La llamada al LLM falló: se sirve el "
                            "**resultado precalculado** del ejemplo."
                        )
                        status.update(
                            label="Pipeline completado (resultado precalculado)",
                            state="complete",
                            expanded=False,
                        )
                    else:
                        st.error(f"Error al clasificar: {str(e)[:300]}")
                        status.update(label="Pipeline con errores", state="error")
            else:
                st.write(
                    f"**LLM · {nombre_bloque}**: modo demo, "
                    "buscando resultado precalculado..."
                )
                resultado = _resultado_cacheado(descripcion)
                if resultado is not None:
                    st.write(
                        "Encontrado el **resultado precalculado** "
                        "de este ejemplo de la galería."
                    )
                    status.update(
                        label="Pipeline completado (resultado precalculado)",
                        state="complete",
                        expanded=False,
                    )
                else:
                    st.error(
                        "Sin claves de API y sin resultado precalculado: la "
                        "descripción no coincide exactamente con ningún ejemplo "
                        "de la galería."
                    )
                    status.update(label="Pipeline sin resultado", state="error")
        st.session_state["clasificador_resultado"] = resultado

# -- Resultado (persiste entre reruns) ----------------------------------------------

resultado_actual = st.session_state.get("clasificador_resultado")
if resultado_actual:
    st.divider()
    st.subheader("Resultado de la clasificación")
    _render_resultado(resultado_actual)
