import asyncio
from typing import Dict, List, Optional
from tortoise import Tortoise
from tortoise.transactions import in_transaction
from tortoise.exceptions import DoesNotExist
from pytune_data.models import Manufacturer, ManufacturerSerialNumber, PianoModel, UserPianoModel
from pytune_data.schemas import (
    ManufacturerCreate, ManufacturerSerialNumberCreate, ManufacturerUpdate, ManufacturerInDB,
    PianoModelCreate, PianoModelUpdate, PianoModelInDB, UserManufacturerCreate,)
from tortoise.queryset import Q
from pytune_data.db import init, close
from unidecode import unidecode
from tortoise.expressions import Q
from tortoise.functions import Function
from rapidfuzz.fuzz import partial_ratio
from tortoise import Tortoise



async def get_all_normalized_brands() -> List[str]:
    """
    Retourne la liste de toutes les marques de piano connues,
    sous forme de noms normalisés, sans doublons ni valeurs nulles.
    """
    await init()
    conn = Tortoise.get_connection("default")

    rows = await conn.execute_query(
        """
        SELECT DISTINCT normalized_name
        FROM manufacturer
        WHERE normalized_name IS NOT NULL
        ORDER BY normalized_name ASC
        """
    )
    # rows[1] contient les résultats ; rows[0] est la description
    brand_list = [row[0] for row in rows[1] if row[0]]
    return brand_list



async def get_manufacturers():
    await init()
    return await Manufacturer.all()

async def get_manufacturer_by_id(manufacturer_id :int):
    await init()
    return await Manufacturer.get(id=manufacturer_id)

# Fonction pour rechercher un fabricant par nom
async def search_manufacturer(query: str, email: str):
    normalized_query = unidecode(query)
    await init()

    # Construction de la requête SQL avec la condition demandée
    manufacturers = await Tortoise.get_connection("default").execute_query(
        """
        SELECT * 
        FROM manufacturer
        WHERE normalized_name % $1
        AND (originated_by IS NULL OR originated_by = $2 OR originated_by = "llm")
        LIMIT 10
        """, 
        [normalized_query, email]
    )

    return manufacturers[1]

async def search_manufacturer_full(query: str, email: Optional[str]) -> List[Dict]:
    await init()
    normalized_query = unidecode(query).lower()

    sql = """
    SELECT id, company, normalized_name, place, country,
           similarity(normalized_name, $1) AS score
    FROM manufacturer
    WHERE normalized_name % $1
    AND (originated_by IS NULL OR originated_by = $2 OR originated_by ='llm')
    ORDER BY score DESC
    LIMIT 10
    """
    rows = await Tortoise.get_connection("default").execute_query(sql, [normalized_query, email])
    manufacturers = rows[1]

    return [
        {
            "id": r["id"],
            "company": r["company"],
            "normalized_name": r["normalized_name"],
            "place": r["place"],
            "country": r["country"],
            "score": round(r["score"], 3),
        }
        for r in manufacturers
    ]


async def search_model_full(query: str, manufacturer_id: int, email: Optional[str]) -> List[Dict]:
    await init()
    normalized_query = unidecode(query).lower().replace('-', '').replace('_', '').replace(' ', '')

    sql = """
    SELECT id, name, normalized_name, kind,
           width_cm, length_cm, height_cm,
           notes, serie, str_length, str_height,
           keys, size_cm,
           piano_type_id, piano_type,
           similarity(normalized_name, $1) AS score
    FROM pianomodel
    WHERE manufacturer_id = $2
      AND normalized_name % $1
    ORDER BY score DESC
    LIMIT 10
    """

    rows = await Tortoise.get_connection("default").execute_query(sql, [normalized_query, manufacturer_id])
    models = rows[1]

    return [
        {
            "id": r["id"],
            "name": r["name"],
            "normalized_name": r["normalized_name"],
            "notes": r["notes"],
            "kind": r["kind"],
            "width_cm": r["width_cm"],
            "length_cm": r["length_cm"],
            "height_cm": r["height_cm"],
            "serie": r["serie"],
            "str_length": r["str_length"],
            "str_height": r["str_height"],
            "keys": r["keys"],
            "size_cm": r["size_cm"],
            "piano_type_id": r["piano_type_id"],
            "piano_type": r["piano_type"],
            "score": round(r["score"], 3),
        }
        for r in models
    ]


