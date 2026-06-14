import os
import argparse
from datetime import datetime
from pathlib import Path

from google import genai
from PIL import Image, ImageOps, ImageEnhance


def preparar_imagen(ruta: Path, max_size: int = 1600) -> Image.Image:
    img = Image.open(ruta)
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")
    w, h = img.size
    scale = min(max_size / w, max_size / h, 1.0)
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)))
    img = ImageEnhance.Contrast(img).enhance(1.15)
    return img


def construir_prompt(nombre_archivo: str) -> str:
    return f"""
Analiza la imagen y conviértela en APUNTES en Markdown limpio.

REGLAS:
1) SOLO devuelve Markdown.
2) Usa # para títulos, ## para secciones, - para listas.
3) Fórmulas en LaTeX: inline $...$ y bloque $$...$$
4) Si hay código: usa bloques con lenguaje.
5) Si hay figuras/gráficas, añade al final:
   ## Figuras
   - Figura 1: descripción breve
   - ![Figura 1]({nombre_archivo})
6) Corrige errores OCR obvios. NO inventes contenido.

OBJETIVO: Crear una nota de estudio limpia y organizada.
""".strip()


EXTENSIONES_VALIDAS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}


def procesar_imagen(ruta_imagen: Path, out_dir: Path, curso: str | None = None, model_id: str = "gemini-2.5-flash", client: genai.Client | None = None) -> Path:
    propio_client = client is None
    if propio_client:
        client = genai.Client()

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        base = ruta_imagen.stem
        curso_slug = (curso or "sin_curso").strip().replace(" ", "_")
        carpeta = out_dir / curso_slug / f"{timestamp}_{base}"
        carpeta.mkdir(parents=True, exist_ok=True)

        img_out_name = "original.jpg"
        img_out_path = carpeta / img_out_name
        img = preparar_imagen(ruta_imagen)
        img.save(img_out_path, quality=92)

        prompt = construir_prompt(img_out_name)
        response = client.models.generate_content(
            model=model_id,
            contents=[prompt, img]
        )

        md_text = (response.text or "").strip()
        md_path = carpeta / "nota.md"
        md_path.write_text(md_text, encoding="utf-8")
    finally:
        if propio_client:
            client.close()

    return md_path


def procesar_carpeta(carpeta: Path, out_dir: Path, curso: str | None = None, model_id: str = "gemini-2.5-flash") -> list[Path]:
    imagenes = sorted(
        p for p in carpeta.iterdir()
        if p.is_file() and p.suffix.lower() in EXTENSIONES_VALIDAS
    )
    if not imagenes:
        raise SystemExit(f"No hay imágenes en: {carpeta}")

    client = genai.Client()
    rutas_md = []
    try:
        for i, ruta_imagen in enumerate(imagenes, start=1):
            print(f"[{i}/{len(imagenes)}] Procesando {ruta_imagen.name}...")
            try:
                md_path = procesar_imagen(ruta_imagen, out_dir, curso, model_id, client=client)
                rutas_md.append(md_path)
                print(f"  -> {md_path}")
            except Exception as e:
                print(f"  ! Error con {ruta_imagen.name}: {e}")
    finally:
        client.close()

    return rutas_md


def main():
    parser = argparse.ArgumentParser(description="Digitaliza apuntes desde imágenes usando Gemini.")
    parser.add_argument("imagen", type=str, help="Ruta de imagen o carpeta con imágenes")
    parser.add_argument("--out", type=str, default="notas", help="Carpeta de salida")
    parser.add_argument("--curso", type=str, default=None, help="Nombre del curso")
    parser.add_argument("--model", type=str, default="gemini-2.5-flash", help="Modelo Gemini")
    args = parser.parse_args()

    if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
        raise SystemExit("Falta la API KEY.\nexport GEMINI_API_KEY='TU_CLAVE'")

    ruta = Path(args.imagen)
    if not ruta.exists():
        raise SystemExit(f"No encuentro la ruta: {ruta}")

    if ruta.is_dir():
        rutas_md = procesar_carpeta(ruta, Path(args.out), args.curso, args.model)

        print("\n" + "=" * 50)
        print(f"✅ {len(rutas_md)} nota(s) creada(s):")
        for md_path in rutas_md:
            print(f"  - {md_path}")
        print("=" * 50)
    else:
        md_path = procesar_imagen(ruta, Path(args.out), args.curso, args.model)

        print("\n" + "=" * 50)
        print("✅ Nota creada:")
        print(md_path)
        print("=" * 50)
        print(md_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
