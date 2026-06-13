"""
Configuracion central del dashboard del TFM.

Unico lugar donde viven rutas, paleta de colores, mapeos de boletines y la
definicion de bloques tematicos y ejemplos de la galeria. Ningun otro modulo
debe hardcodear paths ni colores.
"""

from pathlib import Path

# -- Rutas --------------------------------------------------------------------
# El dashboard vive en <repo>/dashboard/; el repo es su padre.
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
RESULTS_DIR = REPO_ROOT / "results"
CACHE_DIR = REPO_ROOT / "dashboard" / "cache"

PATH_PARQUET = DATA_DIR / "raw" / "silver_official_gazettes_2025_Q1.parquet"
PATH_GT_B0 = DATA_DIR / "ground_truth" / "ground_truth_100_anotado.csv"

PATH_CORPUS_AGREGADOS = CACHE_DIR / "corpus_agregados.parquet"
PATH_SERIE_DIARIA = CACHE_DIR / "serie_diaria.parquet"
PATH_SUNBURST = CACHE_DIR / "sunburst_conteos.parquet"
PATH_EJEMPLOS_CACHEADOS = CACHE_DIR / "ejemplos_cacheados.json"
PATH_GEOJSON_CCAA = CACHE_DIR / "spain_ccaa.geojson"

# Experimentos B0 para la pagina de resultados (nombre, config, csv, modelo)
EXPERIMENTOS_B0 = [
    ("Exp 1 · Baseline",   "Qwen 3.5 9B", "Zero-shot V1",  RESULTS_DIR / "exp1_baseline_qwen9b.csv"),
    ("Exp 2 · Prompt V2",  "Qwen 3.5 9B", "Zero-shot V2",  RESULTS_DIR / "exp2_promptv2_qwen9b.csv"),
    ("Exp 3 · V2 + N1",    "Qwen 3.5 9B", "V2 + ctx N1",   RESULTS_DIR / "exp3_promptv2_n1_qwen9b.csv"),
    ("Exp 4 · Few-shot",   "Qwen 3.5 9B", "Few-shot V3",   RESULTS_DIR / "exp4_fewshot_qwen9b.csv"),
    ("Exp 5 · Gemma 4B",   "Gemma 4 4B",  "Zero-shot V2",  RESULTS_DIR / "exp5_promptv2_gemma4b.csv"),
    ("Exp 6 · Prompt V4",  "Qwen 3.5 9B", "Few-shot V4",   RESULTS_DIR / "exp6_promptv4_qwen9b.csv"),
]

# Etiquetas N2 de B0 (orden canonico para metricas y heatmaps)
LABELS_B0 = ["DIA", "AAP", "AAC", "AAU", "IIA", "AAI", "IAE", "DUP"]

# -- Paleta -------------------------------------------------------------------
# Azules-turquesa para lo normal, coral para destacar lo especial/anomalo.
# Paleta de marca: verdes medioambientales (tomados del logo "ideas
# medioambientales"). Es independiente del modo claro/oscuro.
COLOR_PRIMARIO = "#4c9a2a"        # verde hoja (color principal)
COLOR_PRIMARIO_OSCURO = "#2e7d32"  # verde bosque (acentos profundos)
COLOR_DESTACADO = "#e8743c"       # naranja cálido para anomalías / Gemma
PALETA_VERDES = ["#1b5e20", "#2e7d32", "#4c9a2a", "#7cb342"]  # oscuro -> claro
PALETA_SECUENCIAL = ["#e8f3df", "#aed581", "#7cb342", "#4c9a2a", "#2e7d32", "#1b5e20"]
# Alias retro-compatible (codigo antiguo referenciaba PALETA_AZULES)
PALETA_AZULES = PALETA_VERDES
# Paleta categorica para chips y series: verdes dominantes + tonos naturales
# (teal agua, tierra, ámbar) y el naranja de anomalía al final.
PALETA_CATEGORICA = [
    "#2e7d32", "#4c9a2a", "#7cb342", "#1f9e8f",
    "#6aa84f", "#9c6b3f", "#d99a2b", "#3f7d4e",
    "#aed581", "#557c3e", "#e8743c",
]
COLOR_CHIP_VACIO = "#9aa394"  # chip placeholder para listas vacias
COLOR_BADGE_RELEVANTE = "#2e7d32"  # verde bosque del badge RELEVANTE

