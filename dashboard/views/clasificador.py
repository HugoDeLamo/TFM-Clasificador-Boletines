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

from dashboard import config, data_loader, charts, llm, theme  # noqa: F401

theme.inject_css()

from clasificador.agent import (
    get_ambito,
    inferir_act_type,
    preprocess_description,
    _N1_MAP,
)

# Chip placeholder para listas vacias; el resto de colores sale de config/theme.
_GRIS_CHIP = config.COLOR_CHIP_VACIO

# Retraso entre chips de la cascada de entrada (ms)
_CASCADA_MS = 80


# -- Helpers --------------------------------------------------------------------


def _resultado_cacheado(descripcion: str) -> dict | None:
    """Resultado precalculado si la descripcion coincide EXACTAMENTE con un ejemplo."""
    for ejemplo in config.GALERIA_EJEMPLOS:
        if ejemplo["description"] == descripcion:
            return data_loader.load_ejemplos_cacheados().get(ejemplo["id"])
    return None


def _es_caso_trampa(descripcion: str) -> bool:
    """True si es el caso trampa de la concesion demanial portuaria (easter egg)."""
    trampa = next(
        (e for e in config.GALERIA_EJEMPLOS if e["id"] == "b4_demanial"), None
    )
    return trampa is not None and descripcion == trampa["description"]


def _render_resultado(resultado: dict, color_bloque: str) -> None:
    """Render 100% generico sobre output_dict: no se nombran campos de listas."""
    out = resultado.get("output_dict") or {}

    # La tarjeta del resultado lleva el borde izquierdo del color del bloque
    st.markdown(
        f"<style>.st-key-resultado_card div[data-testid='stVerticalBlockBorderWrapper']"
        f"{{ border-left: 4px solid {color_bloque} !important; }}</style>",
        unsafe_allow_html=True,
    )
    with st.container(border=True, key="resultado_card"):
        col_main, col_conf = st.columns([3, 1])

        with col_main:
            # Badge de relevancia
            if "is_relevant" in out:
                theme.badge_relevancia(bool(out["is_relevant"]))

            # Cada campo cuyo valor sea una lista -> chips en cascada
            chip_idx = 0
            for campo, valor in out.items():
                if not isinstance(valor, list):
                    continue
                st.caption(campo)
                if valor:
                    html = ""
                    for v in valor:
                        html += theme.chip(
                            str(v), color_bloque, retraso_ms=chip_idx * _CASCADA_MS
                        )
                        chip_idx += 1
                    st.markdown(html, unsafe_allow_html=True)
                else:
                    st.markdown(
                        theme.chip("-", _GRIS_CHIP, retraso_ms=chip_idx * _CASCADA_MS),
                        unsafe_allow_html=True,
                    )
                    chip_idx += 1

            # act_type como chip individual (si existe)
            if out.get("act_type") is not None:
                st.caption("act_type")
                st.markdown(
                    theme.chip(
                        str(out["act_type"]), color_bloque,
                        retraso_ms=chip_idx * _CASCADA_MS,
                    ),
                    unsafe_allow_html=True,
                )

        with col_conf:
            conf = out.get("confidence")
            if isinstance(conf, (int, float)):
                theme.barra_confianza(float(conf), color_bloque)

        if out.get("reasoning"):
            st.info(out["reasoning"])

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

