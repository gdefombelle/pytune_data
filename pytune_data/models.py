
from tortoise import fields, models
from tortoise.models import Model
from tortoise.contrib.fastapi import register_tortoise
from enum import IntEnum
import json
import numpy as np
from pydantic import BaseModel
from typing import List, Optional
from pydantic import BaseModel
from typing import Optional
from enum import Enum

# PyTune database orm classes and types

class PianoCategoryEnum(IntEnum):
    NONE = 0
    GRAND_PIANO = 1
    UPRIGHT_PIANO = 2


class UserStatusEnum(IntEnum):
    PENDING = 1
    EMAIL_CONFIRMED = 2
    REVOKED = 99

class ManufacturerStatus(IntEnum):
    PENDING = -1
    ACTIVE = 0
    ARCHIVED = 1

class PianoModelStatus(IntEnum):
    PENDING = -1
    ACTIVE = 0
    ARCHIVED = 1

class UserPianoStatus(IntEnum):
    PENDING = -1
    ACTIVE = 0
    ARCHIVED = 1

class ClientStatusEnum(IntEnum):
    UNDEFINED = -1
    FREE = 1
    PLAN_A = 2
    PLAN_B = 3
    PLAN_C = 4
    DB_PIANO_ADMIN = 98
    ADMIN = 99

class UserTypeEnum(IntEnum):
    UNDEFINED = -1
    INDIVIDUAL = 0
    PROFESSIONNAL = 1
    ADMIN = 99



class Manufacturer(Model):
    id = fields.IntField(pk=True, autoincrement=True)
    company = fields.CharField(max_length=60, unique=True, index=True)
    normalized_name = fields.CharField(max_length=255, null=True)  # Optionnel, calculé par la DB
    place = fields.CharField(max_length=120, null=True)  # Optionnel
    country = fields.CharField(max_length=50, null=True)  # Optionnel
    years_active = fields.CharField(max_length=50, null=True)  # Optionnel
    acquired_by = fields.TextField(null=True)  # Optionnel
    permanently_closed = fields.BooleanField(default=False)
    notes = fields.TextField(null=True)  # Optionnel
    wiki_url = fields.CharField(max_length=255, null=True)  # Optionnel
    piano_models = fields.ReverseRelation["PianoModel"]
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    
    # Champ pour le statut de l'enregistrement (créé par user, un crawler, etc .)
    status = fields.IntEnumField(ManufacturerStatus) 
    # créateur de l'enregistrement
    originated_by = fields.CharField(max_length=255, null=True)

    class Meta:
        table = 'manufacturer'
        unique_together = (('company', 'originated_by'),)  # Contrainte d'unicité sur les deux champs
    def __str__(self) -> str:
        return self.company



# Si vous avez un Enum pour les types de piano
class PianoCategoryEnum(Enum):
    GRAND = 1
    UPRIGHT = 2
    # Ajouter d'autres types si nécessaire


class PianoType(Model):
    id = fields.IntField(pk=True)
    category_id = fields.IntField()  # Référence à piano_categories (1 = Grand, 2 = Upright)
    subtype = fields.CharField(max_length=50)  # Sous-type (Spinet, Console, etc.)
    localized_name = fields.CharField(max_length=50)  # Nom localisé (français)
    min_size_cm = fields.IntField()  # Taille minimale en cm
    max_size_cm = fields.IntField(null=True)  # Taille maximale en cm (NULL si non applicable)
    size_inches = fields.CharField(max_length=20)  # Taille en inches pour affichage

    class Meta:
        table = "piano_types"

    def __str__(self):
        return f"{self.localized_name} ({self.size_inches})"

class ManufacturerSerialNumber(Model):
    """Table des numéros de série des pianos liés aux fabricants."""
    id = fields.IntField(pk=True)
    manufacturer = fields.ForeignKeyField(
        "models.Manufacturer", related_name="serial_numbers", on_delete=fields.CASCADE
    )
    serial_number = fields.CharField(max_length=50, unique=True)
    serial_number_int = fields.IntField()
    year = fields.IntField(null=True)  # Année de fabrication si dispo

    class Meta:
        table = "manufacturer_serial_numbers"

    def __str__(self):
        return f"{self.manufacturer.company} - {self.serial_number} ({self.year})"

class PianoSerialCache(Model):
    id = fields.IntField(pk=True)
    manufacturer_id = fields.IntField()
    serial_number = fields.CharField(max_length=50, unique=True)
    estimated_year = fields.IntField(null=True)
    explanation = fields.TextField(null=True)
    input_tokens = fields.IntField(default=0)
    output_tokens = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "piano_serial_cache"