# -- Identidad por bloque tematico ---------------------------------------------
# Un color por bloque, usado en TODA la app (selector, chips, sunburst, badges).
# Tonos naturales y distinguibles entre sí, en sintonía con la marca verde.
COLORES_BLOQUE = {
    "B0": "#4c9a2a",  # verde (ambiental-energético, color de marca)
    "B1": "#1f9e8f",  # teal agua (hídrico)
    "B2": "#9c6b3f",  # tierra (urbanístico)
    "B3": "#d99a2b",  # ámbar (subvenciones)
    "B4": "#b5503a",  # terracota (contratación)
}
ICONOS_BLOQUE = {"B0": "🌱", "B1": "💧", "B2": "🏗️", "B3": "💶", "B4": "📜"}

# -- Modo claro / oscuro --------------------------------------------------------
# Superficies que cambian con el modo. La marca (verdes, colores de bloque) NO
# cambia. theme.paleta() devuelve el diccionario del modo activo.
TEMA = {
    "claro": {
        "fondo": "#f1f6ee",          # verde-gris muy claro (como el fondo del logo)
        "tarjeta": "#ffffff",
        "texto": "#34422f",
        "texto_fuerte": "#1c2a16",
        "texto_suave": "#6b7d63",
        "borde": "#e0e8da",
        "grid": "#e0e8da",
        "sidebar": "linear-gradient(200deg, #16301c 0%, #1f4a26 55%, #4c9a2a 135%)",
        "gris_otros": "#cdd5c6",
    },
    "oscuro": {
        "fondo": "#0e1410",          # verde casi negro
        "tarjeta": "#19211a",
        "texto": "#d3e0cd",
        "texto_fuerte": "#eef4ec",
        "texto_suave": "#93a589",
        "borde": "#2a352a",
        "grid": "#2a352a",
        "sidebar": "linear-gradient(200deg, #060b07 0%, #0f2113 55%, #1f4a26 135%)",
        "gris_otros": "#3c4a3a",
    },
}

# -- Sunburst -------------------------------------------------------------------
# Sectores que pesan menos que este umbral respecto a su padre se agrupan en
# "otros (n)" gris para mantener la rueda legible.
UMBRAL_OTROS_SUNBURST = 0.015

# -- Boletines ----------------------------------------------------------------
BOLETINES = [
    "boe", "boja", "bocm", "bocyl", "bon", "dogc", "dog", "dogv", "docm",
    "boib", "boc", "bopa", "boa", "doe", "bor", "borm", "bopv", "boca",
    "madridambiental",
]

NOMBRE_BOLETIN = {
    "boe": "BOE (Estado)",
    "boja": "BOJA (Andalucía)",
    "bocm": "BOCM (C. de Madrid)",
    "bocyl": "BOCYL (Castilla y León)",
    "bon": "BON (Navarra)",
    "dogc": "DOGC (Cataluña)",
    "dog": "DOG (Galicia)",
    "dogv": "DOGV (C. Valenciana)",
    "docm": "DOCM (Castilla-La Mancha)",
    "boib": "BOIB (Illes Balears)",
    "boc": "BOC (Cantabria)",
    "bopa": "BOPA (Asturias)",
    "boa": "BOA (Aragón)",
    "doe": "DOE (Extremadura)",
    "bor": "BOR (La Rioja)",
    "borm": "BORM (R. de Murcia)",
    "bopv": "BOPV (País Vasco)",
    "boca": "BOC (Canarias)",
    "madridambiental": "Madrid Ambiental (local)",
}

