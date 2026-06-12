"""
Script OFFLINE de precalculo para el dashboard. Ejecutar UNA vez desde la
raiz del repo:

    uv run python -m dashboard.precompute

Genera en dashboard/cache/:
  - corpus_agregados.parquet  (n0, n1, longitud, fecha, bloque por registro)
  - serie_diaria.parquet      (conteos fecha x boletin)
  - sunburst_conteos.parquet  (conteos n0 x n1 x bloque)
  - spain_ccaa.geojson        (geojson de CCAA, descargado una vez)
  - ejemplos_cacheados.json   (resultados de la galeria para el modo sin API)

La app NUNCA clasifica el corpus completo en runtime.
"""

import html
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from dashboard import config  # noqa: E402
from clasificador.agent import get_ambito, inferir_act_type  # noqa: E402


def construir_corpus_agregados() -> pd.DataFrame:
    print("1/5 Corpus agregado (N0 + N1 + bloque sobre 65k filas, tarda unos minutos)...")
    df = pd.read_parquet(
        config.PATH_PARQUET,
        columns=["description", "bulletin", "publication_timestamp"],
    )
    df["description"] = df["description"].map(
        lambda x: html.unescape(str(x)) if pd.notna(x) else ""
    )
    df["bulletin"] = df["bulletin"].str.lower()
    df["n0"] = df["bulletin"].map(get_ambito)

    t0 = time.perf_counter()
    df["n1"] = [
        inferir_act_type(d, b).value
        for d, b in zip(df["description"], df["bulletin"])
    ]
    print(f"   N1 inferido en {time.perf_counter() - t0:.0f}s")

    df["longitud"] = df["description"].str.len()
    df["fecha"] = pd.to_datetime(df["publication_timestamp"]).dt.date

    # Bloque tematico por keyword matching (primer bloque que matchea)
    desc_lower = df["description"].str.lower()
    df["bloque"] = "sin bloque"
    sin_asignar = pd.Series(True, index=df.index)
    for bloque, kws in config.KEYWORDS_BLOQUES.items():
        mask = desc_lower.str.contains("|".join(kws), na=False, regex=True)
        df.loc[mask & sin_asignar, "bloque"] = bloque
        sin_asignar &= ~mask

    out = df[["description", "bulletin", "n0", "n1", "longitud", "fecha", "bloque"]]
    out.to_parquet(config.PATH_CORPUS_AGREGADOS, index=False)
    print(f"   -> {config.PATH_CORPUS_AGREGADOS} ({len(out):,} filas)")
    return out


def construir_agregados(df: pd.DataFrame) -> None:
    print("2/5 Serie diaria...")
    serie = df.groupby(["fecha", "bulletin"], as_index=False).size()
    serie.columns = ["fecha", "bulletin", "count"]
    serie.to_parquet(config.PATH_SERIE_DIARIA, index=False)
    print(f"   -> {config.PATH_SERIE_DIARIA}")

    print("3/5 Conteos del sunburst...")
    sb = df.groupby(["n0", "n1", "bloque"], as_index=False).size()
    sb.columns = ["n0", "n1", "bloque", "count"]
    sb.to_parquet(config.PATH_SUNBURST, index=False)
    print(f"   -> {config.PATH_SUNBURST}")


def descargar_geojson() -> None:
    print("4/5 Geojson de CCAA...")
    if config.PATH_GEOJSON_CCAA.exists():
        print("   ya existe, omitido")
        return
    try:
        with urllib.request.urlopen(config.GEOJSON_CCAA_URL, timeout=30) as r:
            datos = json.loads(r.read().decode("utf-8"))
        with open(config.PATH_GEOJSON_CCAA, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False)
        nombres = [f["properties"].get("name") for f in datos.get("features", [])]
        print(f"   -> {config.PATH_GEOJSON_CCAA} ({len(nombres)} CCAA: {nombres[:4]}...)")
    except Exception as e:  # sin conexion: la app degrada a bar chart
        print(f"   [AVISO] no se pudo descargar ({type(e).__name__}: {e}). "
              "El mapa degradara a barras.")


def construir_ejemplos_cacheados() -> None:
    """Resultados de la galeria. Si hay API key intenta clasificar en vivo;
    si no, construye el resultado desde el campo 'esperado' de config."""
    print("5/5 Ejemplos cacheados de la galeria...")
    hay_clave = bool(os.environ.get("GOOGLE_API_KEY") or os.environ.get("GROQ_API_KEY"))

    cache: dict[str, dict] = {}
    agentes_vivos = hay_clave
    if hay_clave:
        try:
            import importlib
            from pydantic_ai.models.fallback import FallbackModel
            from clasificador.agent import build_agent
        except ImportError:
            agentes_vivos = False

    for ej in config.GALERIA_EJEMPLOS:
        resultado = None
        if agentes_vivos:
            try:
                cfg = config.BLOQUES[ej["bloque"]]
                import importlib
                schema_mod = importlib.import_module(cfg["schema_modulo"])
                prompts_mod = importlib.import_module(cfg["prompts_modulo"])
                registry = getattr(prompts_mod, cfg["registry_attr"])
                version = cfg["version_defecto"] or sorted(
                    registry, key=lambda v: int(v.lstrip("v"))
                )[-1]
                modelos = [
                    m for m in config.CADENA_MODELOS
                    if (m.startswith("google-gla") and os.environ.get("GOOGLE_API_KEY"))
                    or (m.startswith("groq") and os.environ.get("GROQ_API_KEY"))
                ]
                from pydantic_ai.models.fallback import FallbackModel
                modelo = FallbackModel(*modelos) if len(modelos) > 1 else modelos[0]
                agente = build_agent(
                    modelo, version,
                    output_type=getattr(schema_mod, cfg["schema_clase"]),
                    prompt_registry=registry,
                )
                t0 = time.perf_counter()
                run = agente.run_sync(
                    f"Boletín: {ej['bulletin'].upper()}\n\nDescripción: {ej['description']}"
                )
                resultado = {
                    "output_dict": run.output.model_dump(mode="json"),
                    "modelo": getattr(run.response, "model_name", "online"),
                    "latencia_s": round(time.perf_counter() - t0, 2),
                    "origen": "clasificado en vivo durante el precalculo",
                }
                print(f"   {ej['id']}: clasificado en vivo")
            except Exception as e:
                print(f"   {ej['id']}: fallo en vivo ({type(e).__name__}), uso 'esperado'")
                resultado = None
        if resultado is None:
            resultado = {
                "output_dict": ej["esperado"],
                "modelo": "resultado precalculado (sin API)",
                "latencia_s": None,
                "origen": "construido desde el resultado esperado del ground truth",
            }
        cache[ej["id"]] = resultado

    with open(config.PATH_EJEMPLOS_CACHEADOS, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=1)
    print(f"   -> {config.PATH_EJEMPLOS_CACHEADOS} ({len(cache)} ejemplos)")


def main() -> None:
    config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    df = construir_corpus_agregados()
    construir_agregados(df)
    descargar_geojson()
    construir_ejemplos_cacheados()
    print("\nPrecálculo completo.")


if __name__ == "__main__":
    main()
