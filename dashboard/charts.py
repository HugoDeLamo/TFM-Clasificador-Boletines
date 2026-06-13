"""
Funciones que construyen figuras Plotly para el dashboard.

Todas reciben DataFrames ya preparados y devuelven go.Figure con la paleta
de config.py aplicada. Ninguna toca disco ni Streamlit.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboard import config, theme

# Pasar a st.plotly_chart(..., config=PLOTLY_CONFIG) en todas las vistas
PLOTLY_CONFIG = {"displayModeBar": False}


def _tema(fig: go.Figure, titulo: str | None = None) -> go.Figure:
    """Aplica fondo transparente (hereda la tarjeta), grid punteado y la paleta
    con los colores del modo activo (claro/oscuro)."""
    p = theme.paleta()
    fig.update_layout(
        font=dict(family="Source Sans 3, Source Sans Pro, sans-serif",
                  color=p["texto"]),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=config.PALETA_CATEGORICA,
        margin=dict(l=36, r=16, t=36, b=36),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, bgcolor="rgba(0,0,0,0)", borderwidth=0),
        hoverlabel=dict(font_family="Source Sans 3, sans-serif"),
    )
    fig.update_xaxes(gridcolor=p["grid"], griddash="dot", zeroline=False,
                     linecolor=p["grid"])
    fig.update_yaxes(gridcolor=p["grid"], griddash="dot", zeroline=False,
                     linecolor=p["grid"])
    if titulo:
        fig.update_layout(title=titulo)
    return fig


# -- Explorador -----------------------------------------------------------------

# Etiquetas legibles para el anillo de bloques: "B0 ambiental-energético" -> "B0"
_BLOQUE_A_ID = {
    "B0 ambiental-energético": "B0",
    "B1 hídrico-natural": "B1",
    "B2 urbanístico": "B2",
    "B3 subvenciones": "B3",
    "B4 contratación": "B4",
}


def _agregar_minoritarios(df: pd.DataFrame, col: str, padre_cols: list[str]) -> pd.DataFrame:
    """Agrupa en 'otros (n)' los valores de `col` que pesan menos de
    config.UMBRAL_OTROS_SUNBURST respecto a su padre."""
    df = df.copy()
    if padre_cols:
        total_padre = df.groupby(padre_cols)["count"].transform("sum")
    else:
        total_padre = df["count"].sum()
    share = df["count"] / total_padre
    minor = share < config.UMBRAL_OTROS_SUNBURST
    if minor.any():
        grupos = padre_cols if padre_cols else []
        n_minor = (
            df[minor].groupby(grupos)[col].transform("nunique")
            if grupos else df.loc[minor, col].nunique()
        )
        df.loc[minor, col] = (
            "otros (" + n_minor.astype(str) + ")" if grupos
            else f"otros ({n_minor})"
        )
        df = df.groupby(padre_cols + [col], as_index=False)["count"].sum() if padre_cols \
            else df.groupby([col], as_index=False)["count"].sum()
    return df


def fig_sunburst_taxonomia(df: pd.DataFrame) -> go.Figure:
    """Sunburst N0 -> N1 -> bloque, legible: minoritarios agrupados en gris,
    drill-down real (maxdepth=2), texto solo donde cabe y hover completo.

    df: columnas n0, n1, bloque, count.
    """
    total = df["count"].sum()

    # Agregacion de minoritarios nivel a nivel
    nivel2 = _agregar_minoritarios(
        df.groupby(["n0", "n1"], as_index=False)["count"].sum(), "n1", ["n0"]
    )
    # bloque dentro de (n0, n1): primero re-mapear n1 minoritarios igual que nivel2
    df3 = df.copy()
    mapa_n1 = {}
    for n0 in df["n0"].unique():
        originales = df[df["n0"] == n0].groupby("n1")["count"].sum()
        agrupados = set(nivel2[nivel2["n0"] == n0]["n1"])
        for n1 in originales.index:
            mapa_n1[(n0, n1)] = n1 if n1 in agrupados else next(
                a for a in agrupados if a.startswith("otros")
            )
    df3["n1"] = [mapa_n1[(a, b)] for a, b in zip(df3["n0"], df3["n1"])]
    nivel3 = _agregar_minoritarios(
        df3.groupby(["n0", "n1", "bloque"], as_index=False)["count"].sum(),
        "bloque", ["n0", "n1"],
    )

    # La jerarquia la construye plotly.express (consistencia garantizada de
    # branchvalues); despues se recolorean los sectores por sus ids.
    fig = px.sunburst(
        nivel3,
        path=["n0", "n1", "bloque"],
        values="count",
        maxdepth=2,
    )

    p = theme.paleta()
    # Anillo N0: verdes de marca (oscuro -> claro)
    verdes_n0 = {n0: config.PALETA_VERDES[i % len(config.PALETA_VERDES)]
                 for i, n0 in enumerate(sorted(df["n0"].unique()))}

    def _color_nodo(nid: str) -> str:
        partes = str(nid).split("/")
        hoja = partes[-1]
        if hoja.startswith("otros") or hoja == "sin bloque":
            return p["gris_otros"]
        if len(partes) == 1:  # anillo N0
            return verdes_n0.get(hoja, config.COLOR_PRIMARIO)
        if len(partes) == 2:  # anillo N1: verde lima medio
            return config.PALETA_VERDES[3]
        bloque_id = _BLOQUE_A_ID.get(hoja)  # anillo de bloques
        return config.COLORES_BLOQUE.get(bloque_id, p["gris_otros"])

    tr = fig.data[0]
    tr.marker.colors = [_color_nodo(i) for i in tr.ids]
    # Separadores del color de la tarjeta para que los gajos se distingan en
    # ambos modos (blanco en claro, oscuro en oscuro).
    tr.marker.line = dict(color=p["tarjeta"], width=1.5)
    fig.update_traces(
        textinfo="label+percent parent",
        insidetextorientation="radial",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "%{value:,.0f} publicaciones<br>"
            "%{percentParent:.1%} de su nivel superior<br>"
            "%{percentRoot:.1%} del total"
            "<extra></extra>"
        ),
    )
    fig.update_layout(
        height=560,
        uniformtext=dict(minsize=11, mode="hide"),
        margin=dict(l=8, r=8, t=8, b=8),
    )
    return _tema(fig)


def fig_barras_nivel(df: pd.DataFrame, nivel: str) -> go.Figure:
    """Panel companion del sunburst: desglose COMPLETO del nivel elegido
    (n0 / n1 / bloque), sin agrupar, ordenado por volumen.

    df: corpus de conteos con columnas n0, n1, bloque, count.
    """
    agg = df.groupby(nivel, as_index=False)["count"].sum().sort_values("count")
    if nivel == "bloque":
        gris = theme.paleta()["gris_otros"]
        colores = [
            config.COLORES_BLOQUE.get(_BLOQUE_A_ID.get(str(v), ""), gris)
            for v in agg[nivel]
        ]
    else:
        colores = [config.COLOR_PRIMARIO] * len(agg)
    fig = go.Figure(go.Bar(
        x=agg["count"], y=agg[nivel], orientation="h",
        marker_color=colores,
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} publicaciones<extra></extra>",
    ))
    fig.update_layout(
        height=560,
        xaxis_title="Publicaciones",
        yaxis_title="",
    )
    return _tema(fig)


def fig_mapa_ccaa(geojson: dict, df: pd.DataFrame, feature_key: str) -> go.Figure:
    """Coroplético de CCAA. df: columnas ccaa, count."""
    fig = px.choropleth(
        df,
        geojson=geojson,
        locations="ccaa",
        featureidkey=feature_key,
        color="count",
        color_continuous_scale=config.PALETA_SECUENCIAL,
        labels={"count": "Publicaciones"},
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(height=480, coloraxis_colorbar_title="Publicaciones")
    return _tema(fig)


def fig_barras_ccaa(df: pd.DataFrame) -> go.Figure:
    """Fallback del mapa: barras horizontales por CCAA (df: ccaa, count)."""
    df = df.sort_values("count")
    fig = px.bar(
        df, x="count", y="ccaa", orientation="h",
        color_discrete_sequence=[config.COLOR_PRIMARIO],
        labels={"count": "Publicaciones", "ccaa": ""},
    )
    fig.update_layout(height=480)
    return _tema(fig)


def fig_serie_temporal(df: pd.DataFrame, granularidad: str = "Día") -> go.Figure:
    """Serie temporal. df: columnas fecha (date), bulletin, count."""
    df = df.copy()
    df["fecha"] = pd.to_datetime(df["fecha"])
    if granularidad == "Semana":
        df["fecha"] = df["fecha"].dt.to_period("W").dt.start_time
    agg = df.groupby(["fecha", "bulletin"], as_index=False)["count"].sum()
    fig = px.line(
        agg, x="fecha", y="count", color="bulletin",
        color_discrete_sequence=config.PALETA_CATEGORICA,
        labels={"fecha": "", "count": "Publicaciones", "bulletin": "Boletín"},
    )
    fig.update_layout(height=420, hovermode="x unified")
    return _tema(fig)


def fig_boxplot_longitud(df: pd.DataFrame) -> go.Figure:
    """Boxplot horizontal de longitud por N1, ordenado por mediana, sin outliers.

    df: columnas n1, longitud (puede ser una muestra).
    """
    orden = (
        df.groupby("n1")["longitud"].median().sort_values(ascending=True).index.tolist()
    )
    fig = go.Figure()
    for n1 in orden:
        valores = df.loc[df["n1"] == n1, "longitud"]
        color = config.COLOR_DESTACADO if n1 == "otros" else config.COLOR_PRIMARIO
        fig.add_trace(go.Box(
            x=valores, name=n1, orientation="h",
            boxpoints=False, marker_color=color,
        ))
    fig.update_layout(
        height=620, showlegend=False,
        xaxis_title="Longitud de la descripción (caracteres)",
    )
    return _tema(fig)


# -- Resultados (página 4) --------------------------------------------------------

def fig_evolucion_metricas(df: pd.DataFrame) -> go.Figure:
    """Líneas de evolución. df: tabla de load_metricas_todos_experimentos.

    Qwen como serie principal; Gemma como punto aparte en coral.
    """
    qwen = df[df["Modelo"].str.contains("Qwen")]
    gemma = df[df["Modelo"].str.contains("Gemma")]
    fig = go.Figure()
    metricas = [
        ("Macro F1", config.PALETA_AZULES[0]),
        ("Micro F1", config.PALETA_AZULES[2]),
        ("F1 relevancia", config.COLOR_PRIMARIO),
    ]
    for met, color in metricas:
        fig.add_trace(go.Scatter(
            x=qwen["Experimento"], y=qwen[met], mode="lines+markers",
            name=f"{met} (Qwen)", line=dict(color=color, width=3),
            marker=dict(size=9),
        ))
    for met, _ in metricas:
        fig.add_trace(go.Scatter(
            x=gemma["Experimento"], y=gemma[met], mode="markers",
            name=f"{met} (Gemma)",
            marker=dict(size=14, color=config.COLOR_DESTACADO, symbol="diamond"),
            showlegend=(met == "Macro F1"),
        ))
    fig.update_layout(height=440, yaxis_title="F1", yaxis_range=[0.5, 1.02])
    return _tema(fig)


def fig_heatmap_f1(matriz: pd.DataFrame) -> go.Figure:
    """Heatmap F1 etiqueta x experimento. matriz: index=etiqueta, cols=experimento."""
    fig = px.imshow(
        matriz,
        text_auto=".3f",
        color_continuous_scale=config.PALETA_SECUENCIAL,
        zmin=0, zmax=1,
        aspect="auto",
        labels=dict(color="F1"),
    )
    fig.update_layout(height=460)
    return _tema(fig)


def fig_barras_comparacion(matriz: pd.DataFrame, exp_a: str, exp_b: str) -> go.Figure:
    """Barras agrupadas F1 por etiqueta para dos experimentos."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=matriz.index, y=matriz[exp_a], name=exp_a,
        marker_color=config.COLOR_PRIMARIO,
    ))
    fig.add_trace(go.Bar(
        x=matriz.index, y=matriz[exp_b], name=exp_b,
        marker_color=config.COLOR_DESTACADO,
    ))
    fig.update_layout(
        barmode="group", height=420,
        yaxis_title="F1 por etiqueta", yaxis_range=[0, 1.05],
    )
    return _tema(fig)


def fig_scatter_velocidad(df: pd.DataFrame) -> go.Figure:
    """Scatter s/ítem vs F1 relevancia, Gemma en coral."""
    df = df.copy()
    df["color"] = [
        config.COLOR_DESTACADO if "Gemma" in m else config.COLOR_PRIMARIO
        for m in df["Modelo"]
    ]
    fig = go.Figure(go.Scatter(
        x=df["s/ítem"], y=df["F1 relevancia"],
        mode="markers+text",
        text=df["Experimento"],
        textposition="top center",
        marker=dict(size=14, color=df["color"]),
    ))
    fig.update_layout(
        height=440,
        xaxis_title="Velocidad media (s/ítem)",
        yaxis_title="F1 relevancia",
    )
    return _tema(fig)
