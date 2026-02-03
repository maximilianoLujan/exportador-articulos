import re
import unicodedata
from typing import Tuple

from rapidfuzz import fuzz


# =========================
# Normalización SIN comas
# =========================
def normalize(text: str) -> str:
    if not text:
        return ""

    text = text.upper().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")

    # OJO: NO borramos la coma acá
    text = re.sub(r"[.;:]", "", text)
    text = re.sub(r"\s+", " ", text)

    return text


# =========================
# Parsing correcto
# =========================
def split_name(text: str) -> Tuple[str, str]:
    text = normalize(text)

    if not text:
        return "", ""

    if "," in text:
        a, b = map(str.strip, text.split(",", 1))

        # normalizamos cada parte por separado
        a = a.replace(".", "")
        b = b.replace(".", "")

        # heurística: apellido suele ser más largo
        if len(a) >= len(b):
            return a, b
        else:
            return b, a

    parts = text.replace(".", "").split()
    if len(parts) == 1:
        return parts[0], ""

    # Sin coma el orden es ambiguo. Heurística:
    # - 2 tokens: asumimos que el apellido suele ser el token más "distintivo" (más largo).
    #   Esto hace el match invariante al orden para casos como "ILLESCAS GUSTAVO" vs "GUSTAVO ILLESCAS".
    # - >=3 tokens: intentamos "nombre(s) + apellido" (último token) salvo que el primer token
    #   parezca claramente más largo (posible "apellido + nombre(s)").
    if len(parts) == 2:
        a, b = parts
        if len(a) >= len(b):
            return a, b
        return b, a

    first = parts[0]
    last = parts[-1]
    if len(first) >= len(last) + 3:
        return first, " ".join(parts[1:])

    return last, " ".join(parts[:-1])


# =========================
# Iniciales
# =========================
def initials(name: str) -> str:
    return "".join(w[0] for w in name.split() if w)


# =========================
# Fuzzy
# =========================
def fuzzy_equal(a: str, b: str, threshold=85) -> bool:
    return fuzz.ratio(a, b) >= threshold


# =========================
# Comparación principal
# =========================
def same_person(name_a: str, name_b: str) -> bool:
    last_a, first_a = split_name(name_a)
    last_b, first_b = split_name(name_b)

    # Apellido: fuerte + fuzzy
    if not fuzzy_equal(last_a, last_b):
        # Fallback: si los tokens normalizados son los mismos (solo cambia el orden),
        # consideramos que es la misma persona.
        tokens_a = [t for t in normalize(name_a).replace(",", " ").split() if t]
        tokens_b = [t for t in normalize(name_b).replace(",", " ").split() if t]
        if len(tokens_a) >= 2 and sorted(tokens_a) == sorted(tokens_b):
            return True
        return False

    # Si alguno no tiene nombre → match
    if not first_a or not first_b:
        return True

    # Exacto
    if first_a == first_b:
        return True

    # Iniciales
    if initials(first_a) == initials(first_b):
        return True

    # Prefijo
    if first_a.startswith(first_b) or first_b.startswith(first_a):
        return True

    return False
