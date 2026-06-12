"""
Funciones que construyen figuras Plotly para el dashboard.

Todas reciben DataFrames ya preparados y devuelven go.Figure con la paleta
de config.py aplicada. Ninguna toca disco ni Streamlit.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboard import config


def _tema(fig: go.Figure, titulo: str | None = None) -> go.Figure:
    fig.update_layout(**config.PLOTLY_LAYOUT)
    if titulo:
        fig.update_layout(title=titulo)
    return fig


# -- Explorador -----------------------------------------------------------------

def fig_sunburst_taxonomia(df: pd.DataFrame) -> go.Figure:
    """Sunburst N0 -> N1 -> bloque con volúmenes reales.

    df: columnas n0, n1, bloque, count.
    """
    fig = px.sunburst(
        df,
        path=["n0", "n1", "bloque"],
        values="count",
        color="n0",
        color_discrete_sequence=config.PALETA_AZULES,
        maxdepth=2,
    )
    fig.update_traces(textinfo="label+percent root", insidetextorientation="radial")
    fig.update_layout(height=560)
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


# -- Clasificador (página 3) -------------------------------------------------------

def fig_gauge_confianza(valor: float) -> go.Figure:
    """Gauge de confianza 0-1."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valor,
        number=dict(valueformat=".2f"),
        gauge=dict(
            axis=dict(range=[0, 1]),
            bar=dict(color=config.COLOR_PRIMARIO),
            steps=[
                dict(range=[0, 0.6], color="#fde2dc"),
                dict(range=[0.6, 0.8], color="#d8ecf3"),
                dict(range=[0.8, 1.0], color="#c4e6ef"),
            ],
        ),
    ))
    fig.update_layout(height=220, margin=dict(l=30, r=30, t=30, b=10))
    return _tema(fig)
