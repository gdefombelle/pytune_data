import re
from typing import Optional, Set
from unidecode import unidecode
from typing import Optional
from pytune_data.db import init
from pytune_data.models import KIND_SYNONYMS, PianoModel, PianoType


def extract_model_keys(text: str) -> Set[str]:
    """Extrait des clés comparables à partir d'un libellé de modèle utilisateur ou DB"""
    if not text:
        return set()
    text = text.lower()
    text = re.sub(r'\([^)]*\)', ' ', text)          # supprime (info)
    text = re.sub(r'[\"”“]', '', text)              # supprime guillemets
    parts = re.split(r'[\/,;|]', text)              # coupe sur / ; ,

    keys = set()
    for part in parts:
        part = part.strip()
        if not part:
            continue
        compact = re.sub(r'[^a-z0-9]+', '', part)   # garde a-z0-9
        if compact and len(compact) >= 1:
            keys.add(compact)
        # ajoute aussi les groupes alphanum utiles (ex: c3x)
        keys.update(re.findall(r'[a-z]+[0-9]+|[0-9]+[a-z]+', compact))
    return keys

async def resolve_model(manufacturer_id: int, raw_label: str) -> Optional[int]:
    """Trouve le pianomodel.id le plus probable pour un fabricant donné et un libellé utilisateur."""
    if not manufacturer_id or not raw_label:
        return None

    target_keys = extract_model_keys(raw_label)
    if not target_keys:
        return None

    # Récupération des modèles pour ce fabricant (avec name et normalized_name)
    candidates = await PianoModel.filter(manufacturer_id=manufacturer_id).values("id", "name", "normalized_name")

    best_id = None
    best_score = 0

    for row in candidates:
        name = row.get("normalized_name") or row.get("name") or ""
        model_keys = extract_model_keys(name)

        intersection = target_keys & model_keys
        if intersection:
            score = len(intersection) / max(len(target_keys), 1)
            if score > best_score:
                best_score = score
                best_id = row["id"]

    return best_id

def resolve_kind_id(kind: Optional[str]) -> Optional[int]:
    if not kind:
        return None
    label = kind.strip().lower()
    label = label.replace("piano", "").strip()
    enum_value = KIND_SYNONYMS.get(label)
    return int(enum_value) if enum_value is not None else None



def normalize_label(label: str) -> str:
    return label.strip().lower().replace("-", " ")

import re
from unidecode import unidecode

def normalize_piano_model_name(name: str) -> str:
    """
    Normalize a piano model name for DB matching.
    Examples:
      'CX-3'   -> 'cx3'
      'C 3 X'  -> 'c3x'
      'b-211'  -> 'b211'
      'U1 H'   -> 'u1h'
    """
    if not name:
        return ""

    s = unidecode(name)
    s = s.lower()
    s = re.sub(r'[^a-z0-9]', '', s)  # 🔑 supprime TOUT sauf lettres/chiffres
    return s


async def resolve_piano_type_id(
    kind_id: Optional[int],
    piano_type_label: Optional[str],
    size_cm: Optional[float]
) -> Optional[int]:
    """
    Résout le piano_type.id à partir de :
    - kind_id (obligatoire)
    - piano_type_label (libellé texte, prioritaire)
    - size_cm (en fallback si le label ne donne rien)
    """
    if not kind_id:
        return None

    # --- Stratégie 1 : par libellé
    if piano_type_label:
        label_norm = normalize_label(piano_type_label)
        candidates = await PianoType.filter(category_id=kind_id).values("id", "subtype", "localized_name")
        for row in candidates:
            if normalize_label(row["subtype"]) == label_norm:
                return row["id"]
            if normalize_label(row["localized_name"]) == label_norm:
                return row["id"]

    # --- Stratégie 2 : par taille
    if size_cm and size_cm > 0:
        pt = await PianoType.filter(
            category_id=kind_id,
            min_size_cm__lte=size_cm,
            max_size_cm__gte=size_cm
        ).first()
        if pt:
            return pt.id

    return None

async def create_piano_model_from_llm(
    *,
    manufacturer_id: int,
    model_name: str,
    kind_label: Optional[str],
    size_cm: Optional[int],
    piano_type_label: Optional[str] = None,
    notes: Optional[str] = None,
    originated_by: str = "llm",
) -> PianoModel:
    """
    Create a PianoModel entry from LLM-resolved data.
    """

    await init()


    # ─────────────────────────────────────────────
    # Normalize model name
    # ─────────────────────────────────────────────
    normalized_name = normalize_piano_model_name(model_name)
    display_name = model_name.strip().upper()


    # ─────────────────────────────────────────────
    # Resolve kind (category)
    # ─────────────────────────────────────────────
    kind_id = resolve_kind_id(kind_label)
    
    existing = await PianoModel.filter(
            manufacturer_id=manufacturer_id,
            normalized_name=normalized_name,
            kind=kind_id,
        ).first()

    if existing:
        return existing

    # ─────────────────────────────────────────────
    # Normalize size (INT, SAFE)
    # ─────────────────────────────────────────────
    size_cm_int: int = int(size_cm) if size_cm is not None else 0

    # ─────────────────────────────────────────────
    # Resolve piano_type_id (label > size)
    # ─────────────────────────────────────────────
    piano_type_id = await resolve_piano_type_id(
        kind_id=kind_id,
        piano_type_label=piano_type_label,
        size_cm=size_cm_int,
    )

    # ─────────────────────────────────────────────
    # Map size to physical dimensions
    # ─────────────────────────────────────────────
    length_cm = 0
    height_cm = 0

    if kind_id == 1 and size_cm_int > 0:       # grand
        length_cm = size_cm_int
    elif kind_id == 2 and size_cm_int > 0:     # upright
        height_cm = size_cm_int

    # ─────────────────────────────────────────────
    # Create DB object
    # ─────────────────────────────────────────────
    db_model = PianoModel(
        manufacturer_id=manufacturer_id,
        name=display_name,
        normalized_name=normalized_name,
        kind=kind_id,
        size_cm=size_cm_int,
        length_cm=length_cm,
        height_cm=height_cm,
        piano_type_id=piano_type_id,
        notes=notes or "",
        originated_by=originated_by,
    )

    await db_model.save()
    return db_model