async def search_piano_model(query: str, email: str, manufacturer_id: int):
    # Normaliser la chaîne de recherche pour supprimer les accents et préparer la recherche
    normalized_query = unidecode(query).lower()  # Conversion en minuscule pour rendre la recherche insensible à la casse

    # Assure-toi d'initialiser la connexion à la base de données
    await init()

    # Construction de la requête SQL avec la condition demandée
    piano_models = await Tortoise.get_connection("default").execute_query(
        """
        SELECT * 
        FROM pianomodel
        WHERE LOWER(name) LIKE $1  -- Recherche insensible à la casse sur le nom du modèle
        AND manufacturer_id = $2
        AND (originated_by IS NULL OR originated_by = $3)
        LIMIT 10
        """, 
        [f"{normalized_query}%", manufacturer_id, email]  # Utilisation de % pour chercher à partir de la première lettre
    )

    return piano_models


# Fonction pour récupérer tous les modèles de piano d'un fabricant
async def get_piano_models_by_manufacturer(manufacturer_id: int, email: str = None) -> List[PianoModel]:
    await init()
    manufacturer = await Manufacturer.get(id=manufacturer_id)
    
    # Récupérer tous les modèles
    result = await manufacturer.piano_models.all()
    
    # Filtrer en fonction de `originated_by`
    if email is not None:
        result = [piano for piano in result if piano.originated_by == email or piano.originated_by is None]
    else:
        result = [piano for piano in result if piano.originated_by is None]
    
    return result

# Fonction pour récupérer un modèle de piano spécifique
async def get_piano_model(model_id: int):
    await init()
    return await PianoModel.get(id=model_id)

async def get_closed_manufacturers():
    await init()
    return await Manufacturer.filter(permanently_closed=True)

async def get_still_active_manufacturers():
    await init()
    return await Manufacturer.filter(permanently_closed=False)
        
async def create_manufacturer(manufacturer: ManufacturerCreate) -> ManufacturerInDB:
    await init()
    db_manufacturer = Manufacturer(**manufacturer.model_dump())
    await db_manufacturer.save()
    return ManufacturerInDB.model_validate(db_manufacturer)

async def create_user_manufacturer(manufacturer: UserManufacturerCreate) -> ManufacturerInDB:
    await init()

    # Crée une instance de Manufacturer à partir des données reçues
    db_manufacturer = Manufacturer(**manufacturer.model_dump())
    
    # Sauvegarde le fabricant dans la base de données
    await db_manufacturer.save()

    # Convertit l'objet db_manufacturer en un dictionnaire avec model_dump
   # Convertit l'objet db_manufacturer en un dictionnaire avec to_dict() (Tortoise ORM)
    manufacturer_dict = db_manufacturer.__dict__ 

    # Valide et transforme le dictionnaire en ManufacturerInDB
    manufacturer_in_db =  ManufacturerInDB(**manufacturer_dict)
    return manufacturer_in_db


async def create_user_piano_model(piano_model: PianoModelCreate, email:str = None) -> PianoModelInDB:
    await init()
    db_piano_model = PianoModel(**piano_model.model_dump())
    await db_piano_model.save()

    piano_model_dict = db_piano_model.__dict__
    piano_model_in_db = PianoModelInDB(**piano_model_dict)
    return piano_model_in_db

