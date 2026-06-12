"""
Schema de output del clasificador B4 - Contratacion publica.

Define el contrato entre el LLM y el sistema para el bloque de contratacion publica.
Pydantic AI valida cada respuesta automaticamente y reintenta si el schema falla.

Capas de la taxonomia B4:
    N0  Ambito geografico       -> derivado del campo 'bulletin' (lookup, sin LLM)
    N1  Tipo de acto            -> ActType, compartido con B0-B3, inferido por reglas
    N2  Fase / tipo contractual -> CategoryTypeB4, clasificado por el LLM
    N3  Tipo de prestacion      -> SubcategoryTypeB4, clasificado por el LLM

Hallazgos empiricos del corpus Q1 2025 (~3.700 registros en el universo B4):
    - Sesgo BOE muy fuerte: ~59% de la contratacion esta en BOE (la autonomica
      y local publica en plataformas de contratacion, no en boletines).
    - CONT_FOR domina (~2.471), CONT_LIC ~972, CONT_ENC ~154, CONT_ADJ ~60,
      CONT_CON ~56.
    - CONT_CON es un TIPO de contrato, no una fase: se combina con la fase
      (licitacion de concesion de servicios -> [CONT_LIC, CONT_CON]).
    - Fronteras criticas: "se adjudica" casi siempre es RRHH (plazas, puestos,
      destinos, ~780 registros); "concesion administrativa/demanial" es dominio
      publico (aguas, puertos, vias pecuarias, ~226 registros), no contratacion.
"""

from enum import Enum

from pydantic import BaseModel, Field, model_validator

# ActType es compartido entre todos los bloques - se reutiliza de B0
from clasificador.schema_B0 import ActType


# -- N2: Fase del ciclo contractual y tipo concesional ---------------------------
# Etiquetas multilabel: CONT_CON marca el tipo concesional y se combina con la
# fase (CONT_LIC, CONT_FOR, CONT_ADJ). Lista cerrada.
class CategoryTypeB4(str, Enum):
    CONT_LIC = "CONT_LIC"  # Licitacion / anuncio de contrato / pliegos
    CONT_FOR = "CONT_FOR"  # Formalizacion de contrato
    CONT_ADJ = "CONT_ADJ"  # Adjudicacion de contrato (incluye desiertos)
    CONT_ENC = "CONT_ENC"  # Encargo a medio propio / encomienda de gestion
    CONT_CON = "CONT_CON"  # Concesion de servicios / obra publica (tipo contractual)


# -- N3: Tipo de prestacion del contrato -----------------------------------------
# Lista multilabel. Puede estar vacia aunque is_relevant=True (objeto no inferible).
class SubcategoryTypeB4(str, Enum):
    TIPO_OBRAS       = "tipo_obras"        # ejecucion de obras, construccion, reforma
    TIPO_SERVICIOS   = "tipo_servicios"    # servicios, mantenimiento, limpieza, vigilancia
    TIPO_SUMINISTROS = "tipo_suministros"  # suministro de bienes, equipamiento, energia


# -- Output estructurado del clasificador B4 -------------------------------------
class ClassifierOutputB4(BaseModel):
    is_relevant: bool = Field(
        description=(
            "True si la publicacion pertenece al universo de contratacion publica "
            "(LCSP): licitaciones, formalizaciones, adjudicaciones de contratos, "
            "encargos a medios propios y concesiones de servicios u obras. "
            "False para adjudicaciones de plazas o puestos de personal, concesiones "
            "de dominio publico, subvenciones, enajenaciones patrimoniales y subastas."
        )
    )
    act_type: ActType = Field(
        description=(
            "Tipo de acto administrativo (N1). Forma juridica del documento "
            "inferida del primer token o estructura de la descripcion."
        )
    )
    categories: list[CategoryTypeB4] = Field(
        description=(
            "Fases o tipos contractuales identificados (N2). Lista vacia si "
            "is_relevant=False. Multilabel: una licitacion de concesion de "
            "servicios recibe [CONT_LIC, CONT_CON]."
        )
    )
    subcategories: list[SubcategoryTypeB4] = Field(
        description=(
            "Tipo de prestacion del contrato (N3): obras, servicios o suministros. "
            "Puede ser lista vacia aunque is_relevant=True si el objeto no es "
            "inferible de la descripcion."
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
    def check_invariants(self) -> "ClassifierOutputB4":
        """
        Invariantes de negocio del schema B4:
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