class PianoModel(Model):
    id = fields.IntField(pk=True, autoincrement=True)
    manufacturer = fields.ForeignKeyField("models.Manufacturer", related_name="piano_models")
    name = fields.CharField(max_length=255)  # Ce champ est obligatoire
    serie = fields.CharField(max_length=255, null=True, default="")  # Champ optionnel
    kind = fields.IntEnumField(PianoCategoryEnum)  # Champ optionnel avec enum
    notes = fields.TextField(null=True, default="")  # Champ optionnel
    width_cm = fields.FloatField(default=0.0)  # Champ optionnel
    length_cm = fields.FloatField(default=0.0)  # Champ optionnel
    height_cm = fields.FloatField(default=0.0)  # Champ optionnel
    weight_kg = fields.FloatField(default=0.0)  # Champ optionnel
    str_length = fields.CharField(max_length=255, null=True, default="")  # Champ optionnel
    str_height = fields.CharField(max_length=255, null=True, default="")  # Champ optionnel
    str_weight = fields.CharField(max_length=255, null=True, default="")  # Champ optionnel
    keys = fields.IntField(default=88)  # Champ optionnel
    originated_by = fields.CharField(max_length=255, null=True, default=None)  # Champ optionnel
    status = fields.IntField(default=0)
    size = fields.FloatField(default=0.0) 
    piano_type = fields.ForeignKeyField("models.PianoType", related_name="pianomodel", null=True)  # Association avec piano_types
    class Meta:
        table = "pianomodel"  # Assurez-vous que le nom de la table correspond
        unique_together = (("name", "originated_by"),)  # Contrainte d'unicité sur le couple name, originated_by

    def __str__(self):
        return f"{self.name} - {self.manufacturer.company}"

