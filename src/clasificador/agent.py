"""
Agente y funciones de clasificación para el clasificador taxonómico de boletines oficiales.

Centraliza: pre-procesamiento N0/N1, construcción de agentes Pydantic AI,
clasificación asíncrona individual y ejecución de experimentos en batch.
"""

import asyncio
import json
import re
import time
from pathlib import Path

from pydantic_ai.exceptions import ModelHTTPError

import pandas as pd
from pydantic_ai import Agent
import tqdm

from clasificador.schema_B0 import ActType, ClassifierOutput
from clasificador.prompts_B0 import PROMPT_REGISTRY


# ── N0: ámbito administrativo por bulletin ────────────────────────────────────

_GAZETTE_TO_AMBITO: dict[str, str] = {
    "boe": "estatal",
    "madridambiental": "local",
    # resto → autonómico por defecto
}


def get_ambito(bulletin: str) -> str:
    return _GAZETTE_TO_AMBITO.get(bulletin.lower(), "autonómico")


# ── N1: tipo de acto por primer token ────────────────────────────────────────
# Cobertura medida: 89.6% del corpus (Q1 2025)
# El 10.4% restante cae en OTROS - ver DEC-010 y DEC-011

_N1_MAP: list[tuple[str, ActType]] = [
    (r"corrección de errat",     ActType.CORRECCION_ERRORES),
    (r"corrección de error",     ActType.CORRECCION_ERRORES),
    (r"rectificación",           ActType.CORRECCION_ERRORES),
    (r"real decreto",            ActType.REAL_DECRETO),
    (r"orden foral",             ActType.ORDEN),
    (r"información pública",     ActType.INFORMACION_PUBLICA),
    (r"exposición pública",      ActType.INFORMACION_PUBLICA),
    (r"trámite de información",  ActType.INFORMACION_PUBLICA),
    (r"trámite de audiencia",    ActType.INFORMACION_PUBLICA),
    (r"trámite de",              ActType.INFORMACION_PUBLICA),
    (r"resolución",              ActType.RESOLUCION),
    (r"anuncio",                 ActType.ANUNCIO),
    (r"orden",                   ActType.ORDEN),
    (r"decreto foral",           ActType.DECRETO),
    (r"decreto",                 ActType.DECRETO),
    (r"acuerdo",                 ActType.ACUERDO),
    (r"aprobación",              ActType.APROBACION),
    (r"extracto",                ActType.EXTRACTO),
    (r"convenio",                ActType.CONVENIO),
    (r"adenda",                  ActType.CONVENIO),
    (r"solicitud",               ActType.SOLICITUD),
    (r"modificación",            ActType.MODIFICACION),
    (r"edicto",                  ActType.EDICTO),
    (r"notificación",            ActType.NOTIFICACION),
    (r"notificaciones",          ActType.NOTIFICACION),
    (r"recaudación ejecutiva",   ActType.NOTIFICACION),
    (r"propuesta de resolución", ActType.RESOLUCION),
    (r"bases",                   ActType.CONVOCATORIA),
    (r"convocatoria",            ActType.CONVOCATORIA),
    (r"nombramiento",            ActType.RESOLUCION),
    (r"delegación",              ActType.RESOLUCION),
    (r"emplazamiento",           ActType.NOTIFICACION),
    (r"citación",                ActType.NOTIFICACION),
    (r"diligencia",              ActType.NOTIFICACION),
    (r"cédula",                  ActType.NOTIFICACION),
    (r"requerimiento",           ActType.NOTIFICACION),
    (r"concesión",               ActType.RESOLUCION),
    (r"iniciación",              ActType.RESOLUCION),
    (r"inicio",                  ActType.RESOLUCION),
    (r"apertura",                ActType.RESOLUCION),
    (r"informe",                 ActType.RESOLUCION),
    (r"expediente",              ActType.RESOLUCION),
    (r"recurso",                 ActType.RESOLUCION),
    (r"notaría",                 ActType.RESOLUCION),
    (r"publicación",             ActType.ANUNCIO),
    (r"plan",                    ActType.APROBACION),
    (r"departamento",            ActType.RESOLUCION),
    (r"ley",                     ActType.OTROS),
    (r"sala primera",            ActType.OTROS),
    (r"sala segunda",            ActType.OTROS),
    (r"__toponimo__",            ActType.OTROS),
    (r"__subasta_aeat__",        ActType.OTROS),
]


def preprocess_description(desc: str, bulletin: str) -> str:
    """
    Limpia la descripción antes de clasificar N1.

    Maneja tres formatos especiales:
    - BOCM: "Tema\\n– Tipo de acto..."
    - BOCA / BOIB: "Organisme.- Tipo de acto..."
    - BOE: topónimos en mayúsculas y subastas AEAT
    """
    desc = desc.strip()
    if "\n–" in desc:
        desc = desc.split("\n–", 1)[1].strip()
    elif "\n-" in desc:
        desc = desc.split("\n-", 1)[1].strip()
    if bulletin.lower() in ("boca", "boib") and ".-" in desc:
        desc = desc.split(".-", 1)[1].strip()
    if re.match(r"^[A-ZÁÉÍÓÚÜÑ/\s]+$", desc) and len(desc.split()) <= 4:
        return "__TOPONIMO__"
    if desc.upper().startswith(("U.R.", "E.R.", "SUMA GESTIÓN", "ORGANISMO AUTÓNOMO DE HACIENDA")):
        return "__SUBASTA_AEAT__"
    return desc