async def generate_unique_piano_name(user_id: int, manufacturer_name: str, piano_model_name: str) -> str:
    """
    Fonction pour générer un nom unique pour un piano en cas de duplication.
    Le nom sera sous la forme de : 'ManufacturerName ModelName (i)', où 'i' est un suffixe unique.
    """
    # Combine le nom du fabricant et le modèle de piano
    combined_name = f"{manufacturer_name} {piano_model_name}"
    
    # Recherche des pianos existants pour cet utilisateur, dont le nom commence par le nom combiné
    existing_pianos = await UserPianoModel.filter(user_id=user_id, name__startswith=combined_name).all()

    if not existing_pianos:
        # Si aucun piano de ce modèle n'existe, utiliser le nom combiné sans suffixe
        return combined_name
    
    # Trouver le plus grand suffixe existant et l'incrémenter
    suffix = 1
    for piano in existing_pianos:
        if piano.name.endswith(f"({suffix})"):
            suffix += 1
    
    # Retourner le nom avec le suffixe
    return f"{combined_name} ({suffix})"

async def add_piano_to_user(user_id: int, piano_model_id: int, name: Optional[str] = None):
    # Récupère le modèle de piano
    await init()
    piano_model = await PianoModel.get(id=piano_model_id)
    
    # Si aucun nom n'est donné, génère un nom unique par défaut
    if not name:
        name = await generate_unique_piano_name(user_id, piano_model.name)
    
    # Crée le nouvel enregistrement dans la table pianomodel_user
    new_piano = await UserPianoModel.create(
        user_id=user_id,
        piano_model_id=piano_model_id,
        name=name,  # Utilisation du nom généré
        location = ""
        # Autres champs comme location, purchase_year, etc.
    )
    
    return new_piano

async def update_manufacturer(manufacturer_id: int, manufacturer: ManufacturerUpdate) -> ManufacturerInDB:
    await init()
    db_manufacturer = await Manufacturer.get(id=manufacturer_id)
    await db_manufacturer.update_from_dict(manufacturer.model_dump())
    await db_manufacturer.save()
    return ManufacturerInDB.model_validate(db_manufacturer)

async def update_piano_model(piano_model_id: int, piano_model: PianoModelUpdate) -> PianoModelInDB:
    await init()
    db_piano_model = await PianoModel.get(id=piano_model_id)
    await db_piano_model.update_from_dict(piano_model.model_dump())
    await db_piano_model.save()
    return PianoModelInDB.model_validate(db_piano_model)

async def insert_serial_numbers(manufacturer_id: int, serial_numbers: List[ManufacturerSerialNumberCreate]):
    """Insère plusieurs numéros de série en base."""
    
    # ✅ Conversion des objets Pydantic en dictionnaires exploitables
    serial_data = [
        {
            "manufacturer_id": manufacturer_id,
            "serial_number": serial.serial_number,
            "year": serial.year
        }
        for serial in serial_numbers
    ]

    # ✅ Insérer tous les numéros de série en une seule requête pour améliorer les performances
    await ManufacturerSerialNumber.bulk_create([
        ManufacturerSerialNumber(**data) for data in serial_data
    ])

    from tortoise import Tortoise

# Fonction pour récupérer le type de piano (ex: Studio, Demi-queue) en fonction de la catégorie et de la taille
async def get_piano_type_by_category_and_size(
    size_cm: int,
    category_id: int = None,
    category_name: str = None,
):
    await init()

    if category_id is not None:
        sql = """
            SELECT 
                pt.subtype AS type_en,
                pt.localized_name AS type_fr,
                pt.min_size_cm,
                pt.max_size_cm
            FROM piano_types pt
            WHERE pt.category_id = $1
              AND $2 BETWEEN pt.min_size_cm AND pt.max_size_cm
            LIMIT 1
        """
        params = [category_id, size_cm]

    elif category_name is not None:
        sql = """
            SELECT 
                pt.subtype AS type_en,
                pt.localized_name AS type_fr,
                pt.min_size_cm,
                pt.max_size_cm
            FROM piano_types pt
            JOIN piano_categories pc ON pt.category_id = pc.id
            WHERE pc.name = $1
              AND $2 BETWEEN pt.min_size_cm AND pt.max_size_cm
            LIMIT 1
        """
        params = [category_name, size_cm]

    else:
        raise ValueError("You must provide either category_id or category_name.")

    result = await Tortoise.get_connection("default").execute_query(sql, params)
    return result[1][0] if result[1] else None
