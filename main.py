import json
import re

import pdfplumber


def extraer_datos_memoria(pdf_path):
    datos = {}
    with pdfplumber.open(pdf_path) as pdf:
        # Extraer tablas (como la lista de personal o presupuestos)
        todas_las_tablas = []
        for page in pdf.pages:
            tablas_pag = page.extract_tables()
            if tablas_pag:
                todas_las_tablas.extend(tablas_pag)

        datos["tablas_extraidas"] = todas_las_tablas
    return datos


data = extraer_datos_memoria("memoriaINTIA_2024.pdf")

# --- 2. CONFIGURACIÓN Y ESTRUCTURAS ---

output_json = {
    "nodos": {
        "miembros_instituto": set(),
        "colaboradores": set(),  # Autores que no son miembros
        "titulos": set(),  # Grado, Doctorado, Maestría
        "entidades": set(),  # Instituciones
        "convenios": [],
        "articulos_congresos_nacionales": [],
        "articulos_congresos_internacionales": [],
        "articulos_revistas_nacionales": [],
        "articulos_revistas_internacionales": [],
        "libros": [],
        "capitulos_libros": [],
        "articulos_libros": [],  # Si hubiera
    },
    "arcos": [],  # Lista de diccionarios {origen, destino, relacion, año}
}

# Palabras clave para detectar ámbito Nacional vs Internacional
KEYWORDS_NACIONAL = [
    "Argentina",
    "Buenos Aires",
    "Nacional",
    "Local",
    "CABA",
    "Tandil",
    "La Plata",
    "Córdoba",
    "Catamarca",
]
KEYWORDS_INTERNACIONAL = [
    "International",
    "IEEE",
    "World",
    "Latinoamericano",
    "ACM",
    "Springer",
    "Elsevier",
    "España",
    "Mexico",
    "Chile",
    "Perú",
    "USA",
]

# --- 3. FUNCIONES DE AYUDA ---


def limpiar_nombre(nombre_raw):
    """Normaliza nombres: 'VAZQUEZ, MARTIN' -> 'VAZQUEZ, MARTIN'"""
    if not nombre_raw:
        return ""
    # Quitar caracteres raros y espacios extra
    nombre = nombre_raw.replace("\n", " ").strip().upper()
    # A veces vienen como 'Apellido, Nombre'. Intentamos mantener ese formato.
    return nombre


def detectar_ambito(texto):
    """Determina si es Nacional o Internacional basado en palabras clave."""
    texto_upper = texto.upper()
    score_nac = sum(1 for w in KEYWORDS_NACIONAL if w.upper() in texto_upper)
    score_int = sum(1 for w in KEYWORDS_INTERNACIONAL if w.upper() in texto_upper)

    if score_int > 0:
        return "Internacional"
    if score_nac > 0:
        return "Nacional"
    return "Internacional"  # Por defecto ante duda en publicaciones científicas


def extraer_anio(texto):
    """Busca un año en el texto."""
    match = re.search(r"20[0-9][0-9]", texto)
    return match.group(0) if match else "Indefinido"


# --- 4. LÓGICA DE PARSEO ---

# A. EXTRACCIÓN DE MIEMBROS DEL INSTITUTO
try:
    # Buscamos la tabla que tiene el personal (Sabemos que es la primera en tu data)
    raw_members = data["tablas_extraidas"][0][1][0]
    lista_miembros = [limpiar_nombre(m) for m in raw_members.split("\n") if len(m) > 3]
    output_json["nodos"]["miembros_instituto"].update(lista_miembros)
except Exception as e:
    print(f"Error extrayendo miembros: {e}")

miembros_set = output_json["nodos"]["miembros_instituto"]

# B. EXTRACCIÓN DE PRODUCCIÓN CIENTÍFICA (Artículos y Congresos)
# Recorremos las tablas buscando secciones de producción
for tabla in data["tablas_extraidas"]:
    header = tabla[0][0] if tabla[0] else ""

    tipo_publicacion = None
    if "ARTICULOS" in header:
        tipo_publicacion = "Revista"
    elif "EVENTOS" in header:
        tipo_publicacion = "Congreso"

    if tipo_publicacion:
        # Iterar filas de la tabla (saltando el header)
        for row in tabla[1:]:
            contenido = row[0]
            if not contenido or len(contenido) < 10:
                continue

            # Limpieza básica
            contenido = contenido.replace("\n", " ")

            # Detección de Año y Ambito
            anio = extraer_anio(contenido)
            ambito = detectar_ambito(contenido)

            # Extracción de Autores (Heurística: Nombres en mayúsculas al inicio separados por ;)
            # Regex: Busca nombres en mayuscula al principio hasta que encuentra titulo (Minúsculas)
            autores_match = re.match(r"^([A-ZÁÉÍÓÚÑ\s,;.]+)(?=[A-Z][a-z])", contenido)

            autores_detectados = []
            titulo_pub = "Publicación sin título detectado"

            if autores_match:
                raw_autores = autores_match.group(1)
                titulo_pub = (
                    contenido[len(raw_autores) :].strip()[:50] + "..."
                )  # Recortar título

                # Separar autores por ';' o ',' o ' y '
                lista_autores = re.split(r"[;]|\sy\s", raw_autores)
                for aut in lista_autores:
                    aut_limpio = limpiar_nombre(aut)
                    if len(aut_limpio) > 4:  # Filtro ruido
                        autores_detectados.append(aut_limpio)

            # CLASIFICACIÓN Y GENERACIÓN DE ARCOS
            categoria_key = ""
            if tipo_publicacion == "Congreso":
                categoria_key = f"articulos_congresos_{ambito.lower()}es"  # nacionales/internacionales
            else:
                categoria_key = f"articulos_revistas_{ambito.lower()}es"

            # Guardar el nodo de publicación (usamos el título o un ID generado)
            output_json["nodos"][categoria_key].append(titulo_pub)

            # Generar Arcos: Publicación -> Autor
            for autor in autores_detectados:
                # Verificar si es miembro o colaborador
                es_miembro = False
                # Búsqueda difusa simple (si el apellido está en miembros)
                for miembro in miembros_set:
                    if autor in miembro or miembro in autor:
                        es_miembro = True
                        autor = miembro  # Normalizar al nombre del miembro
                        break

                if not es_miembro:
                    output_json["nodos"]["colaboradores"].add(autor)

                output_json["arcos"].append(
                    {
                        "origen": titulo_pub,
                        "destino": autor,
                        "relacion": "Autoría",
                        "categoria": categoria_key,
                        "año": anio,
                    }
                )

