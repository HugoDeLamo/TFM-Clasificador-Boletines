"""
Sistema de diseño del dashboard: TODO el CSS vive aqui (inject_css) junto a
los componentes HTML reutilizables. Cada pagina llama theme.inject_css() una
vez al principio. Los colores salen SIEMPRE de config.py.

Animaciones definidas como @keyframes y desactivadas con
prefers-reduced-motion. Nada se mueve en bucle infinito mientras se lee
(unica excepcion: el desplazamiento casi imperceptible del hero y el shimmer
de espera del LLM).
"""

import streamlit as st

from dashboard import config

# Gradiente del hero: turquesa -> azul (como la pagina del clasificador)
_GRAD_HERO = f"linear-gradient(120deg, {config.PALETA_AZULES[2]} 0%, {config.COLOR_PRIMARIO} 55%, {config.PALETA_AZULES[0]} 125%)"


def _tinte(hex_color: str, alpha_hex: str) -> str:
    """Color hex con canal alfa (p.ej. _tinte('#1d6fa3', '1f') -> 12 %)."""
    return f"{hex_color}{alpha_hex}"


_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;700;800&family=Source+Sans+3:wght@400;500;600;700&display=swap');

/* =========================== base =========================== */
html, body, [class*="st-"], .stMarkdown {{ font-family: 'Source Sans 3', sans-serif; }}
h1, h2, h3, h4 {{ font-family: 'Sora', sans-serif !important; letter-spacing: -0.4px; }}
.stApp {{ background: {config.COLOR_FONDO}; }}

