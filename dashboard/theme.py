"""
Sistema de diseño del dashboard: TODO el CSS vive aqui (inject_css) junto a
los componentes HTML reutilizables. Cada pagina llama theme.inject_css() una
vez al principio.

Soporta modo claro y oscuro: el modo activo (session_state["modo_color"])
selecciona el diccionario de superficies de config.TEMA, y el CSS se reconstruye
con esos colores en cada rerun. La paleta de marca (verdes medioambientales) y
los colores de bloque NO cambian con el modo.

Animaciones definidas como @keyframes y desactivadas con prefers-reduced-motion.
"""

import streamlit as st

from dashboard import config

# Gradiente del hero: lima -> verde hoja -> verde bosque (igual en ambos modos)
_GRAD_HERO = (
    f"linear-gradient(120deg, {config.PALETA_VERDES[3]} 0%, "
    f"{config.COLOR_PRIMARIO} 55%, {config.PALETA_VERDES[1]} 125%)"
)


# -- Modo claro / oscuro ---------------------------------------------------------

def _modo_defecto() -> str:
    import os
    return os.environ.get("DASHBOARD_MODO", "claro")


def modo_actual() -> str:
    """'claro' u 'oscuro'. Lee la clave persistente 'modo_color' (clave normal de
    session_state, NO ligada a un widget, por lo que sobrevive a los cambios de
    página). Prioridad: selección de la sesión > DASHBOARD_MODO > 'claro'."""
    return st.session_state.get("modo_color", _modo_defecto())


def paleta() -> dict:
    """Diccionario de superficies del modo activo (config.TEMA)."""
    return config.TEMA[modo_actual()]


def _sincronizar_modo() -> None:
    """Copia la selección del widget a la clave persistente 'modo_color'."""
    seleccion = st.session_state.get("modo_color_widget")
    if seleccion:
        st.session_state["modo_color"] = seleccion


def selector_modo() -> None:
    """Control de modo claro/oscuro para la barra lateral.

    El widget usa su propia clave ('modo_color_widget'); el valor real vive en
    'modo_color' (clave normal que persiste entre páginas). El widget se
    inicializa desde esa clave, así que aunque Streamlit limpie el estado del
    widget al cambiar de página, el modo se restaura del valor persistente.
    """
    st.session_state.setdefault("modo_color", _modo_defecto())
    st.segmented_control(
        "Tema",
        options=["claro", "oscuro"],
        format_func=lambda m: ("Claro" if m == "claro" else "Oscuro"),
        default=st.session_state["modo_color"],
        key="modo_color_widget",
        on_change=_sincronizar_modo,
    )


def _tinte(hex_color: str, alpha_hex: str) -> str:
    """Color hex con canal alfa (p.ej. _tinte('#4c9a2a', '1f') -> 12 %)."""
    return f"{hex_color}{alpha_hex}"


# -- CSS -------------------------------------------------------------------------

def _css(p: dict) -> str:
    """Construye la hoja de estilos con los colores del modo activo `p`."""
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;700;800&family=Source+Sans+3:wght@400;500;600;700&display=swap');

/* =========================== base =========================== */
html, body, [class*="st-"], .stMarkdown {{ font-family: 'Source Sans 3', sans-serif; }}
h1, h2, h3, h4 {{ font-family: 'Sora', sans-serif !important; letter-spacing: -0.4px; color: {p['texto_fuerte']}; }}
/* Iconos de Streamlit (ligaduras de Material Symbols): mantener su fuente */
[data-testid="stIconMaterial"], span[class*="material-symbols"],
.material-symbols-rounded, .material-symbols-outlined {{
  font-family: 'Material Symbols Rounded' !important;
  font-weight: normal !important; letter-spacing: normal !important;
}}
.stApp {{ background: {p['fondo']}; }}
.stApp, .stMarkdown, p, span, label, li {{ color: {p['texto']}; }}
/* cabecera superior de Streamlit: transparente para fundirse con el fondo */
header[data-testid="stHeader"] {{ background: transparent !important; }}

