import json
import os
import re

import pdfplumber


def extraer_texto_pdf(pdf_path):
    paginas = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                paginas.append(t)
    return "\n".join(paginas)


OUT_PERSONAL = "personal_unidad_ejecutora.json"
OUT_ARTICULOS = "articulos.json"


def limpiar_texto(texto: str) -> str:
    # Quitar códigos tipo *10620240200033CE* o solos
    texto = re.sub(r"\*?\d{14,}\*?", " ", texto)

    # Quitar 'Página X de Y'
    texto = re.sub(r"Página\s+\d+\s+de\s+\d+", " ", texto)

    # Normalizar espacios
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def extraer_articulos(texto: str) -> list[str]:
    patron_bloque = re.compile(
        r"ARTICULOS Total:\s*\d+.*?Publicado Total publicado:\s*\d+(.*?)TRABAJOS EN EVENTOS C-T PUBLICADOS",
        re.DOTALL,
    )

    match = patron_bloque.search(texto)
    if not match:
        return []

    bloque = limpiar_texto(match.group(1))

    articulos = []

    # 1) Split primario SOLO por ISSN
    partes_issn = re.split(r"(ISSN\s*\d{4}-\d{3}[\dX])", bloque)

    buffer = ""

    for parte in partes_issn:
        if parte.startswith("ISSN"):
            buffer += " " + parte
            articulos.append(buffer.strip())
            buffer = ""
        else:
            buffer += " " + parte

    if buffer.strip():
        articulos.append(buffer.strip())

    resultado_final = []

    # 2) Fallback SOLO si el artículo NO tiene ISSN
    for art in articulos:
        if re.search(r"ISSN\s*\d{4}-\d{3}[\dX]", art):
            resultado_final.append(art.strip())
        else:
            # aplicar fallback por páginas
            subpartes = re.split(r"(p\.\s*\d+\s*-\s*\d+)", art)

            sub_buffer = ""
            for sp in subpartes:
                if re.fullmatch(r"p\.\s*\d+\s*-\s*\d+", sp):
                    sub_buffer += " " + sp
                    resultado_final.append(sub_buffer.strip())
                    sub_buffer = ""
                else:
                    sub_buffer += " " + sp

            if sub_buffer.strip():
                resultado_final.append(sub_buffer.strip())

    return resultado_final


def post_procesar_articulos(articulos: list[str]) -> list[str]:
    resultado = []

    # p. 1-1.  / p. 26871-26892.
    patron_fin = re.compile(r"(p\.\s*\d+\s*-\s*\d+\.)")

    # Inicio claro de nuevo artículo: APELLIDO, NOMBRE o NOMBRE APELLIDO;
    patron_inicio = re.compile(r"\s+[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\-]+,\s*[A-ZÁÉÍÓÚÑ]")

    for art in articulos:
        m_fin = patron_fin.search(art)

        if m_fin:
            fin = m_fin.end()
            resto = art[fin:]

            # SOLO cortar si después empieza otro artículo
            if patron_inicio.search(resto):
                resultado.append(art[:fin].strip())
                resultado.append(resto.strip())
                continue

        resultado.append(art.strip())

    return resultado


def guardar_json(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    # extraer textos de los pdfs en memorias/
    # leer la carpeta memorias/ y recorrer cada pdf

    for file in os.listdir("memorias/"):
        texto = extraer_texto_pdf("memorias/" + file)

        articulos = extraer_articulos(texto)
        articulos = post_procesar_articulos(articulos)

        nombre_archivo = file.strip().replace(".pdf", "")
        nombre_archivo = f"articulos_{nombre_archivo}.json"

        guardar_json(nombre_archivo, articulos)

        print(f"✔ Artículos extraídos de {file}: {len(articulos)} artículos")
        print(f"→ {nombre_archivo}")


if __name__ == "__main__":
    main()