/* =========================== sidebar =========================== */
section[data-testid="stSidebar"] {{
  background: linear-gradient(200deg, #0d1b3e 0%, #163b66 55%, {config.COLOR_PRIMARIO} 130%);
}}
section[data-testid="stSidebar"] * {{ color: #eaf3fa !important; }}
section[data-testid="stSidebar"] a:hover {{
  background: rgba(255,255,255,.12) !important; border-radius: 10px;
}}
section[data-testid="stSidebar"] a[aria-current="page"] {{
  background: rgba(65,182,196,.25) !important; border-radius: 10px;
  box-shadow: inset 3px 0 0 {config.PALETA_AZULES[2]};
}}

/* =========================== tarjetas (contenedores con borde) ====== */
div[data-testid="stVerticalBlockBorderWrapper"] {{
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid {config.COLOR_BORDE_TARJETA} !important;
  box-shadow: 0 1px 3px rgba(16,42,67,.08);
  margin-bottom: 1.5rem;
  transition: box-shadow .2s ease, transform .2s ease;
  animation: fadeUp .4s ease backwards;
}}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(16,42,67,.12);
}}
/* entrada escalonada de las primeras tarjetas de la pagina */
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
  border-radius: 14px;
  padding: 2rem 2.4rem;
  margin-bottom: 1.5rem;
  color: #fff;
  box-shadow: 0 10px 30px rgba(16,42,67,.22);
}}
.hero h1 {{ color: #fff; font-size: 2rem; font-weight: 800; margin: 0 0 .35rem 0; }}
.hero p {{ color: #e3f2f9; font-size: 1.02rem; margin: 0; max-width: 58rem; }}
.hero .icono {{
  position: absolute; right: 2rem; top: 50%; transform: translateY(-50%);
  font-size: 4rem; filter: drop-shadow(0 6px 14px rgba(0,0,0,.25));
}}

/* =========================== secciones =========================== */
.seccion {{
  border-left: 4px solid {config.COLOR_PRIMARIO};
  padding-left: .8rem;
  margin: 2rem 0 .9rem 0;
}}
.seccion h2 {{ font-size: 1.3rem; margin: 0; color: {config.COLOR_TEXTO_FUERTE}; }}
div[data-testid="stVerticalBlockBorderWrapper"] .seccion {{ margin-top: .4rem; }}

/* =========================== tarjetas de metrica =========================== */
.fila-tarjetas {{ display: flex; gap: 1rem; flex-wrap: wrap; align-items: stretch; margin: .2rem 0 1.5rem 0; }}
.tarjeta {{
  flex: 1 1 180px; display: flex; flex-direction: column;
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid {config.COLOR_BORDE_TARJETA};
  border-top: 4px solid var(--acento, {config.COLOR_PRIMARIO});
  padding: 1.05rem 1.25rem .95rem;
  box-shadow: 0 1px 3px rgba(16,42,67,.08);
  transition: transform .2s ease, box-shadow .2s ease;
  animation: fadeUp .4s ease backwards;
}}
.tarjeta:nth-child(1) {{ animation-delay: .05s; }}
.tarjeta:nth-child(2) {{ animation-delay: .10s; }}
.tarjeta:nth-child(3) {{ animation-delay: .15s; }}
.tarjeta:nth-child(4) {{ animation-delay: .20s; }}
.tarjeta:nth-child(5) {{ animation-delay: .25s; }}
.tarjeta:hover {{ transform: translateY(-2px); box-shadow: 0 8px 22px rgba(16,42,67,.14); }}
.tarjeta .icono {{ font-size: 1.4rem; margin-bottom: .15rem; }}
.tarjeta .valor {{
  font-family: 'Sora', sans-serif; font-size: 2rem; font-weight: 700;
  color: {config.COLOR_TEXTO_FUERTE}; line-height: 1.15;
  animation: popIn .6s cubic-bezier(.2, 1.3, .4, 1) backwards;
  animation-delay: .25s;
}}
.tarjeta .etiqueta {{ color: {config.COLOR_TEXTO_SUAVE}; font-size: .86rem; font-weight: 600; margin-top: .2rem; }}

/* =========================== tarjetas de bloque (selector) ============ */
.tarjeta-bloque {{
  position: relative; overflow: hidden;
  background: #ffffff;
  border: 1px solid {config.COLOR_BORDE_TARJETA};
  border-radius: 12px;
  padding: .85rem .95rem .6rem;
  min-height: 7.2rem;
  box-shadow: 0 1px 3px rgba(16,42,67,.08);
  transition: transform .2s ease, box-shadow .2s ease;
}}
.tarjeta-bloque::before {{
  content: ""; position: absolute; top: 0; left: 0; right: 0;
  height: 4px; background: var(--cb); transition: height .2s ease;
}}
.tarjeta-bloque:hover {{ transform: translateY(-2px); box-shadow: 0 8px 22px rgba(16,42,67,.14); }}
.tarjeta-bloque:hover::before {{ height: 6px; }}
.tarjeta-bloque.activa {{
  background: var(--cb-fondo);
  border: 1px solid var(--cb);
  box-shadow: 0 0 0 1px var(--cb), 0 6px 18px rgba(16,42,67,.12);
}}
.tarjeta-bloque .nombre {{
  font-family: 'Sora', sans-serif; font-weight: 700; font-size: .92rem;
  color: {config.COLOR_TEXTO_FUERTE}; margin-top: .1rem;
}}
.tarjeta-bloque .desc {{ color: {config.COLOR_TEXTO_SUAVE}; font-size: .76rem; line-height: 1.25; }}

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
.chip:hover {{ transform: translateY(-2px); box-shadow: 0 4px 10px rgba(16,42,67,.15); }}

/* =========================== badge de relevancia ====================== */
.badge-rel {{
  display: inline-block; padding: .6rem 1.5rem; border-radius: 12px;
  color: #fff; font-family: 'Sora', sans-serif; font-weight: 800;
  font-size: 1.2rem; letter-spacing: 1px;
  box-shadow: 0 8px 22px rgba(16,42,67,.22);
  animation: popIn .45s cubic-bezier(.2, 1.4, .4, 1);
}}

/* =========================== pipeline N0 -> N1 -> LLM ================== */
.pipe-fila {{ display: flex; gap: .55rem; align-items: stretch; margin: .4rem 0 .8rem 0; }}
.pipe-paso {{
  flex: 1; background: #fff;
  border: 1px solid {config.COLOR_BORDE_TARJETA}; border-radius: 12px;
  padding: .7rem .9rem; transition: border-color .25s ease;
}}
.pipe-paso .titulo {{ font-weight: 700; font-size: .82rem; color: {config.COLOR_TEXTO_SUAVE}; }}
.pipe-paso .dato {{ font-weight: 600; font-size: .9rem; color: {config.COLOR_TEXTO_FUERTE}; margin-top: .15rem; }}
.pipe-paso.activo {{
  border-color: var(--cb);
  animation: pulso 0.9s ease 2;
}}
.pipe-paso.completo {{ border-color: var(--cb); background: var(--cb-fondo); }}
.pipe-flecha {{
  align-self: center; font-size: 1.5rem; color: {config.COLOR_GRIS_OTROS};
  transition: color .3s ease;
}}
.pipe-flecha.completo {{ color: var(--cb); }}
.skeleton {{
  height: 90px; border-radius: 12px;
  background: linear-gradient(90deg, #eef2f6 25%, #f8fafc 50%, #eef2f6 75%);
  background-size: 200% 100%;
  animation: shimmer 1.2s linear infinite;
}}

/* =========================== barra de confianza ======================== */
.conf-pista {{
  background: #eef2f6; border-radius: 999px; height: 14px; overflow: hidden;
  margin: .4rem 0 .2rem 0;
}}
.conf-relleno {{
  height: 100%; border-radius: 999px; background: var(--cb, {config.COLOR_PRIMARIO});
  animation: rellenar 1s ease-out forwards;
}}
.conf-num {{
  font-family: 'Sora', sans-serif; font-weight: 800; font-size: 1.5rem;
  color: {config.COLOR_TEXTO_FUERTE};
}}

/* =========================== pill de exito =========================== */
.pill-ok {{
  display: inline-flex; align-items: center; gap: .45rem;
  background: #e6f4ea; color: #1e7e34;
  border-radius: 999px; padding: .35rem 1rem;
  font-weight: 700; font-size: .9rem;
}}

/* =========================== badge de bloque =========================== */
.badge-bloque {{
  display: inline-block; padding: 2px 10px; margin: 0 .25rem 0 0;
  border-radius: 999px; font-weight: 700; font-size: .78rem;
  background: var(--bb-fondo); color: var(--bb-color);
  border: 1px solid var(--bb-borde);
}}

/* =========================== tablas (st.table) ========================= */
.stTable table {{ border-collapse: separate; border-spacing: 0; width: 100%; }}
.stTable thead th {{
  background: #f0f4f8 !important; color: {config.COLOR_TEXTO} !important;
  font-weight: 700; font-size: .82rem; text-transform: none;
  border-bottom: 1px solid {config.COLOR_BORDE_TARJETA} !important;
}}
.stTable tbody tr:hover td {{ background: #f4f8fb !important; transition: background .15s ease; }}
.stTable td, .stTable th {{ padding: .45rem .7rem !important; font-size: .88rem; }}

/* =========================== widgets nativos =========================== */
.stButton > button[kind="primary"] {{
  background: {_GRAD_HERO}; background-size: 180% 180%;
  border: none; border-radius: 10px; font-weight: 700;
  box-shadow: 0 4px 14px rgba(29,111,163,.30);
  transition: transform .2s ease, box-shadow .2s ease;
}}
.stButton > button[kind="primary"]:hover {{
  transform: translateY(-2px); box-shadow: 0 8px 20px rgba(29,111,163,.40);
}}
div[data-testid="stMetric"] {{
  background: #ffffff; border-radius: 12px; padding: .85rem 1.05rem;
  border: 1px solid {config.COLOR_BORDE_TARJETA};
  border-left: 4px solid {config.PALETA_AZULES[2]};
  box-shadow: 0 1px 3px rgba(16,42,67,.08);
}}
button[data-testid="stBaseButton-pills"], button[data-testid="stBaseButton-pillsActive"] {{
  border-radius: 999px !important;
  transition: transform .2s ease, box-shadow .2s ease;
}}
button[data-testid="stBaseButton-pills"]:hover {{
  transform: translateY(-2px); box-shadow: 0 4px 12px rgba(16,42,67,.12);
}}
div[data-testid="stExpander"] {{
  background: #ffffff; border-radius: 12px;
  border: 1px solid {config.COLOR_BORDE_TARJETA};
  box-shadow: 0 1px 3px rgba(16,42,67,.08);
}}

/* =========================== keyframes =========================== */
@keyframes fadeUp {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
@keyframes popIn {{ from {{ opacity: 0; transform: scale(.8); }} to {{ opacity: 1; transform: scale(1); }} }}
@keyframes chipPop {{ from {{ opacity: 0; transform: scale(.5); }} to {{ opacity: 1; transform: scale(1); }} }}
@keyframes heroPan {{ from {{ background-position: 0% 50%; }} to {{ background-position: 100% 50%; }} }}
@keyframes pulso {{
  0%, 100% {{ box-shadow: 0 0 0 0 transparent; }}
  50% {{ box-shadow: 0 0 0 6px var(--cb-pulso, rgba(29,111,163,.18)); }}
}}
@keyframes shimmer {{ from {{ background-position: 200% 0; }} to {{ background-position: -200% 0; }} }}
@keyframes rellenar {{ from {{ width: 0; }} }}

/* =========================== accesibilidad =========================== */
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{
    animation: none !important;
    transition: none !important;
  }}
}}
</style>
"""


def inject_css() -> None:
    """Inyecta el CSS global. Llamar una vez al principio de cada pagina."""
    st.markdown(_CSS, unsafe_allow_html=True)


# Alias para compatibilidad con el nombre anterior
inyectar_css = inject_css


# -- Componentes -----------------------------------------------------------------

def hero(titulo: str, subtitulo: str, icono: str = "") -> None:
    """Banner de cabecera con degradado turquesa->azul y desplazamiento lento."""
    icono_html = f'<div class="icono">{icono}</div>' if icono else ""
    st.markdown(
        f'<div class="hero">{icono_html}<h1>{titulo}</h1><p>{subtitulo}</p></div>',
        unsafe_allow_html=True,
    )


def seccion(titulo: str, emoji: str = "") -> None:
    """Encabezado de seccion con barra de acento a la izquierda."""
    pre = f"{emoji} " if emoji else ""
    st.markdown(
        f'<div class="seccion"><h2>{pre}{titulo}</h2></div>',
        unsafe_allow_html=True,
    )


def tarjetas_metricas(items: list[tuple[str, str, str]]) -> None:
    """Fila de tarjetas (icono, valor, etiqueta), misma altura, popIn del numero."""
    tarjetas = []
    for i, (icono, valor, etiqueta) in enumerate(items):
        acento = config.PALETA_CATEGORICA[i % len(config.PALETA_CATEGORICA)]
        tarjetas.append(
            f'<div class="tarjeta" style="--acento:{acento}">'
            f'<div class="icono">{icono}</div>'
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
    texto = "✓ RELEVANTE" if es_relevante else "✗ NO RELEVANTE"
    st.markdown(
        f'<div class="badge-rel" style="background:{color}">{texto}</div>',
        unsafe_allow_html=True,
    )


def badge_bloque(bloque_id: str) -> str:
    """HTML de un badge de bloque con su color identitario (B0..B4)."""
    color = config.COLORES_BLOQUE.get(bloque_id, config.COLOR_GRIS_OTROS)
    nombre = config.BLOQUES.get(bloque_id, {}).get("nombre", bloque_id)
    estilo = (
        f"--bb-fondo:{_tinte(color, '1f')};--bb-color:{color};"
        f"--bb-borde:{_tinte(color, '40')}"
    )
    return f'<span class="badge-bloque" style="{estilo}">{nombre}</span>'


def pill_exito(texto: str) -> None:
    """Pill verde suave compacta (sustituye al st.success de banner)."""
    st.markdown(
        f'<span class="pill-ok">✓ {texto}</span>', unsafe_allow_html=True
    )


def barra_confianza(valor: float, color: str) -> None:
    """Barra de confianza 0-1 que se rellena animada desde 0."""
    pct = max(0.0, min(1.0, float(valor))) * 100
    st.markdown(
        f'<div class="conf-num">{valor:.2f}</div>'
        f'<div class="conf-pista"><div class="conf-relleno" '
        f'style="--cb:{color}; width:{pct:.0f}%"></div></div>'
        f'<div style="color:{config.COLOR_TEXTO_SUAVE}; font-size:.8rem">confianza</div>',
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
                f'<div class="pipe-flecha {flecha_clase}" style="{vars_color}">→</div>'
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
