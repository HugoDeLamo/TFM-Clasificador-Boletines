from enum import Enum

from pydantic import BaseModel, Field, model_validator


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


class ProcedureType(str, Enum):
    DIA = "DIA"
    AAP = "AAP"
    AAC = "AAC"
    AAU = "AAU"
    IIA = "IIA"
    AAI = "AAI"
    IAE = "IAE"
    DUP = "DUP"


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
        description="Confianza global en la clasificación, entre 0.0 y 1.0.",
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
        if self.is_relevant and not self.procedures:
            raise ValueError("is_relevant=True requiere procedures != []")
        if not self.is_relevant:
            if self.procedures:
                raise ValueError("is_relevant=False con procedures != []")
            if self.technologies:
                raise ValueError("is_relevant=False con technologies != []")
        return self
