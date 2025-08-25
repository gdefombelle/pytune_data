import re
from typing import Optional, Set
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
    return KIND_SYNONYMS.get(label)


def normalize_label(label: str) -> str:
    return label.strip().lower().replace("-", " ")


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
