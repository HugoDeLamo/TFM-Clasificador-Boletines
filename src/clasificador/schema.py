"""
Schema de output del clasificador taxonómico de boletines oficiales españoles.

Define el contrato entre el LLM y el sistema: qué campos devuelve el modelo,
de qué tipo son y qué invariantes deben cumplirse. Pydantic AI valida cada
respuesta automáticamente y reintenta la llamada si el schema no se satisface.

Capas de la taxonomía:
    N0  Ámbito geográfico     → derivado del campo 'bulletin' (lookup, sin LLM)
    N1  Tipo de acto          → ActType, inferido por reglas de primer token
    N2  Procedimiento         → ProcedureType, clasificado por el LLM
    N3  Tecnología/sector     → TechnologyType, clasificado por el LLM
"""

from enum import Enum

from pydantic import BaseModel, Field, model_validator


# ── N1: Tipo de acto administrativo ──────────────────────────────────────────
# Forma jurídica del documento. Se infiere por reglas deterministas en agent.py
# (clasificador N1) antes de llamar al LLM, y el LLM lo confirma/corrige.
class ActType(str, Enum):
    RESOLUCION          = "resolución"
    ANUNCIO             = "anuncio"
    ORDEN               = "orden"
    DECRETO             = "decreto"
    ACUERDO             = "acuerdo"
    APROBACION          = "aprobación"
    CONVOCATORIA        = "convocatoria"
    INFORMACION_PUBLICA = "información_pública"
    CORRECCION_ERRORES  = "corrección_errores"
    NOTIFICACION        = "notificación"
    EXTRACTO            = "extracto"
    CONVENIO            = "convenio"
    SOLICITUD           = "solicitud"
    MODIFICACION        = "modificación"
    EDICTO              = "edicto"
    REAL_DECRETO        = "real_decreto"
    OTROS               = "otros"


# ── N2: Procedimientos ambientales/energéticos ────────────────────────────────
# Etiquetas multilabel: una publicación puede contener más de un procedimiento
# (ej. una resolución que otorga AAP y AAC simultáneamente).
# Lista cerrada — añadir nuevos valores requiere reentrenar y re-anotar.
class ProcedureType(str, Enum):
    DIA = "DIA"   # Declaración de Impacto Ambiental
    AAP = "AAP"   # Autorización Administrativa Previa
    AAC = "AAC"   # Autorización Administrativa de Construcción
    AAU = "AAU"   # Autorización Ambiental Unificada (equivalente regional a DIA)
    IIA = "IIA"   # Informe de Impacto Ambiental (evaluación simplificada)
    AAI = "AAI"   # Autorización Ambiental Integrada (régimen IPPC/IED)
    IAE = "IAE"   # Informe/Declaración Ambiental Estratégico (planes y programas)
    DUP = "DUP"   # Declaración de Utilidad Pública


# ── N3: Tecnologías y sectores ────────────────────────────────────────────────
# Lista multilabel. Puede estar vacía aunque is_relevant=True
# (ej. una AAI sobre una industria química sin tecnología energética explícita).
class TechnologyType(str, Enum):
    FOTOVOLTAICA     = "fotovoltaica"
    EOLICA           = "eólica"
    ALMACENAMIENTO   = "almacenamiento"
    HIBRIDACION      = "hibridación"
    HIDROELECTRICA   = "hidroeléctrica"
    BIOGAS_BIOMETANO = "biogás_biometano"
    BIOMASA          = "biomasa"
    HIDROGENO        = "hidrógeno"
    LINEA_ELECTRICA  = "línea_eléctrica"
    GAS_NATURAL      = "gas_natural"
    PETROLEO         = "petróleo"


# ── Output estructurado del clasificador ──────────────────────────────────────
# Pydantic AI serializa este modelo a JSON schema y lo envía al LLM como
# instrucción de formato. Cada campo incluye una descripción que el LLM lee
# como guía de relleno (equivalente a instrucciones inline en el prompt).
class ClassifierOutput(BaseModel):
    is_relevant: bool = Field(
        description=(
            "True si la publicación pertenece al universo ambiental-energético "
            "monitorizado. False para oposiciones, presupuestos, contratos, etc."
        )
    )
    act_type: ActType = Field(
        description=(
            "Tipo de acto administrativo (N1). Forma jurídica del documento "
            "inferida del primer token o estructura de la descripción."
        )
    )
    procedures: list[ProcedureType] = Field(
        description=(
            "Procedimientos identificados (N2). Lista vacía si is_relevant=False. "
            "Multilabel: una resolución puede otorgar AAP y AAC simultáneamente."
        )
    )
    technologies: list[TechnologyType] = Field(
        description=(
            "Tecnologías o sectores mencionados (N3). Puede ser lista vacía aunque "
            "is_relevant=True (ej. una AAP genérica sin tecnología explícita)."
        )
    )
    confidence: float = Field(
        description=(
            "Confianza global en la clasificación, entre 0.0 y 1.0. "
            "Guía de calibración: "
            "0.95-1.0 → todos los procedimientos están nombrados explícitamente en el texto; "
            "0.80-0.94 → al menos un procedimiento requiere inferencia o el texto es ambiguo; "
            "0.60-0.79 → descripción genérica sin términos clave claros, clasificación probable pero incierta; "
            "< 0.60 → descripción muy ambigua, múltiples interpretaciones posibles."
        ),
        ge=0.0,
        le=1.0,
    )
    reasoning: str = Field(
        description=(
            "Justificación breve. Citar el fragmento de texto que dispara cada "
            "etiqueta. Máximo 2 frases."
        )
    )

    @model_validator(mode="after")
    def check_invariants(self) -> "ClassifierOutput":
        """
        Fuerza las invariantes de negocio del schema:
        - is_relevant=True  → procedures no puede estar vacío
        - is_relevant=False → procedures y technologies deben estar vacíos
        Si se viola alguna, Pydantic AI reintenta la llamada al LLM automáticamente.
        """
        if self.is_relevant and not self.procedures:
            raise ValueError("is_relevant=True requiere procedures != []")
        if not self.is_relevant:
            if self.procedures:
                raise ValueError("is_relevant=False con procedures != []")
            if self.technologies:
                raise ValueError("is_relevant=False con technologies != []")
        return self
