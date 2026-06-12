"""
Construccion de agentes Pydantic AI para la clasificacion en vivo.

Reutiliza build_agent() del paquete clasificador con el schema y el registro
de prompts de cada bloque (config.BLOQUES). La cadena de modelos online es un
FallbackModel; las claves se leen de st.secrets y se exportan a os.environ
ANTES de construir nada.
"""

import importlib
import os
import sys
import time

import streamlit as st

from dashboard import config

if str(config.REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(config.REPO_ROOT / "src"))

from clasificador.agent import build_agent  # noqa: E402

# Provider string -> variable de entorno que necesita
_PROVIDER_ENV = {
    "google-gla": "GOOGLE_API_KEY",
    "groq": "GROQ_API_KEY",
}


def _exportar_secrets() -> None:
    """Copia las claves de st.secrets a os.environ (si existen)."""
    for clave in ("GOOGLE_API_KEY", "GROQ_API_KEY"):
        try:
            valor = st.secrets.get(clave)
        except (FileNotFoundError, KeyError):
            valor = None
        if valor:
            os.environ[clave] = str(valor)


def proveedores_disponibles() -> list[str]:
    """Modelos de la cadena cuya clave de API esta disponible."""
    _exportar_secrets()
    disponibles = []
    for modelo in config.CADENA_MODELOS:
        provider = modelo.split(":", 1)[0]
        env_var = _PROVIDER_ENV.get(provider)
        if env_var and os.environ.get(env_var):
            disponibles.append(modelo)
    return disponibles


def hay_api_keys() -> bool:
    return len(proveedores_disponibles()) > 0


def _resolver_bloque(bloque_id: str):
    """Devuelve (output_type, prompt_registry) del bloque indicado."""
    cfg = config.BLOQUES[bloque_id]
    schema_mod = importlib.import_module(cfg["schema_modulo"])
    prompts_mod = importlib.import_module(cfg["prompts_modulo"])
    output_type = getattr(schema_mod, cfg["schema_clase"])
    registry = getattr(prompts_mod, cfg["registry_attr"])
    return output_type, registry


def versiones_de(bloque_id: str) -> list[str]:
    _, registry = _resolver_bloque(bloque_id)
    return sorted(registry.keys(), key=lambda v: int(v.lstrip("v")))


def version_por_defecto(bloque_id: str) -> str:
    cfg = config.BLOQUES[bloque_id]
    if cfg["version_defecto"]:
        return cfg["version_defecto"]
    return versiones_de(bloque_id)[-1]


@st.cache_resource(show_spinner=False)
def construir_agente(bloque_id: str, version: str):
    """Agente Pydantic AI del bloque con la cadena FallbackModel."""
    from pydantic_ai.models.fallback import FallbackModel

    _exportar_secrets()
    modelos = proveedores_disponibles()
    if not modelos:
        raise RuntimeError("No hay claves de API configuradas en st.secrets")
    modelo = FallbackModel(*modelos) if len(modelos) > 1 else modelos[0]
    output_type, registry = _resolver_bloque(bloque_id)
    return build_agent(
        modelo, version, output_type=output_type, prompt_registry=registry
    )


def clasificar(bloque_id: str, version: str, description: str, bulletin: str) -> dict:
    """Clasifica una descripcion. Devuelve dict con output, modelo y latencia.

    Lanza excepcion si la cadena entera de fallback falla (la vista decide
    como degradar).
    """
    agente = construir_agente(bloque_id, version)
    mensaje = f"Boletín: {bulletin.upper()}\n\nDescripción: {description}"
    t0 = time.perf_counter()
    resultado = agente.run_sync(mensaje)
    latencia = time.perf_counter() - t0

    modelo_usado = "desconocido"
    try:
        respuesta = resultado.response
        modelo_usado = getattr(respuesta, "model_name", None) or "desconocido"
    except Exception:
        pass

    return {
        "output": resultado.output,
        "output_dict": resultado.output.model_dump(mode="json"),
        "modelo": modelo_usado,
        "latencia_s": round(latencia, 2),
    }
