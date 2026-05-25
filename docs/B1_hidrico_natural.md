# Bloque B1 - Clasificador Hidrico y Natural

Documenta la taxonomia, señales lexicas, reglas de clasificacion y decisiones de diseño
del bloque B1 del clasificador taxonomico de boletines oficiales españoles.

---

## 1. Alcance del dominio

El bloque B1 cubre publicaciones relacionadas con la gestion del agua, el dominio forestal
y los espacios naturales. Se considera **relevante** cualquier publicacion que contenga al
menos una de las 11 categorias N2 definidas.

**Siempre irrelevantes (is_relevant=False):**
- Oposiciones y convocatorias de empleo publico
- Contratos de obra o suministro sin relacion con agua o naturaleza
- Subvenciones genericas (turismo, industria, cultura...)
- Presupuestos y modificaciones presupuestarias
- Obras de infraestructura viaria sin afeccion al dominio publico hidraulico
- Plantillas organicas y reorganizaciones administrativas
- Telecomunicaciones
- Urbanismo sin afeccion al dominio publico hidraulico

---

## 2. Taxonomia

### N0 - Ambito geografico
Derivado automaticamente del campo `bulletin` sin intervencion del LLM.

| bulletin | ambito |
|----------|--------|
| boe | estatal |
| madridambiental | local |
| resto | autonomico |

### N1 - Tipo de acto administrativo
Inferido por reglas de primer token en `agent.py::inferir_act_type`. Compartido con B0.
Cobertura: ~89.6% del corpus (Q1 2025). El 10.4% restante cae en `OTROS`.

### N2 - Categoria hidrica (clasificada por LLM)

| Etiqueta | Descripcion | Señales lexicas clave | Notas de ambiguedad |
|----------|-------------|----------------------|---------------------|
| AGU_GEN | Concesion de aguas - uso no especificado | "aprovechamiento de aguas" sin uso concreto, "Comisaria de Aguas" | Solo si no hay señal de uso especifico. "Confederacion Hidrografica" NO es señal de AGU_GEN (aparece en todas las concesiones) |
| AGU_RIE | Concesion de aguas - riego y regadio | "regadio", "comunidad de regantes", "riego", "zona regable" | Tiene prioridad sobre AGU_GEN si aparece cualquier señal de riego |
| AGU_SND | Sondeo / captacion puntual de aguas subterraneas | "sondeo para captacion", "captacion de aguas subterraneas", "pozo de captacion", "acuifero" | Siempre captacion puntual, nunca concesion generica - no combinar con AGU_GEN |
| AGU_ABS | Concesion de aguas - abastecimiento urbano | "abastecimiento de agua", "abastecimiento municipal", "agua potable" | Tiene prioridad sobre AGU_GEN |
| AGU_IND | Concesion de aguas - uso industrial o energetico | "aprovechamiento hidroelectrico", "central hidroelectrica", "refrigeracion industrial" | Tiene prioridad sobre AGU_GEN |
| VIA_PEC | Via pecuaria - ocupacion o modificacion | "via pecuaria", "canada real", "cordel", "vereda", "colada" | - |
| MON | Monte de utilidad publica / dominio forestal | "monte de utilidad publica", "dominio publico forestal", "ocupacion de monte" | Excluir toponomia: "Monte Hermoso", "Monte Blanco" etc. no son dominio forestal |
| ESP_NAT | Espacio natural protegido / Red Natura | "parque natural", "parque nacional", "Red Natura 2000", "ZEPA", "ZEC", "reserva de la biosfera", "zona de especial" | - |
| RES | Gestion de residuos | "gestion de residuos", "tratamiento de residuos", "planta de residuos", "vertedero" | - |
| VER | Vertidos de aguas | "autorizacion de vertido", "vertido de aguas residuales" | "dominio publico hidraulico" NO es señal exclusiva de VER - aparece tambien en concesiones |
| PHD | Plan hidrologico de demarcacion | "plan hidrologico", "demarcacion hidrografica", "ciclo de planificacion hidrica" | Solo para planes de demarcacion, nunca para concesiones individuales |

### N3 - Subcategorias (clasificadas por LLM)

**Uso del agua** (asignar solo si hay señal explicita en el texto):

| Valor | Señales |
|-------|---------|
| uso_agricola | riego, regadio, agricultura |
| uso_urbano | abastecimiento municipal, agua potable |
| uso_industrial | industria, refrigeracion, proceso productivo |
| uso_energetico | central hidroelectrica, aprovechamiento energetico |
| uso_mixto | varios usos simultaneos en el mismo expediente |

**Cuenca hidrografica** (inferir desde organismo emisor o provincia):

