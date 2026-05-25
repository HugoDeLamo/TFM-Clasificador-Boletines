"""
Schema de output del clasificador B1 - Hidrico y Natural.

Define el contrato entre el LLM y el sistema para el bloque hidrico/natural.
Pydantic AI valida cada respuesta automaticamente y reintenta si el schema falla.

Capas de la taxonomia B1:
    N0  Ambito geografico      -> derivado del campo 'bulletin' (lookup, sin LLM)
    N1  Tipo de acto           -> ActType, compartido con B0, inferido por reglas
    N2  Categoria hidrica      -> CategoryType, clasificado por el LLM
    N3  Subcategoria/cuenca    -> SubcategoryType, clasificado por el LLM
"""

from enum import Enum

from pydantic import BaseModel, Field, model_validator

# ActType es compartido entre todos los bloques - se reutiliza de B0
from clasificador.schema_B0 import ActType


# -- N2: Categorias hidricas y naturales ---------------------------------------
# Etiquetas multilabel: un registro puede pertenecer a mas de una categoria
# (ej. una concesion de aguas para riego en zona de Red Natura → AGU_RIE + ESP_NAT).
# Lista cerrada - añadir nuevos valores requiere re-anotar el ground truth.
class CategoryType(str, Enum):
    AGU_GEN = "AGU_GEN"  # Concesion de aguas - uso no especificado o generico
    AGU_RIE = "AGU_RIE"  # Concesion de aguas - riego y regadio
    AGU_SND = "AGU_SND"  # Sondeo / captacion puntual aguas subterraneas
    AGU_ABS = "AGU_ABS"  # Concesion de aguas - abastecimiento urbano
    AGU_IND = "AGU_IND"  # Concesion de aguas - uso industrial o energetico
    VIA_PEC = "VIA_PEC"  # Via pecuaria - ocupacion o modificacion
    MON     = "MON"      # Monte de utilidad publica / dominio forestal
    ESP_NAT = "ESP_NAT"  # Espacio natural protegido / Red Natura
    RES     = "RES"      # Gestion de residuos
    VER     = "VER"      # Vertidos de aguas
    PHD     = "PHD"      # Plan hidrologico de demarcacion


# -- N3: Subcategorias de uso y cuenca hidrica ---------------------------------
# Lista multilabel. Puede estar vacia aunque is_relevant=True
# (ej. una concesion generica sin uso o cuenca explicitos).
class SubcategoryType(str, Enum):
    # Uso del agua
    USO_AGRICOLA   = "uso_agricola"
    USO_URBANO     = "uso_urbano"
    USO_INDUSTRIAL = "uso_industrial"
    USO_ENERGETICO = "uso_energetico"
    USO_MIXTO      = "uso_mixto"
    # Cuenca hidrografica - inferir desde el organismo emisor mencionado en el texto
    CUENCA_GUADALQUIVIR = "cuenca_guadalquivir"
    CUENCA_DUERO        = "cuenca_duero"
    CUENCA_GUADIANA     = "cuenca_guadiana"
    CUENCA_EBRO         = "cuenca_ebro"
    CUENCA_TAJO         = "cuenca_tajo"
    CUENCA_JUCAR        = "cuenca_jucar"
    CUENCA_CANTABRICO   = "cuenca_cantabrico"
    CUENCA_MINO_SIL     = "cuenca_mino_sil"
    CUENCA_SEGURA       = "cuenca_segura"
    CUENCA_INSULAR      = "cuenca_insular"


# -- Output estructurado del clasificador B1 -----------------------------------
class ClassifierOutput(BaseModel):
    is_relevant: bool = Field(
        description=(
            "True si la publicacion pertenece al universo hidrico-natural monitorizado. "
            "False para oposiciones, contratos, subvenciones, obras de infraestructura "
            "sin relacion con agua o naturaleza, etc."
        )
    )
    act_type: ActType = Field(
        description=(
            "Tipo de acto administrativo (N1). Forma juridica del documento "
            "inferida del primer token o estructura de la descripcion."
        )
    )
    categories: list[CategoryType] = Field(
        description=(
            "Categorias identificadas (N2). Lista vacia si is_relevant=False. "
            "Multilabel: una concesion de riego en zona de Red Natura recibe [AGU_RIE, ESP_NAT]."
        )
    )
    subcategories: list[SubcategoryType] = Field(
        description=(
            "Subcategorias de uso del agua y cuenca hidrografica (N3). "
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
    def check_invariants(self) -> "ClassifierOutput":
        """
        Invariantes de negocio del schema B1:
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