def inferir_act_type(description: str, bulletin: str) -> ActType:
    """Infiere el tipo de acto (N1) por reglas de primer token. Cobertura: ~89.6% Q1 2025."""
    text = preprocess_description(description, bulletin).lower().strip()
    for pattern, act_type in _N1_MAP:
        if text.startswith(pattern):
            return act_type
    return ActType.OTROS


# ── Agente ────────────────────────────────────────────────────────────────────

def build_agent(model, prompt_version: str = "v3", *, output_type=None, prompt_registry=None) -> Agent:
    """
    Construye un agente con el prompt indicado.

    Para el bloque B0 no es necesario pasar nada extra (usa defaults de B0).
    Para otros bloques (B1, B2...) pasar output_type y prompt_registry propios:
        build_agent(model, "v1", output_type=B1ClassifierOutput, prompt_registry=PROMPT_REGISTRY_B1)
    """
    registry = prompt_registry if prompt_registry is not None else PROMPT_REGISTRY
    ot       = output_type     if output_type     is not None else ClassifierOutput
    if prompt_version not in registry:
        raise ValueError(f"Versión desconocida: '{prompt_version}'. Opciones: {list(registry)}")
    return Agent(model, output_type=ot, system_prompt=registry[prompt_version])


# ── Clasificación ─────────────────────────────────────────────────────────────

def _build_user_message(description: str, bulletin: str, use_n1_context: bool) -> str:
    n0 = get_ambito(bulletin)
    msg = f"Boletín: {bulletin.upper()} (ámbito: {n0})\n\nDescripción: {description}"
    if use_n1_context:
        msg += f"\n\nTipo de acto pre-clasificado (N1): {inferir_act_type(description, bulletin).value}"
    return msg


async def clasificar_async(
    description: str,
    bulletin: str,
    agent: Agent,
    use_n1_context: bool = False,
) -> dict:
    result = await agent.run(_build_user_message(description, bulletin, use_n1_context))
    output = result.output
    # Serializar el output Pydantic de forma generica para soportar cualquier bloque (B0, B1...).
    # Campos escalares no-enum (bool, float, str) se guardan con su nombre original.
    # Enums y listas reciben el sufijo _pred y se serializan a string/JSON.
    row: dict = {}
    for field_name, value in output.model_dump().items():
        if field_name in ("confidence", "reasoning"):
            row[field_name] = value
        elif isinstance(value, list):
            row[f"{field_name}_pred"] = json.dumps(value, ensure_ascii=False)
        elif isinstance(value, bool):
            row[f"{field_name}_pred"] = value
        else:
            row[f"{field_name}_pred"] = value
    return row


async def run_experiment(
    agent: Agent,
    df_input: pd.DataFrame,
    use_n1_context: bool = False,
    concurrency: int = 1,
    output_path: str = "../results/experiment.csv",
    desc: str = "Clasificando",
) -> pd.DataFrame:
    """
    Ejecuta el agente sobre todos los registros del DataFrame.

    Soporta checkpoint: si el CSV ya existe, retoma desde la última fila guardada.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    done_descriptions: set[str] = set()
    existing_rows: list[dict] = []
    if Path(output_path).exists():
        df_existing = pd.read_csv(output_path)
        done_descriptions = set(df_existing["description"].tolist())
        existing_rows = df_existing.to_dict("records")
        print(f"  Reanudando: {len(done_descriptions)}/{len(df_input)} registros ya clasificados")

    df_pending = df_input[~df_input["description"].isin(done_descriptions)]

    semaphore = asyncio.Semaphore(concurrency)
    # write_lock protege las escrituras al CSV cuando concurrency > 1
    write_lock = asyncio.Lock()

    async def process_row(row, pbar):
        async with semaphore:
            t0 = time.perf_counter()
            try:
                pred = await clasificar_async(row["description"], row["bulletin"], agent, use_n1_context)
            except ModelHTTPError as e:
                if e.status_code == 400:
                    # Descripcion demasiado larga para la ventana de contexto del modelo
                    print(f"\n  [SKIP] context overflow en: {row['description'][:80]!r}")
                    pred = {"error": f"context_overflow: {e}"}
                else:
                    raise
            pred["duration_s"] = round(time.perf_counter() - t0, 3)
            result = {**row.to_dict(), **pred}
            # Guardar inmediatamente tras cada fila para sobrevivir cortes de conexion
            async with write_lock:
                pd.DataFrame([result]).to_csv(
                    output_path, mode="a", header=not Path(output_path).exists(), index=False
                )
            pbar.update(1)
            return result

    new_results: list[dict] = []
    if not df_pending.empty:
        t_start = time.perf_counter()
        # Escribir cabecera si el CSV no existe aun (primera ejecucion sin checkpoint)
        if not Path(output_path).exists() and not existing_rows:
            pd.DataFrame(columns=list(df_pending.iloc[0].to_dict()) + ["duration_s"]).to_csv(
                output_path, index=False
            )
        with tqdm.tqdm(total=len(df_pending), desc=desc) as pbar:
            tasks = [process_row(row, pbar) for _, row in df_pending.iterrows()]
            new_results = await asyncio.gather(*tasks)
        t_total = time.perf_counter() - t_start
        n = len(new_results)
        print(f"Tiempo: {t_total:.1f}s total  |  {t_total/n:.2f}s/item  |  {n} items")

    df_results = pd.read_csv(output_path)
    return df_results