| Valor | Organismo / ambito geografico |
|-------|-------------------------------|
| cuenca_guadalquivir | CHG, Confederacion Hidrografica del Guadalquivir, provincias Andalucia + Jaen/Cordoba/Sevilla/... |
| cuenca_duero | CHD, Confederacion Hidrografica del Duero, CyL + Portugal |
| cuenca_guadiana | CHGu, provincias Extremadura + Castilla-La Mancha occidental |
| cuenca_ebro | CHE, Aragon + Navarra + La Rioja + Cataluna occidental |
| cuenca_tajo | CHT, Madrid + Castilla-La Mancha + Extremadura oriental |
| cuenca_jucar | CHJ, Comunitat Valenciana + Castilla-La Mancha oriental + Murcia norte |
| cuenca_cantabrico | CHC / CHCa, Asturias + Cantabria + Pais Vasco + Galicia norte |
| cuenca_mino_sil | CHMS, Galicia interior + Leon occidental |
| cuenca_segura | CHS, Murcia + Albacete sur + Alicante sur |
| cuenca_insular | organismos hidraulicos de Canarias o Baleares |

---

## 3. Reglas criticas de clasificacion

1. **is_relevant** - True si y solo si se identifica al menos una categoria N2.

2. **AGU_GEN es residual** - Solo si el uso del agua no esta especificado. Si el texto
   contiene cualquier señal de riego, abastecimiento, industria o energia, usar la etiqueta
   especifica (AGU_RIE, AGU_ABS, AGU_IND) en lugar de AGU_GEN. Nunca combinar AGU_GEN
   con una etiqueta especifica de uso.

3. **AGU_SND excluye AGU_GEN** - Un sondeo de aguas subterraneas es siempre captacion
   puntual. No asignar AGU_GEN adicionalmente.

4. **Multilabel permitido** - Un registro puede recibir varias etiquetas N2 simultaneamente.
   Ejemplo: concesion de riego en zona Red Natura → [AGU_RIE, ESP_NAT].

5. **Herencia de etiqueta** - Las modificaciones, desistimientos y caducidades heredan la
   etiqueta del acto original. Una "modificacion de concesion de riego" es AGU_RIE.

6. **Informacion publica equivale a resolucion** - Los anuncios de informacion publica
   previos a una concesion son tan relevantes como la resolucion final.

7. **PHD es exclusivo de planes de demarcacion** - No aplica a concesiones, autorizaciones
   ni expedientes individuales aunque mencionen la demarcacion hidrografica.

8. **MON requiere contexto forestal** - El termino "monte" en toponomia (Monte Hermoso,
   etc.) no activa MON. Requiere "monte de utilidad publica", "dominio publico forestal"
   u ocupacion de monte con expediente forestal.

9. **"dominio publico hidraulico" no implica VER** - Esta expresion aparece en concesiones
   de agua, autorizaciones de obras y otros actos. VER requiere señal explicita de vertido.

10. **reasoning debe citar fragmento exacto** - El campo reasoning debe reproducir la cadena
    de texto que dispara cada etiqueta, no parafrasearla.

---

## 4. Arquitectura del bloque

```
src/clasificador/
    schema_B0.py    - ActType (compartido), schema B0
    schema_B1.py    - CategoryType, SubcategoryType, ClassifierOutput B1
    prompts_B0.py   - Prompts V1-V4 de B0
    prompts_B1.py   - Prompts V1+ de B1
    agent.py        - build_agent, clasificar_async, run_experiment (genericos)

notebooks/
    B0_ambiental_energetico.ipynb
    B1_hidrico_natural.ipynb

data/ground_truth/
    ground_truth_B1_muestreo.csv   - muestreo estratificado sin anotar
```

`agent.py` es compartido entre bloques. `build_agent` acepta `output_type` y
`prompt_registry` opcionales; si se omiten usa los defaults de B0 (backward-compatible).

---

## 5. Muestreo del ground truth

Muestreo estratificado del corpus de boletines con cuotas por etiqueta N2:

| Etiqueta | Cuota objetivo | Pool estimado |
|----------|---------------|---------------|
| AGU_GEN | 25 | ~1,428 |
| AGU_RIE | 25 | ~1,147 |
| VIA_PEC | 20 | ~299 |
| RES | 15 | ~142 |
| AGU_SND | 15 | verificar |
| AGU_ABS | 15 | verificar |
| MON | 10 | verificar |
| VER | 10 | verificar |
| ESP_NAT | 5 | verificar |
| AGU_IND | 5 | verificar |
| PHD | 5 | verificar |

Keywords de busqueda para ESP_NAT corregidas respecto al diseño original: "espacio natural
protegido" y "reserva natural" daban 0 resultados en el corpus y se sustituyeron por
"parque natural", "parque nacional", "red natura", "zepa", "zec", "zona de especial".

Semilla de reproducibilidad: `SEED = 29092025`.

---

## 6. Historial de versiones del prompt

| Version | Descripcion | Estado |
|---------|-------------|--------|
| V1 | Baseline zero-shot con tabla N2, mapeo cuencas/provincias y 10 reglas criticas | Operativo |
