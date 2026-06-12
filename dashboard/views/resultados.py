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

from dashboard import config, data_loader, charts

st.title("📊 Resultados experimentales (B0)")
st.markdown(
    "Seis experimentos sobre el bloque **B0 · Ambiental-Energético**, evaluados "
    "contra un ground truth de 100 registros anotados a mano."
)

# -- Guardas: ficheros necesarios ------------------------------------------------
faltantes = [
    str(path) for *_, path in config.EXPERIMENTOS_B0 if not path.exists()
]
if not config.PATH_GT_B0.exists():
    faltantes.append(str(config.PATH_GT_B0))

if faltantes:
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

# -- 1. Tabla resumen --------------------------------------------------------------
st.header("Tabla resumen de experimentos")

COLS_MAX = ["F1 relevancia", "Micro F1", "Macro F1", "Jaccard", "Subset Acc"]
COLS_MIN = ["Hamming", "s/ítem"]
_estilo_mejor = f"background-color: {config.COLOR_PRIMARIO}; color: white;"

styler = (
    df_metricas.style
    .highlight_max(subset=COLS_MAX, props=_estilo_mejor)
    .highlight_min(subset=COLS_MIN, props=_estilo_mejor)
    .format({c: "{:.3f}" for c in COLS_MAX + ["Hamming"]} | {"s/ítem": "{:.2f}"})
)
st.dataframe(styler, width="stretch", hide_index=True)

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
    st.success("Cifras de control verificadas ✓")

# -- 2. Evolución de las métricas ---------------------------------------------------
st.header("Evolución de las métricas")
st.plotly_chart(charts.fig_evolucion_metricas(df_metricas), width="stretch")
st.caption(
    "Las líneas siguen los experimentos con Qwen 3.5 9B; los rombos corales "
    "marcan a Gemma 4 4B como punto de comparación."
)

# -- 3. F1 por etiqueta --------------------------------------------------------------
st.header("F1 por etiqueta")
matriz = pd.DataFrame(
    {nombre: metricas[nombre]["f1_por_etiqueta"] for nombre in nombres_exp}
).reindex(config.LABELS_B0)
st.plotly_chart(charts.fig_heatmap_f1(matriz), width="stretch")

st.subheader("Comparar dos experimentos")
col_a, col_b = st.columns(2)
with col_a:
    exp_a = st.selectbox("Experimento A", nombres_exp, index=0)
with col_b:
    exp_b = st.selectbox("Experimento B", nombres_exp, index=3)
st.plotly_chart(charts.fig_barras_comparacion(matriz, exp_a, exp_b), width="stretch")

# -- 4. Velocidad frente a calidad ----------------------------------------------------
st.header("Velocidad frente a calidad")
st.plotly_chart(charts.fig_scatter_velocidad(df_metricas), width="stretch")

# -- 5. Explorador de errores ----------------------------------------------------------
st.header("Explorador de errores")
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