# bulletin -> nombre de comunidad autonoma para el coropletico.
# Los valores coinciden EXACTAMENTE con properties.name del geojson cacheado
# (spain-communities.geojson de click_that_hood: sin acentos en varios casos).
# BOE (estatal) y madridambiental (local) NO van al mapa: se muestran aparte.
BULLETIN_A_CCAA = {
    "boja": "Andalucia",
    "boa": "Aragon",
    "bopa": "Asturias",
    "boib": "Baleares",
    "boca": "Canarias",
    "boc": "Cantabria",
    "bocyl": "Castilla-Leon",
    "docm": "Castilla-La Mancha",
    "dogc": "Cataluña",
    "dogv": "Valencia",
    "doe": "Extremadura",
    "dog": "Galicia",
    "bocm": "Madrid",
    "borm": "Murcia",
    "bon": "Navarra",
    "bopv": "Pais Vasco",
    "bor": "La Rioja",
}
GEOJSON_FEATURE_KEY = "properties.name"

# URL publica del geojson de CCAA (se descarga UNA vez en precompute.py)
GEOJSON_CCAA_URL = (
    "https://raw.githubusercontent.com/codeforgermany/click_that_hood/"
    "main/public/data/spain-communities.geojson"
)

# -- Bloques tematicos --------------------------------------------------------
# Configuracion declarativa de cada bloque. llm.py resuelve los imports.
# 'registry_attr' es el nombre del registro dentro de su modulo de prompts
# (B1 lo llama PROMPT_REGISTRY, sin sufijo).
BLOQUES = {
    "B0": dict(
        nombre="B0 · Ambiental-Energético",
        schema_modulo="clasificador.schema_B0",
        schema_clase="ClassifierOutput",
        prompts_modulo="clasificador.prompts_B0",
        registry_attr="PROMPT_REGISTRY",
        version_defecto="v3",
        descripcion="DIA, autorizaciones energéticas (AAP/AAC/AAU), AAI, DUP...",
    ),
    "B1": dict(
        nombre="B1 · Hídrico y Natural",
        schema_modulo="clasificador.schema_B1",
        schema_clase="ClassifierOutput",
        prompts_modulo="clasificador.prompts_B1",
        registry_attr="PROMPT_REGISTRY",
        version_defecto=None,  # None -> la mayor del registry
        descripcion="Concesiones de aguas, montes, vías pecuarias, vertidos...",
    ),
    "B2": dict(
        nombre="B2 · Urbanístico",
        schema_modulo="clasificador.schema_B2",
        schema_clase="ClassifierOutputB2",
        prompts_modulo="clasificador.prompts_B2",
        registry_attr="PROMPT_REGISTRY_B2",
        version_defecto=None,
        descripcion="PGOU, planes especiales, licencias, declaraciones de interés...",
    ),
    "B3": dict(
        nombre="B3 · Subvenciones",
        schema_modulo="clasificador.schema_B3",
        schema_clase="ClassifierOutputB3",
        prompts_modulo="clasificador.prompts_B3",
        registry_attr="PROMPT_REGISTRY_B3",
        version_defecto=None,
        descripcion="Bases reguladoras, convocatorias BDNS, concesiones, reintegros...",
    ),
    "B4": dict(
        nombre="B4 · Contratación Pública",
        schema_modulo="clasificador.schema_B4",
        schema_clase="ClassifierOutputB4",
        prompts_modulo="clasificador.prompts_B4",
        registry_attr="PROMPT_REGISTRY_B4",
        version_defecto=None,
        descripcion="Licitaciones, formalizaciones, adjudicaciones, encomiendas...",
    ),
}