class PianoImage(Model):
    id = fields.IntField(pk=True, autoincrement=True)
    manufacturer = fields.ForeignKeyField("models.Manufacturer", related_name="images", null=True, on_delete=fields.SET_NULL)
    serial_number = fields.CharField(max_length=50, null=True)
    model = fields.ForeignKeyField("models.PianoModel", related_name="images", null=True, on_delete=fields.SET_NULL)
    image_path = fields.CharField(max_length=255)  # Chemin vers le fichier
    uploaded_by = fields.ForeignKeyField("models.User", related_name="uploaded_images", null=True, on_delete=fields.SET_NULL)
    size_detected = fields.CharField(max_length=50, null=True)
    piano_type_detected = fields.CharField(max_length=50, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "piano_images"



class User(Model):
    id = fields.IntField(pk=True, autoincrement=True)
    pianos = fields.ReverseRelation["UserPianoModel"]
    sessions = fields.ReverseRelation["Session"]

    username = fields.CharField(max_length=255, unique=True, index=True)
    email = fields.CharField(max_length=255, unique=True, index=True)
    phone_number = fields.CharField(max_length=20, null=True)
    password = fields.CharField(max_length=255)
    status = fields.IntEnumField(UserStatusEnum)
    client_status = fields.IntEnumField(ClientStatusEnum)
    first_name = fields.CharField(max_length=255, null=True)
    last_name = fields.CharField(max_length=255, null=True)
    language = fields.CharField(max_length=8, default='en')
    timezone = fields.CharField(max_length=50, default='UTC')
    country = fields.CharField(max_length=50, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    last_connection = fields.DatetimeField(auto_now=True)
    user_type = fields.IntEnumField(UserTypeEnum, default=UserTypeEnum.INDIVIDUAL)

    # Champs supplémentaires
    location = fields.CharField(max_length=500, null=True)
    location_details = fields.JSONField(null=True)
    services_offered = fields.JSONField(null=True)
    additional_services = fields.TextField(null=True)
    business_name = fields.CharField(max_length=50, null=True)
    website = fields.CharField(max_length=255, null=True)
    history = fields.TextField(null=True)
    social_networks = fields.TextField(null=True)
    oauth_provider = fields.TextField(null=True)

    accepted_tos = fields.BooleanField(default=False)
    accepted_tos_at = fields.DatetimeField(null=True)
    accepted_privacy_policy = fields.BooleanField(default=False)
    accepted_privacy_policy_at = fields.DatetimeField(null=True)
    extra_data = fields.JSONField(null=True)
    class Config:
        from_attributes = True
    class Meta:
        table = 'user'

    def __str__(self) -> str:
        return self.first_name

class UserPianoModel(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="pianos")
    piano_model = fields.ForeignKeyField("models.PianoModel", related_name="pianomodel_user", null=True)
    name = fields.CharField(max_length=255, null=True)
    location = fields.CharField(max_length=255, null=True)
    purchase_year = fields.IntField(null=True)
    maintenance_log = fields.JSONField(null=True)
    
    # Champs JSON flexibles
    custom_data = fields.JSONField(null=True)
    extra_data = fields.JSONField(null=True)
    notes = fields.TextField(null=True) 
    # Nouveaux champs ajoutés pour les informations supplémentaires
    serial_number = fields.CharField(max_length=255, null=True)  # Numéro de série du piano
    manufacture_year = fields.IntField(null=True)  # Année de fabrication du piano

    class Meta:
        table = "pianomodel_user"
        unique_together = (("user", "piano_model"),)
    class Config:
        from_attributes = True

class Session(Model):
    id = fields.IntField(pk=True, autoincrement=True)
    user_id = fields.ForeignKeyField('models.User', 
                                     related_name='sessions',
                                     null=True,
                                     on_delete=fields.SET_NULL)
    piano_model = fields.ForeignKeyField("models.PianoModel")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    ip_adress = fields.CharField(max_length=40)
    # numerical data
    numeric_data = fields.JSONField()
    # Lists
    lists = fields.JSONField()

    # acoustic signals (NumPy arrays)
    acoustic_signals = fields.JSONField()
    
    class Config:
        from_attributes = True
    class Meta:
        table = "session"

    @property
    def numpy_acoustic_signals(self):
        if self.acoustic_signals is None:
            return None

        return np.frombuffer(json.loads(self.acoustic_signals), dtype=np.float64)

    @numpy_acoustic_signals.setter
    def numpy_acoustic_signals(self, value):
        if value is None:
            self.acoustic_signals = None
            return

        self.acoustic_signals = json.dumps(value.tobytes())

    def save_session(self, user_id, numeric_data, lists, acoustic_signals):
        self.user_id = user_id
        self.numeric_data = json.dumps(numeric_data)
        self.lists = json.dumps(lists)
        self.numpy_acoustic_signals = acoustic_signals
        self.save()

    def get_session_data(self):
        return {
            'numeric_data': json.loads(self.numeric_data),
            'lists': json.loads(self.lists),
            'acoustic_signals': self.numpy_acoustic_signals
        }



class OnlineUser(Model):
    user_email = fields.CharField(max_length=255, pk=True)
    platform = fields.CharField(max_length=50)
    last_seen = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "online_users"
        unique_together = ("user_email", "platform")

    class Config:
        from_attributes = True        




class UserContext(BaseModel):
    firstname: str
    form_completed: bool
    pianos: List[dict]  # ou une structure plus précise
    last_diagnosis_exists: bool
    tuning_session_exists: bool
    language: str


class ClientAPI(Model):
    """
    Modèle représentant les clients d'API pour le système d'autorisation OAuth.
    """
    id = fields.IntField(pk=True, autoincrement=True)
    client_id = fields.CharField(max_length=255, unique=True, index=True)  # Identifiant unique pour le client
    client_secret = fields.CharField(max_length=255, unique=True)  # Secret pour l'authentification du client
    redirect_uris = fields.JSONField(null=True, default=list)  # Utiliser une liste vide comme valeur par défaut
    client_name = fields.CharField(max_length=255)  # Nom de l'application cliente
    client_type = fields.CharField(max_length=50, default="confidential")  # Type du client (public ou confidentiel)
    scope = fields.CharField(max_length=255, default="read write")  # Scopes autorisés
    grant_types = fields.CharField(max_length=255, default="authorization_code")  # Types de grant supportés
    token_endpoint_auth_method = fields.CharField(max_length=50, default="client_secret_basic")  # Méthode d'authentification à la génération du token
    created_at = fields.DatetimeField(auto_now_add=True)  # Date de création du client
    updated_at = fields.DatetimeField(auto_now=True)  # Date de la dernière mise à jour
    contact_email = fields.CharField(max_length=255, null=True)  # Email de contact du client
    valid_until = fields.DatetimeField(null=True)  # Date d'expiration de l'accès à l'API
    class Meta:
        table = "client_api"
        
    class Config:
        from_attributes = True

    def __str__(self):
        return self.client_name

class Diagnosis(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="diagnoses", on_delete=fields.CASCADE)
    pianomodel_user = fields.ForeignKeyField("models.UserPianoModel", related_name="diagnoses", on_delete=fields.CASCADE)
    status = fields.IntField(default=0)  # Peut devenir un Enum plus tard
    data = fields.JSONField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "diagnosis"

class TuningSession(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="tuning_sessions", on_delete=fields.CASCADE)
    pianomodel_user = fields.ForeignKeyField("models.UserPianoModel", related_name="tuning_sessions", on_delete=fields.CASCADE)
    status = fields.IntField(default=0)  # Peut devenir un Enum plus tard
    data = fields.JSONField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "tuning_session"
