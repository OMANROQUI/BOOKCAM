import os
import argparse
from datetime import datetime
from pathlib import Path

import google.generativeai as genai
from PIL import Image, ImageOps, ImageEnhance


def preparar_imagen(ruta: Path, max_size: int = 1600) -> Image.Image:
    """Arregla rotación EXIF, convierte a RGB y reduce tamaño para ahorrar costo/tiempo."""
    img = Image.open(ruta)
    img = ImageOps.exif_transpose(img)  # corrige rotación de cámara
    img = img.convert("RGB")

    # Redimensionar manteniendo aspecto (para no mandar 4000x3000 si no hace falta)
    w, h = img.size
    scale = min(max_size / w, max_size / h, 1.0)
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)))

    # Mejora ligera de contraste (útil en tablero)
    img = ImageEnhance.Contrast(img).enhance(1.15)
    return img


def construir_prompt(nombre_archivo: str) -> str:
    return f"""
Analiza la imagen y conviértela en APUNTES en **Markdown limpio**.

REGLAS DE SALIDA (OBLIGATORIAS):
1) Devuelve **SOLO Markdown** (sin explicaciones, sin saludos).
2) Estructura:
   - Empieza con: # Título (si no hay, inventa uno corto según el tema)
   - Usa ## para secciones, - para viñetas, 1. para pasos.
3) Fórmulas en LaTeX inline: $...$ y en bloque: $$...$$
4) Si hay código, ponlo en bloques ``` (con lenguaje si se reconoce).
5) Si hay una **gráfica/diagrama/dibujo importante**, NO la redibujes:
   - Añade una sección al final:
     ## Figuras
     - Figura 1: (breve descripción)
     - Incrusta la foto como referencia: ![Figura 1]({nombre_archivo})
   (Si no hay figuras, NO crees esa sección.)
6) Corrige errores obvios de OCR (acentos, palabras partidas), pero NO inventes contenido.

OBJETIVO:
- Que el resultado parezca una nota de clase lista para estudiar.
""".strip()


def procesar_imagen(ruta_imagen: Path, api_key: str, out_dir: Path, curso: str | None = None) -> Path:
    genai.configure(api_key=api_key)

    # Carpeta de salida organizada
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    base = ruta_imagen.stem
    curso_slug = (curso or "sin_curso").strip().replace(" ", "_")
    carpeta = out_dir / curso_slug / f"{timestamp}_{base}"
    carpeta.mkdir(parents=True, exist_ok=True)

    # Copiar/guardar imagen (para que el Markdown la pueda referenciar)
    img_out_name = "original.jpg"
    img_out_path = carpeta / img_out_name

    img = preparar_imagen(ruta_imagen)
    img.save(img_out_path, quality=92)

    prompt = construir_prompt(img_out_name)

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content([prompt, img])

    md_text = (response.text or "").strip()

    md_path = carpeta / "nota.md"
    md_path.write_text(md_text, encoding="utf-8")

    return md_path


def main():
    parser = argparse.ArgumentParser(description="Digitaliza apuntes desde una foto a Markdown con Gemini.")
    parser.add_argument("imagen", type=str, help="Ruta de la imagen (jpg/png).")
    parser.add_argument("--out", type=str, default="notas", help="Directorio base de salida.")
    parser.add_argument("--curso", type=str, default=None, help="Nombre del curso/carpeta (ej: Control, Señales).")
    args = parser.parse_args()

    # API key por variable de entorno (más seguro que pegarla en el código)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit(
            "Falta la API key. Configúrala así:\n"
            "  Windows (PowerShell):  setx GEMINI_API_KEY \"TU_CLAVE\"\n"
            "  Linux/Mac (bash):      export GEMINI_API_KEY=\"TU_CLAVE\"\n"
            "Luego cierra y abre la terminal de nuevo."
        )

    ruta_imagen = Path(args.imagen)
    if not ruta_imagen.exists():
        raise SystemExit(f"No encuentro la imagen: {ruta_imagen}")

    out_dir = Path(args.out)

    md_path = procesar_imagen(ruta_imagen, api_key, out_dir, args.curso)

    print("\n" + "=" * 50)
    print("✅ Nota creada:")
    print(md_path)
    print("=" * 50)
    print(md_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