# Keywords de dominio por bloque (las mismas de los notebooks BX). Se usan en
# precompute.py para asignar el anillo "bloque" del sunburst: primer bloque
# cuyo keyword aparece en la descripcion; si ninguno, "sin bloque".
KEYWORDS_BLOQUES = {
    "B0 ambiental-energético": [
        "impacto ambiental", "autorización ambiental", "autorización administrativa previa",
        "autorización administrativa de construcción", "utilidad pública", "fotovoltaica",
        "eólic", "parque solar", "línea eléctrica", "subestación", "evaluación ambiental",
    ],
    "B1 hídrico-natural": [
        "concesión de aguas", "aprovechamiento de aguas", "confederación hidrográfica",
        "vía pecuaria", "monte de utilidad pública", "vertido", "regadío",
        "comunidad de regantes", "parque natural", "red natura",
    ],
    "B2 urbanístico": [
        "plan general de ordenación", "pgou", "plan parcial", "plan especial",
        "estudio de detalle", "modificación puntual", "proyecto de urbanización",
        "reparcelación", "licencia urbanística", "declaración de interés comunitario",
    ],
    "B3 subvenciones": [
        "extracto de la", "convocatoria de subvenc", "convocatoria de ayuda",
        "se convocan", "bdns", "concesión de subvenc", "concesión de ayuda",
        "bases reguladoras", "reintegro de subvenc",
    ],
    "B4 contratación": [
        "anuncio de licitación", "licitación de", "formalización del contrato",
        "formalización de contrato", "adjudicación del contrato",
        "encomienda de gestión", "encargo a medio propio", "concesión de servicio",
    ],
}

# Cadena de modelos online para la demo (FallbackModel, en este orden).
# Verificados en vivo (jun 2026): gemini-2.0-flash y 1.5-flash ya NO tienen
# free tier (429 limit:0); los tres siguientes si responden.
CADENA_MODELOS = [
    "google-gla:gemini-2.5-flash-lite",
    "groq:llama-3.3-70b-versatile",
    "google-gla:gemini-2.5-flash",
]

