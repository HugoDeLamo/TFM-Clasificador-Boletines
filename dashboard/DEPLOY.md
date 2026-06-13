# Despliegue de la demo en Streamlit Community Cloud

La demo se despliega desde el repositorio de GitHub en
[share.streamlit.io](https://share.streamlit.io) (gratis para repos públicos).

## Qué se versiona y qué no

- **Sí se versiona** (lo necesita la app en runtime): `dashboard/cache/`
  (corpus agregado, serie temporal, sunburst, geojson, ejemplos cacheados),
  `results/*.csv` (métricas de los experimentos) y los ground truth.
- **No se versiona**: `data/raw/` (el parquet de 65k filas, solo necesario para
  re-ejecutar los notebooks o `precompute.py`) y `.streamlit/secrets.toml`
  (las claves se ponen en el panel de Streamlit Cloud, nunca en el repo).

La app **no lee el parquet crudo en runtime**: trabaja sobre el cache
precalculado, así que el despliegue funciona sin él.

## Pasos

1. **Subir el código a GitHub** (desde tu terminal, con tus credenciales):
   ```bash
   git push origin feature/B1-hidrico-natural
   ```
   Para la demo conviene tenerlo en `main`; si quieres, fusiona la rama o
   despliega directamente desde `feature/B1-hidrico-natural` (Cloud permite
   elegir la rama).

2. **Crear la app en Streamlit Cloud**:
   - Entra en https://share.streamlit.io e inicia sesión con GitHub.
   - "Create app" → "Deploy a public app from GitHub".
   - Repository: `HugoDeLamo/TFM-Clasificador-Boletines`
   - Branch: la rama que hayas subido.
   - **Main file path**: `dashboard/app.py`
   - (Opcional) Advanced settings → Python version: **3.13**.

3. **Claves de API** (para la clasificación en vivo de la página 3):
   En Advanced settings → "Secrets", pega:
   ```toml
   GOOGLE_API_KEY = "tu_clave"
   GROQ_API_KEY = "tu_clave"
   ```
   Sin claves la app arranca igual en **modo demo**: los ejemplos de la galería
   devuelven su resultado precalculado.

   (Opcional) Para fijar el tema por defecto del despliegue, añade en Secrets:
   ```toml
   DASHBOARD_MODO = "oscuro"
   ```
   No es una clave secreta, pero Streamlit Cloud solo expone variables vía
   `st.secrets`/entorno por esta vía.

4. **Deploy**. Streamlit instala `requirements.txt` y arranca `dashboard/app.py`.
   El primer arranque tarda un par de minutos.

## Notas

- `requirements.txt` es la fuente de dependencias en Cloud (incluye `tqdm`,
  que importa el paquete `clasificador`). El `pyproject.toml` no se usa para el
  despliegue.
- El paquete `clasificador` (en `src/`) se importa por inserción en `sys.path`
  desde cada vista; no requiere instalación.
- Si actualizas el cache (`uv run python -m dashboard.precompute`), recuerda
  volver a commitear `dashboard/cache/` para que el cambio llegue a la demo.
