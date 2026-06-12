"""
Schema de output del clasificador B3 - Subvenciones.

Define el contrato entre el LLM y el sistema para el bloque de subvenciones y ayudas.
Pydantic AI valida cada respuesta automaticamente y reintenta si el schema falla.

Capas de la taxonomia B3:
    N0  Ambito geografico        -> derivado del campo 'bulletin' (lookup, sin LLM)
    N1  Tipo de acto             -> ActType, compartido con B0/B1/B2, inferido por reglas
    N2  Fase del ciclo de ayuda  -> CategoryTypeB3, clasificado por el LLM
    N3  Sector destinatario      -> SubcategoryTypeB3, clasificado por el LLM

Hallazgos empiricos del corpus Q1 2025 (~4.560 registros en el universo B3):
    - SUB_CONV ~2.263 (dominan los extractos BDNS), SUB_CON ~1.167,
      SUB_BASE ~1.429, SUB_REV ~10 (etiqueta muy minoritaria).
    - Multilabel frecuente: ~430 registros donde la misma orden aprueba las bases
      reguladoras Y convoca la ayuda -> [SUB_BASE, SUB_CONV].
    - ~273 registros con "bases reguladoras" son de bolsas de trabajo o procesos
      selectivos (empleo publico, futuro B5) -> is_relevant=False.
"""

from enum import Enum

from pydantic import BaseModel, Field, model_validator

# ActType es compartido entre todos los bloques - se reutiliza de B0
from clasificador.schema_B0 import ActType


# -- N2: Fase del ciclo de vida de la subvencion ---------------------------------
# Etiquetas multilabel: un registro puede pertenecer a mas de una categoria
# (ej. orden que aprueba bases y convoca → SUB_BASE + SUB_CONV).
# Lista cerrada - añadir nuevos valores requiere re-anotar el ground truth.
class CategoryTypeB3(str, Enum):
    SUB_CONV = "SUB_CONV"  # Convocatoria / extracto de convocatoria (BDNS)
    SUB_CON  = "SUB_CON"   # Concesion / resolucion de concesion de subvenciones o ayudas
    SUB_BASE = "SUB_BASE"  # Bases reguladoras de subvencion
    SUB_REV  = "SUB_REV"   # Reintegro / revocacion / perdida del derecho al cobro


# -- N3: Sector destinatario de la ayuda -----------------------------------------
# Lista multilabel. Puede estar vacia aunque is_relevant=True (sector no inferible).
# Los 10 sectores cubren ~83% del universo B3 segun keyword matching (Q1 2025).
class SubcategoryTypeB3(str, Enum):
    SECTOR_AGRICULTURA   = "sector_agricultura"    # agro, ganaderia, pesca, forestal, rural
    SECTOR_RENOVABLE     = "sector_renovable"      # renovables, autoconsumo, eficiencia energetica
    SECTOR_CULTURA       = "sector_cultura"        # cultura, artes, audiovisual, patrimonio
    SECTOR_VIVIENDA      = "sector_vivienda"       # vivienda, alquiler, rehabilitacion
    SECTOR_SOCIAL        = "sector_social"         # servicios sociales, inclusion, igualdad, juventud
    SECTOR_EDUCACION     = "sector_educacion"      # educacion, becas, universidad
    SECTOR_INDUSTRIA     = "sector_industria"      # industria, comercio, pymes, emprendimiento
    SECTOR_DEPORTE       = "sector_deporte"        # deporte y actividad fisica
    SECTOR_EMPLEO        = "sector_empleo"         # fomento del empleo y la contratacion
    SECTOR_INVESTIGACION = "sector_investigacion"  # I+D+i, investigacion, innovacion


# -- Output estructurado del clasificador B3 -------------------------------------
class ClassifierOutputB3(BaseModel):
    is_relevant: bool = Field(
        description=(
            "True si la publicacion pertenece al universo de subvenciones, ayudas, "
            "becas o premios con dotacion economica. False para procesos selectivos "
            "de personal, bolsas de trabajo, contratacion publica, presupuestos y "
            "convenios sin concesion de ayuda."
        )
    )
    act_type: ActType = Field(
        description=(
            "Tipo de acto administrativo (N1). Forma juridica del documento "
            "inferida del primer token o estructura de la descripcion."
        )
    )
    categories: list[CategoryTypeB3] = Field(
        description=(
            "Fases del ciclo de la subvencion identificadas (N2). Lista vacia si "
            "is_relevant=False. Multilabel: una orden que aprueba bases y convoca "
            "recibe [SUB_BASE, SUB_CONV]."
        )
    )
    subcategories: list[SubcategoryTypeB3] = Field(
        description=(
            "Sectores destinatarios de la ayuda (N3). Puede ser lista vacia aunque "
            "is_relevant=True si el sector no es inferible de la descripcion."
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
    def check_invariants(self) -> "ClassifierOutputB3":
        """
        Invariantes de negocio del schema B3:
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