# -- Galeria de ejemplos (pagina 3) --------------------------------------------
# Textos REALES del ground truth. 'esperado' alimenta el cache de resultados
# para el modo demo sin API keys (precompute.py).
GALERIA_EJEMPLOS = [
    dict(
        id="b0_aau",
        bloque="B0",
        titulo="AAU simplificada (BOJA)",
        bulletin="boja",
        description=(
            "Anuncio de 4 de febrero de 2025, de la Delegación Territorial de "
            "Sostenibilidad, Medio Ambiente y Economía Azul en Huelva, por el que "
            "se da publicidad a la nueva autorización ambiental unificada "
            "simplificada otorgada en esta provincia. (PP. 262/2025)."
        ),
        esperado=dict(
            is_relevant=True, act_type="anuncio", procedures=["AAU"],
            technologies=[], confidence=0.97,
            reasoning="'autorización ambiental unificada' es la señal explícita de AAU (procedimiento andaluz).",
        ),
    ),
    dict(
        id="b0_multi",
        bloque="B0",
        titulo="AAP + AAC + DUP (BOE, Red Eléctrica)",
        bulletin="boe",
        description=(
            "Resolución de 24 de febrero de 2025, de la Dirección General de "
            "Política Energética y Minas, por la que se otorga a Red Eléctrica de "
            "España, SAU, autorización administrativa previa y autorización "
            "administrativa de construcción de la línea aérea de transporte de "
            "energía eléctrica a 400 kV, doble circuito, de entrada y salida en la "
            "subestación Torrejón de Velasco, de la línea eléctrica a 400 kV "
            "Morata-Villaviciosa, en Torrejón de Velasco (Madrid), y se declara, "
            "en concreto, la utilidad pública."
        ),
        esperado=dict(
            is_relevant=True, act_type="resolución",
            procedures=["AAP", "AAC", "DUP"], technologies=["línea_eléctrica"],
            confidence=0.98,
            reasoning="'autorización administrativa previa' → AAP; 'autorización administrativa de construcción' → AAC; 'se declara, en concreto, la utilidad pública' → DUP. 'línea aérea de transporte de energía eléctrica' → línea_eléctrica.",
        ),
    ),
    dict(
        id="b1_riego",
        bloque="B1",
        titulo="Concesión de aguas para riego (CHD)",
        bulletin="boe",
        description=(
            "Anuncio de la Confederación Hidrográfica del Duero, O.A., de "
            "información pública del expediente de modificación de características "
            "de concesión de un aprovechamiento de aguas subterráneas, de "
            "referencia MC-0219/2024 (INTEGRA-AYE) AV, con destino a riego en el "
            "término municipal de Constanzana (Ávila)."
        ),
        esperado=dict(
            is_relevant=True, act_type="anuncio", categories=["AGU_RIE"],
            subcategories=["uso_agricola", "cuenca_duero"], confidence=0.96,
            reasoning="'con destino a riego' → AGU_RIE + uso_agricola. 'Confederación Hidrográfica del Duero' → cuenca_duero. La modificación hereda la etiqueta del acto original.",
        ),
    ),
    dict(
        id="b2_modpun",
        bloque="B2",
        titulo="Modificación que menciona el PGOU (Mijas)",
        bulletin="boja",
        description=(
            "Resolución de 16 de enero de 2025, de la Delegación Territorial de "
            "Fomento, Articulación del Territorio y Vivienda en Málaga, por la que "
            "se dispone la publicación de la Resolución de 11 de diciembre de "
            "2024, que ordena proceder al registro y publicación de la "
            "«Modificación del Plan General de Ordenación Urbana (PGOU) de Mijas»."
        ),
        esperado=dict(
            is_relevant=True, act_type="resolución", categories=["MOD_PUN"],
            subcategories=["fase_definitiva"], confidence=0.93,
            reasoning="'Modificación del Plan General de Ordenación Urbana' → MOD_PUN; el PGOU es el objeto modificado, no el acto. Registro y publicación → fase_definitiva.",
        ),
    ),
    dict(
        id="b3_bdns",
        bloque="B3",
        titulo="Extracto BDNS con bases y convocatoria (DOG)",
        bulletin="dog",
        description=(
            "EXTRACTO de la Orden de 3 de enero de 2025 por la que se establecen "
            "las bases reguladoras de los programas de subvenciones para sufragar "
            "los gastos de funcionamiento de las entidades asociativas gallegas de "
            "personas trabajadoras autónomas y la contratación de personal de "
            "apoyo, y se convocan para el año 2025 (código de procedimiento "
            "TR358A)."
        ),
        esperado=dict(
            is_relevant=True, act_type="extracto", categories=["SUB_CONV"],
            subcategories=["sector_industria", "sector_empleo"], confidence=0.95,
            reasoning="Es un EXTRACTO: la fase es únicamente SUB_CONV aunque el acto extractado establezca las bases. 'entidades de trabajadoras autónomas' → sector_industria; 'contratación de personal de apoyo' → sector_empleo.",
        ),
    ),
    dict(
        id="b4_demanial",
        bloque="B4",
        titulo="Concesión demanial portuaria (caso trampa)",
        bulletin="boe",
        description=(
            "Resolución de la Autoridad Portuaria de Baleares por la que se "
            "anuncia el concurso público para la explotación, en régimen de "
            "concesión administrativa, de un bar-cafetería y restaurante en el "
            "edificio Port Centre del puerto de Palma (CC-C-P-0011), la elección "
            "de la solución más ventajosa y el otorgamiento de la correspondiente "
            "concesión administrativa."
        ),
        esperado=dict(
            is_relevant=False, act_type="resolución", categories=[],
            subcategories=[], confidence=0.9,
            reasoning="'concesión administrativa' de una Autoridad Portuaria es demanial (ocupación de dominio público), no un contrato de concesión de servicios LCSP: irrelevante para B4.",
        ),
    ),
]

# Cifras de control de la pagina 4 (si el calculo no las reproduce, el parseo
# de los CSVs esta mal): Exp1 Macro F1 0.795 · Exp4 Macro 0.975 y F1rel 1.000 ·
# Exp5 (Gemma) Macro 0.974.
CIFRAS_CONTROL = {
    "Exp 1 · Baseline": {"macro_f1": 0.795},
    "Exp 4 · Few-shot": {"macro_f1": 0.975, "is_rel_f1": 1.000},
    "Exp 5 · Gemma 4B": {"macro_f1": 0.974},
}