/* =========================== sidebar =========================== */
section[data-testid="stSidebar"] {{ background: {p['sidebar']}; }}
section[data-testid="stSidebar"] * {{ color: #eaf3e6 !important; }}
section[data-testid="stSidebar"] a:hover {{
  background: rgba(255,255,255,.12) !important; border-radius: 10px;
}}
section[data-testid="stSidebar"] a[aria-current="page"] {{
  background: rgba(124,179,66,.30) !important; border-radius: 10px;
  box-shadow: inset 3px 0 0 {config.PALETA_VERDES[3]};
}}

/* =========================== tarjetas =========================== */
div[data-testid="stVerticalBlockBorderWrapper"] {{
  background: {p['tarjeta']};
  border-radius: 12px;
  border: 1px solid {p['borde']} !important;
  box-shadow: 0 1px 3px rgba(8,20,12,.08);
  margin-bottom: 1.5rem;
  transition: box-shadow .2s ease, transform .2s ease;
  animation: fadeUp .4s ease backwards;
}}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(8,20,12,.14);
}}
div[data-testid="stVerticalBlockBorderWrapper"]:nth-of-type(1) {{ animation-delay: .05s; }}
div[data-testid="stVerticalBlockBorderWrapper"]:nth-of-type(2) {{ animation-delay: .10s; }}
div[data-testid="stVerticalBlockBorderWrapper"]:nth-of-type(3) {{ animation-delay: .15s; }}
div[data-testid="stVerticalBlockBorderWrapper"]:nth-of-type(4) {{ animation-delay: .20s; }}
div[data-testid="stVerticalBlockBorderWrapper"]:nth-of-type(5) {{ animation-delay: .25s; }}
div[data-testid="stVerticalBlockBorderWrapper"]:nth-of-type(6) {{ animation-delay: .30s; }}

