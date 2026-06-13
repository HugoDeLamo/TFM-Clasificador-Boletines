"""
Pagina "Explorador del corpus": taxonomia, geografia, evolucion temporal,
longitudes y buscador con salto al clasificador en vivo.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import math
import re
import unicodedata

import pandas as pd
import streamlit as st

from dashboard import config, data_loader, charts, theme

MSG_PRECOMPUTE = (
    "Ejecuta `uv run python -m dashboard.precompute` para generar los "
    "ficheros de cache."
)


def _aviso_cache(nombre: str) -> None:
    st.warning(f"Falta el fichero de cache de {nombre}. {MSG_PRECOMPUTE}")


def _fmt_miles(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _fmt_pct(valor: float) -> str:
    return f"{valor:.1f} %".replace(".", ",")


# -- Utilidades de matching de nombres de CCAA ---------------------------------

def _normalizar(texto: str) -> str:
    """Minusculas y sin acentos (NFKD sin marcas combinantes)."""
    sin_acentos = "".join(
        c for c in unicodedata.normalize("NFKD", str(texto))
        if not unicodedata.combining(c)
    )
    return sin_acentos.lower().strip()


_STOPWORDS = {
    "de", "del", "la", "las", "los", "y", "comunidad", "region",
    "islas", "illes", "principado", "foral", "autonoma",
}


def _tokens(texto: str) -> set[str]:
    return {
        t for t in re.split(r"[^a-z]+", _normalizar(texto))
        if t and t not in _STOPWORDS
    }


def construir_mapeo_ccaa(geojson: dict) -> tuple[str, dict[str, str]]:
    """Deducir el feature_key y mapear nombre de config -> nombre del geojson.

    Intenta en orden: igualdad normalizada, 'contains' en ambas direcciones y
    coincidencia de tokens sin stopwords. Los nombres sin match se descartan.
    """
    nombres_geo = [
        f.get("properties", {}).get("name", "")
        for f in geojson.get("features", [])
    ]
    mapeo: dict[str, str] = {}
    for nombre_cfg in set(config.BULLETIN_A_CCAA.values()):
        norm_cfg = _normalizar(nombre_cfg)
        elegido = None
        # 1) igualdad exacta tras normalizar
        for ng in nombres_geo:
            if _normalizar(ng) == norm_cfg:
                elegido = ng
                break
        # 2) contains en cualquier direccion (Valencia, Madrid, Murcia, Baleares)
        if elegido is None:
            for ng in nombres_geo:
                ngn = _normalizar(ng)
                if ngn and (ngn in norm_cfg or norm_cfg in ngn):
                    elegido = ng
                    break
        # 3) tokens sin stopwords (Castilla y Leon vs Castilla-Leon)
        if elegido is None:
            toks_cfg = _tokens(nombre_cfg)
            for ng in nombres_geo:
                toks_geo = _tokens(ng)
                if toks_geo and (toks_geo <= toks_cfg or toks_cfg <= toks_geo):
                    elegido = ng
                    break
        if elegido is not None:
            mapeo[nombre_cfg] = elegido
    return "properties.name", mapeo


# ===============================================================================

theme.inject_css()

corpus = data_loader.load_corpus_agregados()
serie = data_loader.load_serie_diaria()
sunburst = data_loader.load_sunburst_conteos()
geojson = data_loader.load_geojson_ccaa()

# -- Hero + tarjetas de resumen --------------------------------------------------

if corpus is not None:
    n_total = len(corpus)
    n_boletines = int(corpus["bulletin"].nunique())
    pct_bloque = 100.0 * float((corpus["bloque"] != "sin bloque").mean())
    pct_otros = 100.0 * float((corpus["n1"] == "otros").mean())
    subtitulo_hero = (
        f"{_fmt_miles(n_total)} publicaciones · Q1 2025 · "
        f"{n_boletines} boletines (BOE, 17 autonómicos y Madrid Ambiental)"
    )
else:
    subtitulo_hero = "65.201 publicaciones · Q1 2025 · 19 boletines"

theme.hero("Explorador del corpus", subtitulo_hero, "🔍")

if corpus is not None:
    theme.tarjetas_metricas(
        [
            (_fmt_miles(n_total), "Publicaciones"),
            (str(n_boletines), "Fuentes (18 oficiales + 1 local)"),
            (_fmt_pct(pct_bloque), "Con bloque temático"),
            (_fmt_pct(pct_otros), "N1 «otros»"),
        ]
    )

# -- 1. Taxonomia ---------------------------------------------------------------

theme.seccion("Taxonomía del corpus")
with st.container(border=True):
    if sunburst is None:
        _aviso_cache("conteos del sunburst")
    else:
        st.markdown(
            "El anillo interior es el **ámbito (N0)**, el siguiente el **tipo de "
            "acto (N1)** y al profundizar, el **bloque temático** (con su color "
            "identitario). Se muestran dos anillos a la vez: **haz clic en un "
            "sector para profundizar** y los gajos pequeños se agrupan en "
            "«otros (n)» gris; el detalle completo está siempre en el hover y "
            "en el panel de la derecha."
        )
        col_rueda, col_panel = st.columns([2, 1])
        with col_rueda:
            # El boton re-monta el chart (cicla la key) y resetea el drill-down
            st.session_state.setdefault("sunburst_reset", 0)
            if st.button("↺ Volver a la vista global", type="tertiary"):
                st.session_state["sunburst_reset"] += 1
            st.plotly_chart(
                charts.fig_sunburst_taxonomia(sunburst),
                key=f"sunburst_taxonomia_{st.session_state['sunburst_reset']}",
                config=charts.PLOTLY_CONFIG,
            )
        with col_panel:
            nivel = st.selectbox(
                "Desglose completo del nivel",
                ["n0", "n1", "bloque"],
                index=2,
                format_func={
                    "n0": "N0 · Ámbito",
                    "n1": "N1 · Tipo de acto",
                    "bloque": "Bloque temático",
                }.get,
                key="sunburst_nivel_panel",
            )
            st.plotly_chart(
                charts.fig_barras_nivel(sunburst, nivel),
                key="sunburst_panel_barras",
                config=charts.PLOTLY_CONFIG,
            )
        leyenda = " ".join(theme.badge_bloque(b) for b in config.BLOQUES)
        st.markdown(f"Bloques temáticos: {leyenda}", unsafe_allow_html=True)

# -- 2. Geografia -----------------------------------------------------------------

theme.seccion("Distribución geográfica")
with st.container(border=True):
    if corpus is None:
        _aviso_cache("corpus agregado")
    else:
        col_mapa, col_extra = st.columns(2)

        conteo_boletines = corpus["bulletin"].value_counts()
        df_ccaa = (
            conteo_boletines.rename_axis("bulletin")
            .reset_index(name="count")
            .assign(ccaa=lambda d: d["bulletin"].map(config.BULLETIN_A_CCAA))
            .dropna(subset=["ccaa"])
            .groupby("ccaa", as_index=False)["count"].sum()
        )

        with col_mapa:
            if geojson is None:
                st.warning(f"Falta el geojson de CCAA. {MSG_PRECOMPUTE}")
                st.plotly_chart(charts.fig_barras_ccaa(df_ccaa), key="barras_ccaa", config=charts.PLOTLY_CONFIG)
            else:
                feature_key, mapeo = construir_mapeo_ccaa(geojson)
                df_mapa = df_ccaa.assign(ccaa=df_ccaa["ccaa"].map(mapeo)).dropna(
                    subset=["ccaa"]
                )
                st.plotly_chart(
                    charts.fig_mapa_ccaa(geojson, df_mapa, feature_key),
                    key="mapa_ccaa",
                    config=charts.PLOTLY_CONFIG,
                )

        with col_extra:
            st.markdown("**Fuera del mapa autonómico**")
            m1, m2 = st.columns(2)
            m1.metric(
                config.NOMBRE_BOLETIN["boe"],
                _fmt_miles(int(conteo_boletines.get("boe", 0))),
            )
            m2.metric(
                config.NOMBRE_BOLETIN["madridambiental"],
                _fmt_miles(int(conteo_boletines.get("madridambiental", 0))),
            )
            st.caption(
                "El BOE es el boletín **estatal** y Madrid Ambiental es una fuente "
                "**local** (Ayuntamiento de Madrid): ninguno corresponde a una "
                "comunidad autónoma, por eso se muestran aparte del coroplético."
            )

# -- 3. Evolucion temporal ---------------------------------------------------------

theme.seccion("Evolución temporal")
with st.container(border=True):
    if serie is None:
        _aviso_cache("serie diaria")
    else:
        volumen = serie.groupby("bulletin")["count"].sum().sort_values(ascending=False)
        opciones = [str(b) for b in volumen.index]
        top6 = opciones[:6]

        col_gran, col_sel = st.columns([1, 3])
        with col_gran:
            granularidad = st.radio(
                "Granularidad", ["Día", "Semana"], horizontal=True, key="gran_serie"
            )
        with col_sel:
            seleccion = st.multiselect(
                "Boletines",
                options=opciones,
                default=top6,
                format_func=lambda b: config.NOMBRE_BOLETIN.get(b, b),
                key="boletines_serie",
            )

        if not seleccion:
            st.info("Selecciona al menos un boletín para ver la serie.")
        else:
            df_filtrado = serie[serie["bulletin"].isin(seleccion)]
            st.plotly_chart(
                charts.fig_serie_temporal(df_filtrado, granularidad),
                key="serie_temporal",
                config=charts.PLOTLY_CONFIG,
            )

# -- 4. Longitudes -------------------------------------------------------------------

theme.seccion("Longitud de las descripciones por tipo de acto")
with st.container(border=True):
    if corpus is None:
        _aviso_cache("corpus agregado")
    else:
        col_box, col_ej = st.columns([3, 2])

        with col_box:
            muestra = corpus.sample(
                n=min(20_000, len(corpus)), random_state=42
            )
            st.plotly_chart(
                charts.fig_boxplot_longitud(muestra[["n1", "longitud"]]),
                key="boxplot_longitud",
                config=charts.PLOTLY_CONFIG,
            )

        with col_ej:
            with st.expander("Ejemplos de descripciones cortas", expanded=True):
                cortas = corpus[corpus["longitud"] < 30].copy()
                es_mayus = cortas["description"].astype(str).str.isupper()
                toponimos = (
                    cortas.loc[es_mayus, "description"].drop_duplicates().head(3)
                )
                notificaciones = (
                    cortas.loc[~es_mayus, "description"].drop_duplicates().head(3)
                )

                if cortas.empty:
                    st.caption("No hay descripciones de menos de 30 caracteres.")
                else:
                    st.markdown("**Cabeceras topónimas en mayúsculas**")
                    for texto in toponimos:
                        st.code(texto, language=None)
                    st.warning(
                        "**Limitación documentada del corpus**: estas cabeceras "
                        "topónimas son solo el municipio de la sección del boletín; "
                        "el contenido real del acto es **irrecuperable sin el PDF** "
                        "original."
                    )
                    st.markdown("**Notificaciones y actos cortos**")
                    for texto in notificaciones:
                        st.code(texto, language=None)
                    st.caption(
                        "Edictos y notificaciones de una sola línea: clasificables, "
                        "pero con muy poca señal para el modelo."
                    )

# -- 5. Buscador -----------------------------------------------------------------------

theme.seccion("Buscador")
with st.container(border=True):
    if corpus is None:
        _aviso_cache("corpus agregado")
    else:
        consulta = st.text_input(
            "Búsqueda libre en las descripciones",
            placeholder="p. ej. autorización ambiental, fotovoltaica, PGOU...",
            key="busqueda_texto",
        )

        col_bol, col_fechas = st.columns(2)
        boletines_corpus = sorted(str(b) for b in corpus["bulletin"].dropna().unique())
        with col_bol:
            filtro_boletines = st.multiselect(
                "Boletines",
                options=boletines_corpus,
                format_func=lambda b: config.NOMBRE_BOLETIN.get(b, b),
                key="busqueda_boletines",
            )

        fechas = pd.to_datetime(pd.Series(corpus["fecha"]))
        fecha_min = fechas.min().date()
        fecha_max = fechas.max().date()
        with col_fechas:
            rango = st.date_input(
                "Rango de fechas",
                value=(fecha_min, fecha_max),
                min_value=fecha_min,
                max_value=fecha_max,
                key="busqueda_fechas",
            )

        resultados = corpus
        if consulta.strip():
            resultados = resultados[
                resultados["description"]
                .astype(str)
                .str.contains(consulta.strip(), case=False, regex=False, na=False)
            ]
        if filtro_boletines:
            resultados = resultados[resultados["bulletin"].isin(filtro_boletines)]
        if isinstance(rango, (tuple, list)) and len(rango) == 2:
            f_ini, f_fin = rango
            fechas_res = pd.to_datetime(pd.Series(resultados["fecha"])).dt.date
            resultados = resultados[
                ((fechas_res >= f_ini) & (fechas_res <= f_fin)).to_numpy()
            ]

        n_res = len(resultados)
        st.markdown(
            f"**{n_res:,}".replace(",", ".") + " coincidencias**"
        )

        if n_res == 0:
            st.info("Sin resultados. Prueba a relajar los filtros.")
        else:
            POR_PAGINA = 20
            total_paginas = max(1, math.ceil(n_res / POR_PAGINA))
            pagina = st.number_input(
                f"Página (de {total_paginas})",
                min_value=1,
                max_value=total_paginas,
                value=1,
                step=1,
                key="busqueda_pagina",
            )
            visibles = resultados.iloc[
                (pagina - 1) * POR_PAGINA : pagina * POR_PAGINA
            ]
            # st.table (no st.dataframe) para que herede el modo claro/oscuro
            tabla = visibles[["bulletin", "fecha", "description"]].rename(
                columns={"bulletin": "Boletín", "fecha": "Fecha", "description": "Descripción"}
            )
            st.table(tabla.style.hide(axis="index"))

            indices_visibles = list(visibles.index)
            elegida = st.selectbox(
                "Selecciona una publicación de esta página",
                options=indices_visibles,
                format_func=lambda i: str(visibles.loc[i, "description"])[:90],
                key="busqueda_fila",
            )
            if st.button("Clasificar esta publicación", type="primary"):
                st.session_state["clasificar_descripcion"] = str(
                    visibles.loc[elegida, "description"]
                )
                st.session_state["clasificar_bulletin"] = str(
                    visibles.loc[elegida, "bulletin"]
                )
                st.switch_page("views/clasificador.py")
