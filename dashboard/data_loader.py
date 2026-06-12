"""
Carga cacheada de datos para el dashboard.

Todo lo costoso se precalcula offline en precompute.py; aqui solo se leen
parquets/JSON de dashboard/cache/ y los CSVs de resultados (pequeños).
El parseo de etiquetas es tolerante: exp5 (Gemma) contiene una fila de error
con columnas desplazadas y valores no-JSON.
"""

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    hamming_loss,
    jaccard_score,
    precision_score,
    recall_score,
)
from sklearn.preprocessing import MultiLabelBinarizer

# El paquete clasificador vive en <repo>/src
from dashboard import config

if str(config.REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(config.REPO_ROOT / "src"))


# -- Parseo tolerante -----------------------------------------------------------

import re as _re

# Las etiquetas reales del proyecto son siempre [A-Za-z_] (DIA, AGU_GEN,
# sector_industria...). Cualquier token con digitos o puntuacion es basura
# de una fila corrupta (p.ej. '52.223' en exp5 por columnas desplazadas).
_PATRON_ETIQUETA = _re.compile(r"^[A-Za-zÀ-ÿ_]+$")


def parse_labels(value) -> list[str]:
    """Convierte cualquier representación de etiquetas a lista de strings.

    Acepta JSON list ('["AAU"]'), string separado por comas ('AAP,AAC') o
    basura (fila de error de Gemma, valores numéricos) -> lista vacía.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    s = str(value).strip()
    if s in ("", "nan", "None", "[]"):
        return []
    if s.startswith("["):
        try:
            items = json.loads(s)
            if isinstance(items, list):
                return [str(i).strip() for i in items if str(i).strip()]
            return []
        except (json.JSONDecodeError, TypeError):
            return []
    tokens = [x.strip().strip('"') for x in s.split(",") if x.strip()]
    return [t for t in tokens if _PATRON_ETIQUETA.match(t)]


def parse_bool(value) -> bool:
    """Booleano tolerante: maneja bool, 'True'/'False' string y basura -> False."""
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    return s == "true"


# -- Cargas cacheadas -----------------------------------------------------------

@st.cache_data(show_spinner="Cargando corpus agregado...")
def load_corpus_agregados() -> pd.DataFrame | None:
    """Corpus con n0/n1/longitud/fecha precalculados. None si falta el cache."""
    if not config.PATH_CORPUS_AGREGADOS.exists():
        return None
    return pd.read_parquet(config.PATH_CORPUS_AGREGADOS)


@st.cache_data
def load_serie_diaria() -> pd.DataFrame | None:
    if not config.PATH_SERIE_DIARIA.exists():
        return None
    return pd.read_parquet(config.PATH_SERIE_DIARIA)


@st.cache_data
def load_sunburst_conteos() -> pd.DataFrame | None:
    if not config.PATH_SUNBURST.exists():
        return None
    return pd.read_parquet(config.PATH_SUNBURST)


@st.cache_data
def load_geojson_ccaa() -> dict | None:
    if not config.PATH_GEOJSON_CCAA.exists():
        return None
    with open(config.PATH_GEOJSON_CCAA, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_ejemplos_cacheados() -> dict:
    if not config.PATH_EJEMPLOS_CACHEADOS.exists():
        return {}
    with open(config.PATH_EJEMPLOS_CACHEADOS, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_ground_truth_b0() -> pd.DataFrame:
    return pd.read_csv(config.PATH_GT_B0)


@st.cache_data
def load_experimento_b0(path: str) -> pd.DataFrame:
    """Carga un CSV de resultados B0 de forma tolerante a la fila de error."""
    df = pd.read_csv(path)
    df["is_relevant_pred"] = df["is_relevant_pred"].map(parse_bool)
    df["procedures_pred_list"] = df["procedures_pred"].map(parse_labels)
    df["technologies_pred_list"] = df.get(
        "technologies_pred", pd.Series([None] * len(df))
    ).map(parse_labels)
    df["duration_s"] = pd.to_numeric(df.get("duration_s"), errors="coerce")
    df["confidence"] = pd.to_numeric(df.get("confidence"), errors="coerce")
    return df


# -- Metricas B0 ------------------------------------------------------------------

def compute_metrics_b0(df_exp: pd.DataFrame, gt: pd.DataFrame) -> dict:
    """Métricas de un experimento B0 contra el GT (merge por description).

    Devuelve dict con métricas escalares + 'f1_por_etiqueta' (dict label->f1)
    + 'df_eval' (DataFrame alineado para el explorador de errores).
    """
    df_eval = gt[["id", "bulletin", "description", "is_relevant_gt", "procedures_gt"]].merge(
        df_exp[[
            "description", "is_relevant_pred", "procedures_pred_list",
            "confidence", "reasoning", "duration_s",
        ]],
        on="description", how="left",
    )
    labels = config.LABELS_B0
    mlb = MultiLabelBinarizer(classes=labels)
    mlb.fit([labels])

    gt_sets = [set(parse_labels(v)) & set(labels) for v in df_eval["procedures_gt"]]
    pred_sets = [
        set(v) & set(labels) if isinstance(v, list) else set()
        for v in df_eval["procedures_pred_list"]
    ]
    Y = mlb.transform(gt_sets)
    Yhat = mlb.transform(pred_sets)

    rel_gt = df_eval["is_relevant_gt"].map(parse_bool)
    rel_pred = df_eval["is_relevant_pred"].map(parse_bool)

    f1_por_etiqueta = dict(zip(labels, f1_score(Y, Yhat, average=None, zero_division=0)))

    df_eval["gt_set"] = [sorted(s) for s in gt_sets]
    df_eval["pred_set"] = [sorted(s) for s in pred_sets]
    df_eval["acierto_exacto"] = [
        g == p and rg == rp
        for g, p, rg, rp in zip(gt_sets, pred_sets, rel_gt, rel_pred)
    ]

    return {
        "is_rel_f1": round(f1_score(rel_gt, rel_pred, zero_division=0), 4),
        "is_rel_precision": round(precision_score(rel_gt, rel_pred, zero_division=0), 4),
        "is_rel_recall": round(recall_score(rel_gt, rel_pred, zero_division=0), 4),
        "micro_f1": round(f1_score(Y, Yhat, average="micro", zero_division=0), 4),
        "macro_f1": round(f1_score(Y, Yhat, average="macro", zero_division=0), 4),
        "hamming_loss": round(hamming_loss(Y, Yhat), 4),
        "jaccard_samples": round(jaccard_score(Y, Yhat, average="samples", zero_division=0), 4),
        "subset_accuracy": round(accuracy_score(Y, Yhat), 4),
        "duracion_media_s": round(float(df_eval["duration_s"].mean()), 2),
        "f1_por_etiqueta": f1_por_etiqueta,
        "df_eval": df_eval,
    }


@st.cache_data(show_spinner="Calculando métricas de los 6 experimentos...")
def load_metricas_todos_experimentos() -> pd.DataFrame:
    """Tabla con una fila por experimento B0 y sus métricas globales."""
    gt = load_ground_truth_b0()
    filas = []
    for nombre, modelo, cfg, path in config.EXPERIMENTOS_B0:
        df_exp = load_experimento_b0(str(path))
        m = compute_metrics_b0(df_exp, gt)
        filas.append({
            "Experimento": nombre,
            "Modelo": modelo,
            "Config": cfg,
            "F1 relevancia": m["is_rel_f1"],
            "Micro F1": m["micro_f1"],
            "Macro F1": m["macro_f1"],
            "Hamming": m["hamming_loss"],
            "Jaccard": m["jaccard_samples"],
            "Subset Acc": m["subset_accuracy"],
            "s/ítem": m["duracion_media_s"],
        })
    return pd.DataFrame(filas)