/* =========================== hero =========================== */
.hero {{
  position: relative; overflow: hidden;
  background: {_GRAD_HERO};
  background-size: 180% 180%;
  animation: heroPan 15s ease-in-out infinite alternate;
  border-radius: 14px; padding: 2rem 2.4rem; margin-bottom: 1.5rem;
  color: #fff; box-shadow: 0 10px 30px rgba(8,20,12,.25);
}}
.hero h1 {{ color: #fff !important; font-size: 2rem; font-weight: 800; margin: 0 0 .35rem 0; }}
.hero p {{ color: #eaf6e2 !important; font-size: 1.02rem; margin: 0; max-width: 58rem; }}
.hero .icono {{
  position: absolute; right: 2rem; top: 50%; transform: translateY(-50%);
  font-size: 4rem; filter: drop-shadow(0 6px 14px rgba(0,0,0,.25));
}}

/* =========================== secciones =========================== */
.seccion {{ border-left: 4px solid {config.COLOR_PRIMARIO}; padding-left: .8rem; margin: 2rem 0 .9rem 0; }}
.seccion h2 {{ font-size: 1.3rem; margin: 0; color: {p['texto_fuerte']}; }}
div[data-testid="stVerticalBlockBorderWrapper"] .seccion {{ margin-top: .4rem; }}

/* =========================== tarjetas de metrica =========================== */
.fila-tarjetas {{ display: flex; gap: 1rem; flex-wrap: wrap; align-items: stretch; margin: .2rem 0 1.5rem 0; }}
.tarjeta {{
  flex: 1 1 180px; display: flex; flex-direction: column;
  background: {p['tarjeta']}; border-radius: 12px;
  border: 1px solid {p['borde']};
  border-top: 4px solid var(--acento, {config.COLOR_PRIMARIO});
  padding: 1.05rem 1.25rem .95rem;
  box-shadow: 0 1px 3px rgba(8,20,12,.08);
  transition: transform .2s ease, box-shadow .2s ease;
  animation: fadeUp .4s ease backwards;
}}
.tarjeta:nth-child(1) {{ animation-delay: .05s; }}
.tarjeta:nth-child(2) {{ animation-delay: .10s; }}
.tarjeta:nth-child(3) {{ animation-delay: .15s; }}
.tarjeta:nth-child(4) {{ animation-delay: .20s; }}
.tarjeta:nth-child(5) {{ animation-delay: .25s; }}
.tarjeta:hover {{ transform: translateY(-2px); box-shadow: 0 8px 22px rgba(8,20,12,.14); }}
.tarjeta .valor {{
  font-family: 'Sora', sans-serif; font-size: 2rem; font-weight: 700;
  color: {p['texto_fuerte']}; line-height: 1.15;
  animation: popIn .6s cubic-bezier(.2, 1.3, .4, 1) backwards; animation-delay: .25s;
}}
.tarjeta .etiqueta {{ color: {p['texto_suave']}; font-size: .86rem; font-weight: 600; margin-top: .2rem; }}

/* =========================== tarjetas de bloque (selector) =========================== */
.tarjeta-bloque {{
  position: relative; overflow: hidden;
  background: {p['tarjeta']}; border: 1px solid {p['borde']}; border-radius: 12px;
  padding: .85rem .95rem .6rem; min-height: 7.2rem;
  box-shadow: 0 1px 3px rgba(8,20,12,.08);
  transition: transform .2s ease, box-shadow .2s ease;
}}
.tarjeta-bloque::before {{
  content: ""; position: absolute; top: 0; left: 0; right: 0;
  height: 4px; background: var(--cb); transition: height .2s ease;
}}
.tarjeta-bloque:hover {{ transform: translateY(-2px); box-shadow: 0 8px 22px rgba(8,20,12,.14); }}
.tarjeta-bloque:hover::before {{ height: 6px; }}
.tarjeta-bloque.activa {{
  background: var(--cb-fondo); border: 1px solid var(--cb);
  box-shadow: 0 0 0 1px var(--cb), 0 6px 18px rgba(8,20,12,.14);
}}
.tarjeta-bloque .nombre {{
  font-family: 'Sora', sans-serif; font-weight: 700; font-size: .92rem;
  color: {p['texto_fuerte']}; margin-top: .1rem;
}}
.tarjeta-bloque .desc {{ color: {p['texto_suave']}; font-size: .76rem; line-height: 1.25; }}

/* =========================== chips =========================== */
.chip {{
  display: inline-block; padding: 4px 12px; margin: .18rem .3rem .18rem 0;
  border-radius: 999px;
  background: var(--chip-fondo); color: var(--chip-color);
  border: 1px solid var(--chip-borde);
  font-weight: 700; font-size: .85rem; letter-spacing: .2px;
  transition: transform .2s ease, box-shadow .2s ease;
  animation: chipPop .35s cubic-bezier(.34, 1.56, .64, 1) backwards;
}}
.chip:hover {{ transform: translateY(-2px); box-shadow: 0 4px 10px rgba(8,20,12,.18); }}

/* =========================== badge de relevancia =========================== */
.badge-rel {{
  display: inline-block; padding: .6rem 1.5rem; border-radius: 12px;
  color: #fff; font-family: 'Sora', sans-serif; font-weight: 800;
  font-size: 1.2rem; letter-spacing: 1px;
  box-shadow: 0 8px 22px rgba(8,20,12,.22);
  animation: popIn .45s cubic-bezier(.2, 1.4, .4, 1);
}}

/* =========================== pipeline N0 -> N1 -> LLM =========================== */
.pipe-fila {{ display: flex; gap: .55rem; align-items: stretch; margin: .4rem 0 .8rem 0; }}
.pipe-paso {{
  flex: 1; background: {p['tarjeta']};
  border: 1px solid {p['borde']}; border-radius: 12px;
  padding: .7rem .9rem; transition: border-color .25s ease;
}}
.pipe-paso .titulo {{ font-weight: 700; font-size: .82rem; color: {p['texto_suave']}; }}
.pipe-paso .dato {{ font-weight: 600; font-size: .9rem; color: {p['texto_fuerte']}; margin-top: .15rem; }}
.pipe-paso.activo {{ border-color: var(--cb); animation: pulso 0.9s ease 2; }}
.pipe-paso.completo {{ border-color: var(--cb); background: var(--cb-fondo); }}
.pipe-flecha {{ align-self: center; font-size: 1.5rem; color: {p['gris_otros']}; transition: color .3s ease; }}
.pipe-flecha.completo {{ color: var(--cb); }}
.skeleton {{
  height: 90px; border-radius: 12px;
  background: linear-gradient(90deg, {p['borde']} 25%, {p['tarjeta']} 50%, {p['borde']} 75%);
  background-size: 200% 100%; animation: shimmer 1.2s linear infinite;
}}

/* =========================== barra de confianza =========================== */
.conf-pista {{ background: {p['borde']}; border-radius: 999px; height: 14px; overflow: hidden; margin: .4rem 0 .2rem 0; }}
.conf-relleno {{ height: 100%; border-radius: 999px; background: var(--cb, {config.COLOR_PRIMARIO}); animation: rellenar 1s ease-out forwards; }}
.conf-num {{ font-family: 'Sora', sans-serif; font-weight: 800; font-size: 1.5rem; color: {p['texto_fuerte']}; }}

/* =========================== pill de exito =========================== */
.pill-ok {{
  display: inline-flex; align-items: center; gap: .45rem;
  background: {_tinte(config.COLOR_PRIMARIO, '24')}; color: {config.COLOR_PRIMARIO};
  border-radius: 999px; padding: .35rem 1rem; font-weight: 700; font-size: .9rem;
}}

/* =========================== badge de bloque =========================== */
.badge-bloque {{
  display: inline-block; padding: 2px 10px; margin: 0 .25rem 0 0;
  border-radius: 999px; font-weight: 700; font-size: .78rem;
  background: var(--bb-fondo); color: var(--bb-color); border: 1px solid var(--bb-borde);
}}

/* =========================== tablas (st.table) =========================== */
.stTable table {{ border-collapse: separate; border-spacing: 0; width: 100%; background: {p['tarjeta']}; }}
.stTable thead th {{
  background: {_tinte(config.COLOR_PRIMARIO, '14')} !important; color: {p['texto_fuerte']} !important;
  font-weight: 700; font-size: .82rem; border-bottom: 1px solid {p['borde']} !important;
}}
.stTable tbody tr:hover td {{ background: {_tinte(config.COLOR_PRIMARIO, '0d')} !important; transition: background .15s ease; }}
.stTable td, .stTable th {{ padding: .45rem .7rem !important; font-size: .88rem; color: {p['texto']}; border-color: {p['borde']} !important; }}

/* =========================== widgets nativos =========================== */
.stButton > button[kind="primary"] {{
  background: {_GRAD_HERO}; background-size: 180% 180%; border: none; border-radius: 10px;
  font-weight: 700; box-shadow: 0 4px 14px rgba(76,154,42,.30);
  transition: transform .2s ease, box-shadow .2s ease;
}}
.stButton > button[kind="primary"]:hover {{ transform: translateY(-2px); box-shadow: 0 8px 20px rgba(76,154,42,.40); }}
/* botón primario deshabilitado: gris apagado (se "enciende" al habilitarse) */
.stButton > button[kind="primary"]:disabled {{
  background: {p['borde']} !important; color: {p['texto_suave']} !important;
  box-shadow: none !important; transform: none !important; cursor: not-allowed; opacity: .7;
}}
.stButton > button[kind="secondary"] {{
  background: {p['tarjeta']}; color: {p['texto']}; border: 1px solid {p['borde']};
}}
div[data-testid="stMetric"] {{
  background: {p['tarjeta']}; border-radius: 12px; padding: .85rem 1.05rem;
  border: 1px solid {p['borde']}; border-left: 4px solid {config.PALETA_VERDES[2]};
  box-shadow: 0 1px 3px rgba(8,20,12,.08);
}}
div[data-testid="stMetric"] * {{ color: {p['texto_fuerte']}; }}
/* inputs, areas y selects: superficie de tarjeta del modo activo */
.stTextInput input, .stTextArea textarea, .stNumberInput input,
.stDateInput input {{
  background: {p['tarjeta']} !important; color: {p['texto']} !important;
}}
.stTextInput input::placeholder, .stTextArea textarea::placeholder {{ color: {p['texto_suave']} !important; }}
div[data-baseweb="select"] > div, div[data-baseweb="base-input"] {{
  background: {p['tarjeta']} !important; border-color: {p['borde']} !important;
}}
div[data-baseweb="select"] * {{ color: {p['texto']} !important; }}
/* menu desplegable de los selectbox/multiselect (se monta al final del body).
   BaseWeb pinta el texto y el fondo del resaltado en elementos hijos, asi que
   hay que forzar tambien los descendientes (*). */
ul[role="listbox"], div[data-baseweb="menu"], div[data-baseweb="popover"] div[role="listbox"],
div[data-baseweb="popover"] ul {{
  background: {p['tarjeta']} !important; border: 1px solid {p['borde']} !important;
}}
[role="option"] {{ background: {p['tarjeta']} !important; color: {p['texto']} !important; }}
[role="option"] * {{ color: {p['texto']} !important; background: transparent !important; }}
[role="option"]:hover, [role="option"][aria-selected="true"] {{
  background: {_tinte(config.COLOR_PRIMARIO, '22')} !important;
}}
[role="option"]:hover *, [role="option"][aria-selected="true"] * {{
  color: {config.COLOR_PRIMARIO} !important;
}}
/* etiquetas (tags) del multiselect */
span[data-baseweb="tag"] {{ background: {_tinte(config.COLOR_PRIMARIO, '24')} !important; }}
span[data-baseweb="tag"] * {{ color: {config.COLOR_PRIMARIO} !important; }}
/* grupos de botones: pills Y segmented_control (selector de tema). El texto va
   en un hijo, por eso se fuerza el color tambien en los descendientes (*). */
div[data-testid="stButtonGroup"] button {{
  border-radius: 999px !important; transition: transform .2s ease, box-shadow .2s ease;
  background: {p['tarjeta']} !important; border: 1px solid {p['borde']} !important;
}}
div[data-testid="stButtonGroup"] button * {{ color: {p['texto_fuerte']} !important; }}
div[data-testid="stButtonGroup"] button[aria-checked="true"],
button[data-testid="stBaseButton-pillsActive"],
button[data-testid="stBaseButton-segmented_controlActive"] {{
  background: {_tinte(config.COLOR_PRIMARIO, '24')} !important; border-color: {config.COLOR_PRIMARIO} !important;
}}
div[data-testid="stButtonGroup"] button[aria-checked="true"] *,
button[data-testid="stBaseButton-pillsActive"] *,
button[data-testid="stBaseButton-segmented_controlActive"] * {{
  color: {config.COLOR_PRIMARIO} !important;
}}
div[data-testid="stButtonGroup"] button:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(8,20,12,.14); }}
div[data-testid="stExpander"] {{ background: {p['tarjeta']}; border-radius: 12px; border: 1px solid {p['borde']}; box-shadow: 0 1px 3px rgba(8,20,12,.08); overflow: hidden; }}
/* cabecera (summary) del expander: misma superficie que el cuerpo */
div[data-testid="stExpander"] details, div[data-testid="stExpander"] summary {{
  background: {p['tarjeta']} !important;
}}
div[data-testid="stExpander"] summary, div[data-testid="stExpander"] summary * {{ color: {p['texto_fuerte']} !important; }}
/* bloques de codigo (st.code): superficie y texto del modo activo */
[data-testid="stCode"], [data-testid="stCode"] pre, .stCode pre, pre, code {{
  background: {p['fondo']} !important; color: {p['texto']} !important;
}}
[data-testid="stCode"] {{ border: 1px solid {p['borde']}; border-radius: 8px; }}

/* =========================== keyframes =========================== */
@keyframes fadeUp {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
@keyframes popIn {{ from {{ opacity: 0; transform: scale(.8); }} to {{ opacity: 1; transform: scale(1); }} }}
@keyframes chipPop {{ from {{ opacity: 0; transform: scale(.5); }} to {{ opacity: 1; transform: scale(1); }} }}
@keyframes heroPan {{ from {{ background-position: 0% 50%; }} to {{ background-position: 100% 50%; }} }}
@keyframes pulso {{ 0%, 100% {{ box-shadow: 0 0 0 0 transparent; }} 50% {{ box-shadow: 0 0 0 6px var(--cb-pulso, rgba(76,154,42,.18)); }} }}
@keyframes shimmer {{ from {{ background-position: 200% 0; }} to {{ background-position: -200% 0; }} }}
@keyframes rellenar {{ from {{ width: 0; }} }}

@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ animation: none !important; transition: none !important; }}
}}
</style>
"""


def inject_css() -> None:
    """Inyecta el CSS global con los colores del modo activo."""
    st.markdown(_css(paleta()), unsafe_allow_html=True)


# -- Componentes -----------------------------------------------------------------

def hero(titulo: str, subtitulo: str, icono: str = "") -> None:
    """Banner de cabecera con degradado verde y desplazamiento lento."""
    icono_html = f'<div class="icono">{icono}</div>' if icono else ""
    st.markdown(
        f'<div class="hero">{icono_html}<h1>{titulo}</h1><p>{subtitulo}</p></div>',
        unsafe_allow_html=True,
    )


def seccion(titulo: str) -> None:
    """Encabezado de seccion con barra de acento a la izquierda (sin emoji)."""
    st.markdown(
        f'<div class="seccion"><h2>{titulo}</h2></div>', unsafe_allow_html=True
    )


def tarjetas_metricas(items: list[tuple[str, str]]) -> None:
    """Fila de tarjetas (valor, etiqueta), misma altura, popIn del numero.

    El acento superior rota los colores de bloque para dar variedad cromática.
    """
    acentos = list(config.COLORES_BLOQUE.values())
    tarjetas = []
    for i, (valor, etiqueta) in enumerate(items):
        acento = acentos[i % len(acentos)]
        tarjetas.append(
            f'<div class="tarjeta" style="--acento:{acento}">'
            f'<div class="valor">{valor}</div>'
            f'<div class="etiqueta">{etiqueta}</div></div>'
        )
    st.markdown(
        f'<div class="fila-tarjetas">{"".join(tarjetas)}</div>',
        unsafe_allow_html=True,
    )


def chip(texto: str, color: str, retraso_ms: int = 0) -> str:
    """HTML de un chip: fondo al 12 %, texto al 100 % del color, entrada en cascada."""
    estilo = (
        f"--chip-fondo:{_tinte(color, '1f')};"
        f"--chip-color:{color};"
        f"--chip-borde:{_tinte(color, '40')};"
        f"animation-delay:{retraso_ms}ms"
    )
    return f'<span class="chip" style="{estilo}">{texto}</span>'


def badge_relevancia(es_relevante: bool) -> None:
    color = config.COLOR_BADGE_RELEVANTE if es_relevante else config.COLOR_DESTACADO
    texto = "RELEVANTE" if es_relevante else "NO RELEVANTE"
    st.markdown(
        f'<div class="badge-rel" style="background:{color}">{texto}</div>',
        unsafe_allow_html=True,
    )


def badge_bloque(bloque_id: str) -> str:
    """HTML de un badge de bloque con su color identitario (B0..B4)."""
    color = config.COLORES_BLOQUE.get(bloque_id, paleta()["gris_otros"])
    nombre = config.BLOQUES.get(bloque_id, {}).get("nombre", bloque_id)
    estilo = (
        f"--bb-fondo:{_tinte(color, '1f')};--bb-color:{color};"
        f"--bb-borde:{_tinte(color, '40')}"
    )
    return f'<span class="badge-bloque" style="{estilo}">{nombre}</span>'


def pill_exito(texto: str) -> None:
    """Pill verde suave compacta (sustituye al st.success de banner)."""
    st.markdown(f'<span class="pill-ok">{texto}</span>', unsafe_allow_html=True)


def barra_confianza(valor: float, color: str) -> None:
    """Barra de confianza 0-1 que se rellena animada desde 0."""
    pct = max(0.0, min(1.0, float(valor))) * 100
    st.markdown(
        f'<div class="conf-num">{valor:.2f}</div>'
        f'<div class="conf-pista"><div class="conf-relleno" '
        f'style="--cb:{color}; width:{pct:.0f}%"></div></div>'
        f'<div style="color:{paleta()["texto_suave"]}; font-size:.8rem">confianza</div>',
        unsafe_allow_html=True,
    )


def pipeline_html(pasos: list[dict], color_bloque: str) -> str:
    """HTML del flujo N0 -> N1 -> LLM como 3 tarjetas conectadas.

    pasos: [{titulo, dato, estado}] con estado en {pendiente, activo, completo}.
    La flecha se enciende cuando el paso ANTERIOR esta completo.
    """
    vars_color = (
        f"--cb:{color_bloque};"
        f"--cb-fondo:{_tinte(color_bloque, '14')};"
        f"--cb-pulso:{_tinte(color_bloque, '30')}"
    )
    piezas = []
    for i, paso in enumerate(pasos):
        if i > 0:
            flecha_clase = "completo" if pasos[i - 1]["estado"] == "completo" else ""
            piezas.append(
                f'<div class="pipe-flecha {flecha_clase}" style="{vars_color}">&#8594;</div>'
            )
        estado = paso.get("estado", "pendiente")
        dato = paso.get("dato") or "&nbsp;"
        piezas.append(
            f'<div class="pipe-paso {estado}" style="{vars_color}">'
            f'<div class="titulo">{paso["titulo"]}</div>'
            f'<div class="dato">{dato}</div></div>'
        )
    return f'<div class="pipe-fila">{"".join(piezas)}</div>'


def tarjeta_bloque_html(bloque_id: str, activa: bool) -> str:
    """HTML de la tarjeta del selector de bloque (icono, nombre, descripcion)."""
    cfg = config.BLOQUES[bloque_id]
    color = config.COLORES_BLOQUE[bloque_id]
    icono = config.ICONOS_BLOQUE.get(bloque_id, "")
    clase = "tarjeta-bloque activa" if activa else "tarjeta-bloque"
    estilo = f"--cb:{color};--cb-fondo:{_tinte(color, '14')}"
    return (
        f'<div class="{clase}" style="{estilo}">'
        f'<div style="font-size:1.3rem">{icono}</div>'
        f'<div class="nombre">{cfg["nombre"]}</div>'
        f'<div class="desc">{cfg["descripcion"]}</div></div>'
    )