# C. EXTRACCIÓN DE TESIS (Miembro -> Título)
# Buscamos secciones de "DIRECCION DE TESIS"
current_degree = None
for tabla in data["tablas_extraidas"]:
    header = tabla[0][0] if tabla[0] else ""

    if "TESIS DE GRADO" in header:
        current_degree = "Tesis de Grado"
    elif "DOCTORADO" in header:
        current_degree = "Tesis de Doctorado"
    elif "MAESTRIA" in header:
        current_degree = "Tesis de Maestría"
    elif "BECAS" in header:
        current_degree = None  # Ignoramos becas por ahora si solo pide Títulos

    if current_degree:
        output_json["nodos"]["titulos"].add(current_degree)

        for row in tabla[1:]:
            contenido = row[0]
            if not contenido or "Total:" in contenido:
                continue

            # Regex para buscar "Director o tutor [NOMBRE]"
            match_director = re.search(
                r"(?:Director o tutor|Co-director o co-tutor)\s+([A-ZÁÉÍÓÚÑ, ]+)",
                contenido,
            )
            anio = extraer_anio(contenido)

            if match_director:
                director_raw = match_director.group(1).strip()
                # Limpiar nombre del director (sacar posibles residuos)
                director = director_raw.split("\n")[0]

                # Validar que sea un miembro
                for miembro in miembros_set:
                    if director in miembro:
                        director = miembro
                        break

                # Crear Arco: Miembro -> Título (según pedido)
                output_json["arcos"].append(
                    {
                        "origen": director,
                        "destino": current_degree,
                        "relacion": "Dirección",
                        "categoria": "Titulo_Academico",
                        "año": anio,
                    }
                )

# D. EXTRACCIÓN DE ENTIDADES Y CONVENIOS
# Buscamos en proyectos y extension
for tabla in data["tablas_extraidas"]:
    # Aplanamos el contenido para buscar keywords
    texto_bloque = " ".join([str(celda) for fila in tabla for celda in fila if celda])

    # Entidades colaboradoras (Buscamos "Institución/es:")
    if "Institución/es:" in texto_bloque:
        # Regex para capturar lo que sigue a Institución/es:
        match_inst = re.findall(
            r"Institución/es:\s*(.*?)(?=\sEjecuta:)", texto_bloque, re.DOTALL
        )
        anio = extraer_anio(texto_bloque)
        for inst in match_inst:
            entidades = inst.replace("\n", " ").split(";")
            for ent in entidades:
                ent_clean = ent.strip()
                if (
                    len(ent_clean) > 3
                    and "UNIVERSIDAD NACIONAL DEL CENTRO" not in ent_clean
                ):
                    output_json["nodos"]["entidades"].add(ent_clean)
                    # Aquí podrías crear un arco Miembro -> Entidad si pudieras vincular el director del proyecto

    # Convenios
    if "Convenio" in texto_bloque and "EXTENSION" in str(tabla[0]):
        # Extraer nombre del convenio
        match_conv = re.search(r"(Convenio.*?)(\.|,|\n)", texto_bloque)
        if match_conv:
            convenio_nombre = match_conv.group(1)
            output_json["nodos"]["convenios"].append(convenio_nombre)
            # Buscar el organizador
            match_org = re.search(
                r"Organizador o coordinador\s*,?\s*([A-Z, ]+)", texto_bloque
            )
            if match_org:
                organizador = match_org.group(1).strip()
                # Validar miembro
                for m in miembros_set:
                    if organizador in m:
                        organizador = m
                        break

                output_json["arcos"].append(
                    {
                        "origen": organizador,
                        "destino": convenio_nombre,
                        "relacion": "Coordinación",
                        "categoria": "Convenio",
                        "año": extraer_anio(texto_bloque),
                    }
                )

# --- 5. CONVERSIÓN FINAL A JSON SERIALIZABLE ---
# Convertir sets a listas para JSON
final_output = {
    "nodos": {k: list(v) for k, v in output_json["nodos"].items()},
    "arcos": output_json["arcos"],
}

# Imprimir resultado (o guardarlo en archivo)
with open("output_memoria.json", "w", encoding="utf-8") as f:
    json.dump(final_output, f, indent=2, ensure_ascii=False)
