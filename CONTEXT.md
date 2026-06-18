# Contexto del Proyecto: BOOKCAM

Herramienta de digitalización inteligente para estudiantes STEM. Convierte fotos de tableros, diapositivas y apuntes manuales en notas digitales estructuradas en Markdown, preservando fórmulas (LaTeX) y referencias a figuras originales.

- **Estado actual:** CLI en Python funcional (V0).
- **Objetivo futuro:** Aplicación móvil interactiva (MVP en Flutter).

---

## 1. Stack Técnico Activo

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.10+ |
| IA | Gemini API (`gemini-2.5-flash`) con SDK `google-genai` |
| Imágenes | `pillow` (EXIF, resize, contraste) |
| Persistencia | Sistema de archivos local (Markdown + JPG) |
| Autenticación | Variable de entorno `GEMINI_API_KEY` o `GOOGLE_API_KEY` |

---

## 2. Estructura del Repositorio

```text
BOOKCAM/
├── digitalizador.py     # Script principal CLI
├── requirements.txt     # google-genai, pillow
├── CONTEXT.md           # Contexto del proyecto (este archivo)
├── .gitignore
├── fotos_prueba/        # Imágenes de prueba locales
├── notas/               # Carpeta de salida por defecto (gitignored)
└── tablero_prueba.jpg   # Imagen de ejemplo
```

### Salida generada

**Imagen individual** (`procesar_imagen`): crea una carpeta con timestamp basada en el nombre del archivo:

```text
notas/
└── {Curso}/
    └── {YYYY-MM-DD_HHMMSS}_{nombre_imagen}/
        ├── original.jpg   # Imagen optimizada enviada al LLM
        └── nota.md        # Apunte digitalizado
```

**Carpeta de imágenes** (`procesar_carpeta`): crea **una sola carpeta y un solo `nota.md`** con el contenido combinado de todas las imágenes, enviadas en una única llamada al LLM y en el orden alfabético de los archivos:

```text
notas/
└── {Curso}/
    └── {YYYY-MM-DD_HHMMSS}_{nombre_carpeta}/
        ├── original_1.jpg  # Imágenes optimizadas, en orden
        ├── original_2.jpg
        ├── ...
        └── nota.md         # Apunte único combinando todas las imágenes
```

Si no se indica `--curso`, se usa el slug `sin_curso`. Formatos no soportados (p. ej. PDF) dentro de la carpeta se ignoran silenciosamente.

---

## 3. Uso del CLI

```bash
# Configurar API key
export GEMINI_API_KEY='tu_clave'

# Instalar dependencias
pip install -r requirements.txt

# Una sola imagen
python digitalizador.py ruta/imagen.jpg --curso Calculo --out notas

# Carpeta con varias imágenes (procesamiento por lotes)
python digitalizador.py fotos_prueba/ --curso Fisica --out notas

# Cambiar modelo
python digitalizador.py imagen.png --model gemini-2.5-flash
```

**Argumentos:**

| Argumento | Descripción | Default |
|---|---|---|
| `imagen` | Ruta a imagen o carpeta | (requerido) |
| `--out` | Directorio de salida | `notas` |
| `--curso` | Nombre del curso/materia | `sin_curso` |
| `--model` | Modelo Gemini | `gemini-2.5-flash` |

**Formatos soportados:** `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.tiff`

---

## 4. Comportamiento del Sistema

### 4.1 Procesamiento de imágenes (`preparar_imagen`)

1. Corrección EXIF (orientación).
2. Conversión a RGB.
3. Redimensionado inteligente (máx. 1600 px, sin ampliar).
4. Mejora de contraste (+15 %).

### 4.2 Reglas de la IA (`construir_prompt` / `construir_prompt_multiple`)

- Salida estrictamente en Markdown.
- Títulos con `#` / `##`, listas con `-`.
- Fórmulas en LaTeX: inline `$...$` y bloque `$$...$$`.
- Figuras: la IA **no** reconstruye diagramas. Referencia la imagen con `![Figura N](original.jpg)` (o `original_N.jpg` en lotes) bajo una sección `## Figuras`.
- Corregir OCR obvio; **no inventar** contenido.
- En modo carpeta (`construir_prompt_multiple`): se le indica explícitamente a la IA el orden y nombre de cada imagen, y se le pide tratar el conjunto como un único documento continuo, sin repetir contenido entre imágenes.

### 4.3 Funciones principales

| Función | Responsabilidad |
|---|---|
| `preparar_imagen()` | Preprocesamiento visual |
| `construir_prompt()` / `construir_prompt_multiple()` | Prompt para una imagen / para un lote combinado |
| `procesar_imagen()` | Una imagen → carpeta con `nota.md` |
| `procesar_carpeta()` | Carpeta de imágenes → **una sola** llamada a Gemini con todas las imágenes en orden → un único `nota.md` combinado |
| `main()` | CLI con `argparse` |

El procesamiento por carpeta envía todas las imágenes en una sola petición al modelo (no una petición por imagen), por lo que un fallo de la API afecta a todo el lote, no a una imagen individual.

---

## 5. Roadmap

### Fase 1 — Mejoras al core Python (actual)

- [x] Procesar múltiples imágenes automáticamente (`procesar_carpeta`), combinadas en una sola nota.
- [ ] Generar un `index.md` global para organizar el directorio.
- [ ] Detección y estructuración automática de títulos.

### Fase 2 — Interfaz y funcionalidad extendida

- [ ] Interfaz gráfica simple / drag & drop.
- [ ] Exportación de `.md` a PDF manteniendo imágenes embebidas.
- [ ] Integración nativa con bóvedas de Obsidian.

### Fase 3 — App móvil (MVP)

- [ ] UI de gestión académica (Materias → Clases → Notas).
- [ ] Flujo de captura (Cámara → Recorte → Mejora visual).
- [ ] Editor híbrido (texto editable OCR + bloques de imagen intactos).

**Stack propuesto V1 móvil:** Flutter, Hive/SQLite/Isar, ML Kit/Tesseract + Gemini, exportación PDF con paquete `pdf`.

---

## 6. Decisiones de Diseño

1. **Figuras intactas:** Las gráficas no se interpretan semánticamente. Se mantienen como recortes de imagen incrustados para evitar pérdida visual.
2. **Texto editable:** Todo texto OCR/IA debe poder corregirse; la escritura manual nunca es 100 % fiable.
3. **Local-first:** Sin login ni sincronización en la nube en el MVP. Persistencia local por simplicidad y coste.
4. **Modularidad progresiva:** Separar preprocesamiento, cliente Gemini y generación Markdown cuando el proyecto crezca. En V0 conviven en `digitalizador.py`.

---

## 7. Instrucciones para Asistentes IA

**Rol:** Ingeniero senior en Python, procesamiento básico de imágenes (Pillow) e integración con LLMs.

**Antes de cambios estructurales:**

- Revisar la estructura de salida (sección 2) y mantener Markdown limpio con preservación de imágenes.
- Respetar el flujo CLI existente (`procesar_imagen`, `procesar_carpeta`, flags `--out`, `--curso`, `--model`).
- No proponer integraciones en la nube, bases de datos remotas ni autenticación salvo petición explícita para V2.

**Prioridad inmediata (Fase 1):** `index.md` global y detección automática de títulos.

**Ejemplo de prompt de sesión:**

> Lee `CONTEXT.md`. Prioridad: Fase 1 — generar un `index.md` que liste las notas bajo `notas/{curso}/`. Revisa `procesar_carpeta` y propón la implementación mínima.
