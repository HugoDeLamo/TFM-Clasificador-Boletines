"""
Schema de output del clasificador B2 - Urbanístico.

Define el contrato entre el LLM y el sistema para el bloque urbanístico.
Pydantic AI valida cada respuesta automaticamente y reintenta si el schema falla.

Capas de la taxonomia B2:
    N0  Ambito geografico      -> derivado del campo 'bulletin' (lookup, sin LLM)
    N1  Tipo de acto           -> ActType, compartido con B0/B1, inferido por reglas
    N2  Categoria urbanistica  -> CategoryTypeB2, clasificado por el LLM
    N3  Fase + uso del suelo   -> SubcategoryTypeB2, clasificado por el LLM
"""

from enum import Enum

from pydantic import BaseModel, Field, model_validator

# ActType es compartido entre todos los bloques - se reutiliza de B0
from clasificador.schema_B0 import ActType


# -- N2: Categorias urbanisticas -----------------------------------------------
# Etiquetas multilabel: un registro puede pertenecer a mas de una categoria
# (ej. plan especial en zona de especial interes → PLAN_ESP + DIC_INT).
# Lista cerrada - añadir nuevos valores requiere re-anotar el ground truth.
class CategoryTypeB2(str, Enum):
    PGOU     = "PGOU"      # Plan General de Ordenacion Urbana y equivalentes regionales
    PLAN_ESP = "PLAN_ESP"  # Plan Parcial / Plan Especial / Estudio de Detalle
    MOD_PUN  = "MOD_PUN"   # Modificacion puntual de planeamiento urbanistico
    PROY_URB = "PROY_URB"  # Proyecto de urbanizacion / reparcelacion / parcelacion
    LIC_URB  = "LIC_URB"   # Licencia urbanistica / autorizacion de uso excepcional
    DIC_INT  = "DIC_INT"   # Declaracion de interes comunitario / utilidad e interes social


# -- N3: Subcategorias de fase y uso del suelo ---------------------------------
# Lista multilabel. Puede estar vacia aunque is_relevant=True.
class SubcategoryTypeB2(str, Enum):
    # Fase del ciclo urbanistico
    FASE_AVANCE      = "fase_avance"
    FASE_IP          = "fase_ip"
    FASE_INICIAL     = "fase_inicial"
    FASE_PROVISIONAL = "fase_provisional"
    FASE_DEFINITIVA  = "fase_definitiva"
    FASE_CORRECCION  = "fase_correccion"
    # Uso del suelo
    USO_RESIDENCIAL  = "uso_residencial"
    USO_INDUSTRIAL   = "uso_industrial"
    USO_EQUIPAMIENTO = "uso_equipamiento"
    USO_RUSTICO      = "uso_rustico"
    USO_ENERGETICO   = "uso_energetico"
    USO_COMERCIAL    = "uso_comercial"


# -- Output estructurado del clasificador B2 -----------------------------------
class ClassifierOutputB2(BaseModel):
    is_relevant: bool = Field(
        description=(
            "True si la publicacion pertenece al universo urbanistico monitorizado. "
            "False para planes de estudios universitarios, planes de emergencia, "
            "planes estrategicos sin urbanismo, presupuestos, RRHH, contratos publicos."
        )
    )
    act_type: ActType = Field(
        description=(
            "Tipo de acto administrativo (N1). Forma juridica del documento "
            "inferida del primer token o estructura de la descripcion."
        )
    )
    categories: list[CategoryTypeB2] = Field(
        description=(
            "Categorias identificadas (N2). Lista vacia si is_relevant=False. "
            "Multilabel: un plan especial en suelo rustico puede recibir [PLAN_ESP, LIC_URB]."
        )
    )
    subcategories: list[SubcategoryTypeB2] = Field(
        description=(
            "Subcategorias de fase del ciclo urbanistico y uso del suelo (N3). "
            "Puede ser lista vacia aunque is_relevant=True si no hay informacion suficiente."
        )
    )
    confidence: float = Field(
        description=(
            "Confianza global en la clasificacion, entre 0.0 y 1.0. "
            "Guia de calibracion: "
            "0.95-1.0 → todas las categorias estan nombradas explicitamente en el texto; "
            "0.80-0.94 → al menos una categoria requiere inferencia o el texto es ambiguo; "
            "0.60-0.79 → descripcion generica sin terminos clave claros; "
            "< 0.60 → descripcion muy ambigua, multiples interpretaciones posibles."
        ),
        ge=0.0,
        le=1.0,
    )
    reasoning: str = Field(
        description=(
            "Justificacion breve. Citar el fragmento de texto que dispara cada "
            "etiqueta. Maximo 2 frases."
        )
    )

    @model_validator(mode="after")
    def check_invariants(self) -> "ClassifierOutputB2":
        """
        Invariantes de negocio del schema B2:
        - is_relevant=True  → categories no puede estar vacia
        - is_relevant=False → categories y subcategories deben estar vacias
        Si se viola alguna, Pydantic AI reintenta la llamada al LLM automaticamente.
        """
        if self.is_relevant and not self.categories:
            raise ValueError("is_relevant=True requiere categories != []")
        if not self.is_relevant:
            if self.categories:
                raise ValueError("is_relevant=False con categories != []")
            if self.subcategories:
                raise ValueError("is_relevant=False con subcategories != []")
        return self