theme.hero(
    "Clasificador en vivo",
    "Pipeline jerárquico de 3 pasos sobre cualquier descripción de boletín oficial: "
    "N0 resuelve el ámbito por lookup, N1 deduce el tipo de acto con reglas de primer "
    "token y un LLM con Pydantic AI clasifica el bloque temático, con cadena de "
    "fallback entre modelos si el principal falla.",
    "⚡",
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

# -- Selector de bloque (tarjetas clicables) ----------------------------------------

theme.seccion("Bloque temático")

bloques_ids = list(config.BLOQUES.keys())
st.session_state.setdefault("clasificador_bloque", bloques_ids[0])
bloque = st.session_state["clasificador_bloque"]

cols_bloques = st.columns(len(bloques_ids))
for col, bid in zip(cols_bloques, bloques_ids):
    with col:
        st.markdown(
            theme.tarjeta_bloque_html(bid, activa=(bid == bloque)),
            unsafe_allow_html=True,
        )

        def _elegir_bloque(bid: str = bid) -> None:
            st.session_state["clasificador_bloque"] = bid

        st.button(
            "✓ Seleccionado" if bid == bloque else "Elegir",
            key=f"bloque_btn_{bid}",
            on_click=_elegir_bloque,
            use_container_width=True,
            type="primary" if bid == bloque else "secondary",
        )

col_desc, col_version = st.columns([3, 1])
with col_desc:
    st.caption(
        f"{config.ICONOS_BLOQUE.get(bloque, '')} "
        f"**{config.BLOQUES[bloque]['nombre']}** · "
        f"{config.BLOQUES[bloque]['descripcion']}"
    )
with col_version:
    versiones = llm.versiones_de(bloque)
    defecto = llm.version_por_defecto(bloque)
    version = st.selectbox(
        "Versión del prompt",
        versiones,
        index=versiones.index(defecto),
        key=f"clasificador_version_{bloque}",
    )

color_bloque = config.COLORES_BLOQUE[bloque]

# -- Galeria de ejemplos -----------------------------------------------------------

theme.seccion("Ejemplos de la galería")
st.caption(
    "Casos reales del ground truth: pulsa uno y se rellena el formulario. "
    "Al seleccionarlo, el bloque correspondiente se activa automáticamente."
)

# Etiqueta legible del ejemplo: nombre del bloque + título del caso
_ETIQUETA_EJEMPLO = {
    e["id"]: f'{config.BLOQUES[e["bloque"]]["nombre"]} — {e["titulo"]}'
    for e in config.GALERIA_EJEMPLOS
}


def _aplicar_ejemplo() -> None:
    sel = st.session_state.get("clasificador_galeria")
    if not sel:
        return
    ejemplo = next(e for e in config.GALERIA_EJEMPLOS if e["id"] == sel)
    st.session_state["clasificar_descripcion"] = ejemplo["description"]
    st.session_state["clasificar_bulletin"] = ejemplo["bulletin"]
    st.session_state["clasificador_bloque"] = ejemplo["bloque"]
    st.session_state["ejemplo_activo"] = ejemplo["id"]


st.selectbox(
    "Elige un ejemplo de la galería",
    options=[None, *_ETIQUETA_EJEMPLO],
    format_func=lambda k: "— Selecciona un caso —" if k is None else _ETIQUETA_EJEMPLO[k],
    key="clasificador_galeria",
    on_change=_aplicar_ejemplo,
    label_visibility="collapsed",
)

# -- Formulario --------------------------------------------------------------------

theme.seccion("Publicación")

st.session_state.setdefault("clasificar_descripcion", "")
st.session_state.setdefault("clasificar_bulletin", config.BOLETINES[0])

with st.container(border=True):
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
        clasificacion_en_vivo = False
        nombre_bloque = config.BLOQUES[bloque]["nombre"]
        with st.status("Ejecutando pipeline...", expanded=True) as status:
            # Las 3 tarjetas del flujo se van encendiendo segun avanza el pipeline
            pasos = [
                {"titulo": "N0 · Ámbito", "dato": "", "estado": "pendiente"},
                {"titulo": "N1 · Tipo de acto", "dato": "", "estado": "pendiente"},
                {"titulo": f"LLM · {nombre_bloque}", "dato": "", "estado": "pendiente"},
            ]
            flujo = st.empty()

            def _pintar_flujo() -> None:
                flujo.markdown(
                    theme.pipeline_html(pasos, color_bloque), unsafe_allow_html=True
                )

            # Paso N0: ambito por lookup del boletin
            pasos[0]["estado"] = "activo"
            _pintar_flujo()
            time.sleep(0.4)
            ambito = get_ambito(bulletin)
            pasos[0].update(dato=f"{ambito} (lookup sin LLM)", estado="completo")
            _pintar_flujo()

            # Paso N1: tipo de acto por reglas de primer token
            pasos[1]["estado"] = "activo"
            _pintar_flujo()
            time.sleep(0.4)
            act = inferir_act_type(descripcion, bulletin)
            texto = preprocess_description(descripcion, bulletin).lower().strip()
            patron = next((p for p, _t in _N1_MAP if texto.startswith(p)), None)
            if patron is not None:
                pasos[1].update(
                    dato=f'{act.value} · regla: "{patron}"', estado="completo"
                )
            else:
                pasos[1].update(
                    dato=f"{act.value} · sin regla (OTROS, 10,4 % del corpus)",
                    estado="completo",
                )
            _pintar_flujo()

            # Paso LLM: clasificacion del bloque tematico
            pasos[2]["estado"] = "activo"
            _pintar_flujo()
            esqueleto = st.empty()  # shimmer mientras se espera al modelo
            if not modo_demo:
                esqueleto.markdown(
                    '<div class="skeleton"></div>', unsafe_allow_html=True
                )
                try:
                    resultado = llm.clasificar(bloque, version, descripcion, bulletin)
                    clasificacion_en_vivo = True
                    pasos[2].update(
                        dato=f"{resultado['modelo']} · {resultado['latencia_s']} s",
                        estado="completo",
                    )
                    esqueleto.empty()
                    _pintar_flujo()
                    status.update(
                        label="Pipeline completado", state="complete", expanded=True
                    )
                except Exception as e:
                    esqueleto.empty()
                    resultado = _resultado_cacheado(descripcion)
                    if resultado is not None:
                        pasos[2].update(
                            dato="resultado precalculado (el LLM falló)",
                            estado="completo",
                        )
                        _pintar_flujo()
                        status.update(
                            label="Pipeline completado (resultado precalculado)",
                            state="complete",
                            expanded=True,
                        )
                    else:
                        st.error(f"Error al clasificar: {str(e)[:300]}")
                        status.update(label="Pipeline con errores", state="error")
            else:
                resultado = _resultado_cacheado(descripcion)
                if resultado is not None:
                    pasos[2].update(
                        dato="resultado precalculado (modo demo)", estado="completo"
                    )
                    _pintar_flujo()
                    status.update(
                        label="Pipeline completado (resultado precalculado)",
                        state="complete",
                        expanded=True,
                    )
                else:
                    st.error(
                        "Sin claves de API y sin resultado precalculado: la "
                        "descripción no coincide exactamente con ningún ejemplo "
                        "de la galería."
                    )
                    status.update(label="Pipeline sin resultado", state="error")

        if resultado is not None:
            # El resultado recuerda con que bloque se clasifico (color estable)
            resultado = {**resultado, "bloque": bloque}
            out = resultado.get("output_dict") or {}

            # Celebracion discreta en clasificaciones en vivo muy confiables
            conf = out.get("confidence")
            if (
                clasificacion_en_vivo
                and out.get("is_relevant")
                and isinstance(conf, (int, float))
                and conf > 0.9
            ):
                st.toast("Clasificación con confianza alta", icon="🎯")

            # Easter egg: detectar correctamente el caso trampa demanial
            if _es_caso_trampa(descripcion) and out.get("is_relevant") is False:
                st.balloons()

        st.session_state["clasificador_resultado"] = resultado

# -- Resultado (persiste entre reruns) ----------------------------------------------

resultado_actual = st.session_state.get("clasificador_resultado")
if resultado_actual:
    theme.seccion("Resultado de la clasificación")
    color_resultado = config.COLORES_BLOQUE.get(
        resultado_actual.get("bloque", bloque), color_bloque
    )
    _render_resultado(resultado_actual, color_resultado)
