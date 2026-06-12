"""
Vista "Resultados experimentales (B0)".

Tabla resumen con cifras de control verificadas, evolucion de metricas,
F1 por etiqueta (heatmap + comparador), velocidad frente a calidad y un
explorador de errores con el razonamiento del modelo.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import pandas as pd
import streamlit as st

from dashboard import config, data_loader, charts, theme

theme.inject_css()

# -- Guardas: ficheros necesarios ------------------------------------------------
faltantes = [
    str(path) for *_, path in config.EXPERIMENTOS_B0 if not path.exists()
]
if not config.PATH_GT_B0.exists():
    faltantes.append(str(config.PATH_GT_B0))

if faltantes:
    theme.hero(
        "Resultados experimentales · B0",
        "Experimentos sobre el bloque B0 · Ambiental-Energético, evaluados "
        "contra un ground truth de 100 registros anotados a mano.",
        "📊",
    )
    st.warning(
        "Faltan ficheros de datos necesarios para esta página:\n\n"
        + "\n".join(f"- `{f}`" for f in faltantes)
        + "\n\nEjecuta `uv run python -m dashboard.precompute` desde la raíz "
        "del repositorio y recarga la página."
    )
    st.stop()


# -- Métricas por experimento (UNA sola vez, reutilizadas en 1, 3 y 5) ------------
@st.cache_data(show_spinner="Evaluando experimentos contra el ground truth...")
def _metricas_por_experimento() -> dict:
    gt = data_loader.load_ground_truth_b0()
    return {
        nombre: data_loader.compute_metrics_b0(
            data_loader.load_experimento_b0(str(path)), gt
        )
        for nombre, _modelo, _cfg, path in config.EXPERIMENTOS_B0
    }


metricas = _metricas_por_experimento()
df_metricas = data_loader.load_metricas_todos_experimentos()
nombres_exp = [nombre for nombre, *_ in config.EXPERIMENTOS_B0]

# -- Hero + tarjetas resumen (valores calculados desde df_metricas) ----------------
_mejor_macro = df_metricas["Macro F1"].max()
_exp_mejor_macro = df_metricas.loc[df_metricas["Macro F1"].idxmax(), "Experimento"]
_mejor_f1_rel = df_metricas["F1 relevancia"].max()
_mas_rapido = df_metricas["s/ítem"].min()
_exp_mas_rapido = df_metricas.loc[df_metricas["s/ítem"].idxmin(), "Experimento"]
_n_exp = len(df_metricas)

theme.hero(
    "Resultados experimentales · B0",
    f"{_n_exp} experimentos sobre el bloque B0 · Ambiental-Energético, evaluados "
    "contra un ground truth de 100 registros anotados a mano. "
    f"Mejor Macro F1: {_mejor_macro:.3f}.",
    "📊",
)
st.markdown(
    f"Bloque evaluado: {theme.badge_bloque('B0')}", unsafe_allow_html=True
)
theme.tarjetas_metricas([
    ("🏆", f"{_mejor_macro:.3f}", f"Mejor Macro F1 · {_exp_mejor_macro}"),
    ("🎯", f"{_mejor_f1_rel:.3f}", "Mejor F1 relevancia"),
    ("⚡", f"{_mas_rapido:.2f} s", f"s/ítem · {_exp_mas_rapido}"),
    ("🧪", f"{_n_exp}", "Experimentos evaluados"),
])

# -- 1. Tabla resumen --------------------------------------------------------------
with st.container(border=True):
    theme.seccion("Tabla resumen de experimentos", "📋")

    COLS_MAX = ["F1 relevancia", "Micro F1", "Macro F1", "Jaccard", "Subset Acc"]
    COLS_MIN = ["Hamming", "s/ítem"]
    # Resaltado suave del mejor valor por columna: tinte azul y numero en
    # negrita del color primario (nada de celdas azul oscuro)
    _estilo_mejor = (
        "background-color: rgba(29,111,163,.12); "
        f"color: {config.COLOR_PRIMARIO}; font-weight: 700;"
    )

    styler = (
        df_metricas.style
        .highlight_max(subset=COLS_MAX, props=_estilo_mejor)
        .highlight_min(subset=COLS_MIN, props=_estilo_mejor)
        .format({c: "{:.3f}" for c in COLS_MAX + ["Hamming"]} | {"s/ítem": "{:.2f}"})
        .hide(axis="index")
    )
    # st.table (HTML real): la cabecera y el hover de filas los estiliza theme.py
    st.table(styler)

    # Cifras de control + verificación automática
    _partes = []
    for exp, esperados in config.CIFRAS_CONTROL.items():
        _partes.append(
            exp + ": " + " y ".join(f"{k} = {v:.3f}" for k, v in esperados.items())
        )
    st.caption("Cifras de control esperadas (notebooks de origen): " + " · ".join(_partes))

    TOLERANCIA = 0.0005
    discrepancias = []
    for exp, esperados in config.CIFRAS_CONTROL.items():
        for clave, esperado in esperados.items():
            calculado = metricas[exp][clave]
            if abs(calculado - esperado) > TOLERANCIA:
                discrepancias.append(
                    f"{exp} · {clave}: calculado {calculado:.4f} frente a "
                    f"esperado {esperado:.4f}"
                )
    if discrepancias:
        st.error(
            "Discrepancia en las cifras de control (¿parseo de CSVs incorrecto?):\n\n"
            + "\n".join(f"- {d}" for d in discrepancias)
        )
    else:
        theme.pill_exito("Cifras de control verificadas")

# -- 2. Evolución de las métricas ---------------------------------------------------
with st.container(border=True):
    theme.seccion("Evolución de las métricas", "📈")
    st.plotly_chart(charts.fig_evolucion_metricas(df_metricas), width="stretch", config=charts.PLOTLY_CONFIG)
    st.caption(
        "Las líneas siguen los experimentos con Qwen 3.5 9B; los rombos corales "
        "marcan a Gemma 4 4B como punto de comparación."
    )

# -- 3. F1 por etiqueta --------------------------------------------------------------
with st.container(border=True):
    theme.seccion("F1 por etiqueta", "🔥")
    matriz = pd.DataFrame(
        {nombre: metricas[nombre]["f1_por_etiqueta"] for nombre in nombres_exp}
    ).reindex(config.LABELS_B0)
    st.plotly_chart(charts.fig_heatmap_f1(matriz), width="stretch", config=charts.PLOTLY_CONFIG)

    theme.seccion("Comparar dos experimentos", "⚖️")
    col_a, col_b = st.columns(2)
    with col_a:
        exp_a = st.selectbox("Experimento A", nombres_exp, index=0)
    with col_b:
        exp_b = st.selectbox("Experimento B", nombres_exp, index=3)
    st.plotly_chart(charts.fig_barras_comparacion(matriz, exp_a, exp_b), width="stretch", config=charts.PLOTLY_CONFIG)

# -- 4. Velocidad frente a calidad ----------------------------------------------------
with st.container(border=True):
    theme.seccion("Velocidad frente a calidad", "⚡")
    st.plotly_chart(charts.fig_scatter_velocidad(df_metricas), width="stretch", config=charts.PLOTLY_CONFIG)

# -- 5. Explorador de errores ----------------------------------------------------------
with st.container(border=True):
    theme.seccion("Explorador de errores", "🕵️")
    exp_err = st.selectbox("Experimento", nombres_exp, index=0, key="exp_errores")
    df_eval = metricas[exp_err]["df_eval"]
    errores = df_eval[~df_eval["acierto_exacto"].astype(bool)].sort_values("id")

    st.metric("Errores (predicción ≠ ground truth)", f"{len(errores)} de {len(df_eval)}")

    if errores.empty:
        st.info("Este experimento no comete ningún error de acierto exacto.")
    else:
        tabla_errores = pd.DataFrame({
            "Descripción": errores["description"].values,
            "GT relevante": errores["is_relevant_gt"].map(data_loader.parse_bool).values,
            "GT etiquetas": [", ".join(s) for s in errores["gt_set"]],
            "Predicción relevante": errores["is_relevant_pred"].map(data_loader.parse_bool).values,
            "Predicción etiquetas": [", ".join(s) for s in errores["pred_set"]],
            "Razonamiento": errores["reasoning"].values,
        })
        st.dataframe(tabla_errores, width="stretch", hide_index=True)

    st.caption(
        "Los registros donde la predicción difiere del ground truth, con el "
        "razonamiento del modelo: material de análisis para la defensa."
    )
