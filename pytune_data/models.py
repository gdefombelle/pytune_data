
from datetime import datetime
from uuid import uuid4
from tortoise import fields, models
from tortoise.models import Model
from tortoise.contrib.fastapi import register_tortoise
from enum import IntEnum
import json
import numpy as np
from pydantic import BaseModel
from typing import Dict, List, Optional
from pydantic import BaseModel
from typing import Optional
from enum import Enum

from pytune_data.db import init

# PyTune database orm classes and types

# class PianoCategoryEnum(IntEnum):
#     NONE = 0
#     GRAND_PIANO = 1
#     UPRIGHT_PIANO = 2


class UserStatusEnum(IntEnum):
    PENDING = 1                 # signup fait, email envoyé
    EMAIL_CONFIRMED = 2         # lien validé
    EMAIL_BOUNCED = 3           # ❌ adresse invalide (bounce)
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

class PianoCategoryEnum(IntEnum):
    GRAND = 1
    UPRIGHT = 2
    # Ajouter d'autres types si nécessaire

class DiagnosisSessionStatus(IntEnum):
    CREATED = 0        # juste créée, pas encore démarrée
    RUNNING = 1        # en cours (notes qui arrivent)
    FINISHED = 2       # terminée proprement
    CANCELLED = 3      # annulée par l'utilisateur
    ERROR = 99         # plantée / interrompue

KIND_SYNONYMS = {
    "grand": PianoCategoryEnum.GRAND,
    "horizontal": PianoCategoryEnum.GRAND,
    "upright": PianoCategoryEnum.UPRIGHT,
    "vertical": PianoCategoryEnum.UPRIGHT,
}


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
# models/piano_model.py (ou fichier équivalent)

class PianoModel(Model):
    id = fields.IntField(pk=True, autoincrement=True)

    manufacturer = fields.ForeignKeyField(
        "models.Manufacturer", related_name="piano_models"
    )

    name = fields.CharField(max_length=255)
    normalized_name = fields.CharField(max_length=255, null=True)
    serie = fields.CharField(max_length=255, null=True, default="")
    kind = fields.IntEnumField(PianoCategoryEnum)
    notes = fields.TextField(null=True, default="")

    width_cm = fields.FloatField(default=0.0)
    length_cm = fields.FloatField(default=0.0)
    height_cm = fields.FloatField(default=0.0)
    weight_kg = fields.FloatField(default=0.0)

    str_length = fields.CharField(max_length=255, null=True, default="")
    str_height = fields.CharField(max_length=255, null=True, default="")
    str_weight = fields.CharField(max_length=255, null=True, default="")

    keys = fields.IntField(default=88)
    originated_by = fields.CharField(max_length=255, null=True, default=None)
    status = fields.IntField(default=0)

    # ✅ ALIGNÉ DB / ORM
    size_cm = fields.IntField(default=0, db_column="size_cm")

    @property
    def size(self) -> int:
        return self.size_cm or 0

    @size.setter
    def size(self, v: int):
        self.size_cm = int(v)

    piano_type = fields.ForeignKeyField(
        "models.PianoType",
        related_name="pianomodel",
        null=True
    )

    class Meta:
        table = "pianomodel"
        unique_together = (("name", "originated_by"),)

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

    # Relations existantes
    pianos = fields.ReverseRelation["UserPianoModel"]
    sessions = fields.ReverseRelation["Session"]

    # Auth / identité
    username = fields.CharField(max_length=255, unique=True, index=True)
    email = fields.CharField(max_length=255, unique=True, index=True)
    phone_number = fields.CharField(max_length=20, null=True)
    password = fields.CharField(max_length=255)

    status = fields.IntEnumField(UserStatusEnum)
    client_status = fields.IntEnumField(ClientStatusEnum)
    user_type = fields.IntEnumField(UserTypeEnum, default=UserTypeEnum.INDIVIDUAL)

    first_name = fields.CharField(max_length=255, null=True)
    last_name = fields.CharField(max_length=255, null=True)

    # 🌍 Locale
    language = fields.CharField(max_length=8, default='en')
    timezone = fields.CharField(max_length=50, default='UTC')
    country = fields.CharField(max_length=50, null=True)

    # 🕒 Dates
    created_at = fields.DatetimeField(auto_now_add=True, timezone=True)
    updated_at = fields.DatetimeField(auto_now=True, timezone=True)
    last_connection = fields.DatetimeField(null=True, timezone=True)

    # 🧾 Abonnement (NOUVEAU)
    plan_code = fields.CharField(max_length=50, default="freemium")
    role = fields.CharField(max_length=50, default="individual")
    plan_started_at = fields.DatetimeField(auto_now_add=True)
    plan_ends_at = fields.DatetimeField(null=True)

    # 🧑‍🔧 Profil pro / extended
    location = fields.CharField(max_length=500, null=True)
    location_details = fields.JSONField(null=True)
    services_offered = fields.JSONField(null=True)
    additional_services = fields.TextField(null=True)
    business_name = fields.CharField(max_length=50, null=True)
    website = fields.CharField(max_length=255, null=True)
    history = fields.TextField(null=True)
    social_networks = fields.TextField(null=True)
    oauth_provider = fields.TextField(null=True)

    # ✅ Legal
    accepted_tos = fields.BooleanField(default=False)
    accepted_tos_at = fields.DatetimeField(null=True, timezone=True)
    accepted_privacy_policy = fields.BooleanField(default=False)
    accepted_privacy_policy_at = fields.DatetimeField(null=True, timezone=True)

    extra_data = fields.JSONField(null=True)

    # 🔐 RBAC / Subscription (relations inverses)
    entitlements: fields.ReverseRelation["UserEntitlement"]
    quotas: fields.ReverseRelation["UserQuota"]
    plan_history: fields.ReverseRelation["UserPlanHistory"]

    class Meta:
        table = 'users'

    class Config:
        from_attributes = True

    def __str__(self) -> str:
        return self.first_name or self.email

class UserPianoModel(Model):
    id = fields.IntField(pk=True)

    # Relations
    user = fields.ForeignKeyField("models.User", related_name="pianos")
    piano_model = fields.ForeignKeyField(
        "models.PianoModel",
        related_name="user_pianos_by_model",
        null=True,
        db_column="pianomodel_id",
        source_field="pianomodel_id",
    )
    manufacturer = fields.ForeignKeyField(
        "models.Manufacturer",
        related_name="user_pianos_by_manufacturer",
        null=True,
        db_column="manufacturer_id",
    )
    piano_identification_session = fields.ForeignKeyField(
        "models.PianoIdentificationSession",
        related_name="user_pianos_by_session",
        null=True,
        db_column="piano_identification_session_id",
    )

    # Info libre utilisateur
    name = fields.CharField(max_length=255, null=True)
    location = fields.JSONField(null=True)
    purchase_year = fields.IntField(null=True)
    serial_number = fields.CharField(max_length=255, null=True)
    manufacture_year = fields.IntField(null=True)
    notes = fields.TextField(null=True)

    # 🎹 Infos piano
    model_name = fields.CharField(max_length=255, null=True)

    # ✅ Nouveaux IDs “plats” (pas de FK)
    kind_id = fields.SmallIntField(null=True, description="1=uprgrand , 2=upright (no FK)")
    piano_type_id = fields.SmallIntField(
        null=True,
        description="1=Spinet, 2=Console, 3=Studio, 4=Full upright, 5=Baby Grand, 6=Medium, 7=Parlor, 8=Music room, 9=Concert (no FK)",
    )

    # Labels conservés pour l’affichage / compat
    kind = fields.CharField(max_length=50, null=True)         # "grand" | "upright"
    type_label = fields.CharField(max_length=100, null=True)  # "baby grand" | "console" | ...

    size_cm = fields.FloatField(null=True)
    keys = fields.IntField(null=True)

    # 🧠 Résumés
    llm_description = fields.TextField(null=True)
    sound_characteristics = fields.TextField(null=True)
    condition_notes = fields.TextField(null=True)

    # 🛠 Extras
    maintenance_log = fields.JSONField(null=True)
    custom_data = fields.JSONField(null=True)
    extra_data = fields.JSONField(null=True)

    # Métadonnées
    public_share_token = fields.CharField(max_length=32, null=True, unique=True)
    status = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    async def ensure_public_token(self):
        if not self.public_share_token:
            self.public_share_token = uuid4().hex[:12]
            await self.save()
        return self.public_share_token

    class Meta:
        table = "pianomodel_user"
        unique_together = (("user", "piano_model"),)  # on traitera le dédoublonnage “manuel” plus tard

    class Config:
        from_attributes = True

class Session(Model):
    id = fields.IntField(pk=True, autoincrement=True)
    user_id = fields.ForeignKeyField('models.User', 
                                     related_name='sessions',
                                     null=True,
                                     on_delete=fields.SET_NULL)
    identification_session = fields.ForeignKeyField(
        "models.PianoIdentificationSession",
        related_name="user_pianos",
        null=True,
        db_column="piano_identification_session_id",
        on_delete=fields.SET_NULL
        )

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

class UserQuotaContext(BaseModel):
    limit: int
    used: int
    remaining: int


class UserContext(BaseModel):
    # --- Identité légère ---
    firstname: str
    language: str = "en"
    last_login: datetime

    # --- Etat produit ---
    form_completed: bool
    pianos: List[dict]
    last_diagnosis_exists: bool
    tuning_session_exists: bool

    # --- 🧾 Subscription / RBAC (NOUVEAU 🔑) ---
    plan_code: str                 # freemium | indy | pro
    role: str                      # individual | professional | admin
    entitlements: List[str]        # ["piano.create", "diagnosis.basic", ...]
    quotas: Dict[str, UserQuotaContext]  # {"pianos": {...}}

    # ⚠️ temporaire (à déprécier)
    subscription_level: Optional[str] = None

    # --- 🎼 Profil musical / émotionnel ---
    piano_years_playing: Optional[int] = None
    piano_study_started_as: Optional[str] = None  # Child | Adult | Self-taught
    music_styles: Optional[List[str]] = None
    favorite_composers: Optional[List[str]] = None
    favorite_performers: Optional[List[str]] = None
    current_piece: Optional[str] = None
    piano_satisfaction: Optional[str] = None
    wishes_to_change_piano: Optional[bool] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True     

class UserEntitlement(Model):
    user = fields.ForeignKeyField(
        "models.User",
        related_name="entitlements",
        on_delete=fields.CASCADE,
        pk=True,                # ✅ PK ORM (porteuse)
    )

    entitlement = fields.CharField(
        max_length=100,
    )

    source = fields.CharField(max_length=50, default="plan")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "user_entitlements"
        unique_together = (("user", "entitlement"),)

    def __str__(self):
        return f"{self.user_id}:{self.entitlement}"

class UserQuota(Model):
    id = fields.IntField(pk=True)  # ✅ PK technique ORM

    user = fields.ForeignKeyField(
        "models.User",
        related_name="quotas",
        on_delete=fields.CASCADE,
    )

    quota_key = fields.CharField(max_length=50)

    limit_value = fields.IntField()
    used_value = fields.IntField(default=0)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "user_quotas"
        unique_together = (("user", "quota_key"),)

    def remaining(self) -> int:
        return -1 if self.limit_value == -1 else max(self.limit_value - self.used_value, 0)

    def __str__(self):
        return f"{self.user_id}:{self.quota_key}={self.used_value}/{self.limit_value}"

class UserPlanHistory(Model):
    id = fields.IntField(pk=True, autoincrement=True)

    user = fields.ForeignKeyField(
        "models.User",
        related_name="plan_history",
        on_delete=fields.CASCADE
    )

    plan_code = fields.CharField(max_length=50)
    started_at = fields.DatetimeField(auto_now_add=True)
    ended_at = fields.DatetimeField(null=True)

    class Meta:
        table = "user_plan_history"

    def __str__(self):
        return f"{self.user_id}:{self.plan_code}"

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

class DiagnosisSession(Model):
    id = fields.IntField(pk=True)

    # 🔑 relation vers User
    user = fields.ForeignKeyField(
        "models.User",
        related_name="diagnosis_sessions",
        on_delete=fields.CASCADE
    )

    # 🔑 relation optionnelle vers le piano concerné
    pianomodel_user = fields.ForeignKeyField(
        "models.UserPianoModel",
        related_name="diagnosis_sessions",
        on_delete=fields.CASCADE,
        null=True
    )

    status = fields.IntEnumField(DiagnosisSessionStatus, default=DiagnosisSessionStatus.CREATED)
    data = fields.JSONField(null=True)

    created_at = fields.DatetimeField(auto_now_add=True, timezone=True)
    updated_at = fields.DatetimeField(auto_now=True, timezone=True)

    class Meta:
        table = "diagnosis_session"

class DiagnosisNote(Model):
    id = fields.IntField(pk=True)

    session = fields.ForeignKeyField(
        "models.DiagnosisSession",
        related_name="notes",
        on_delete=fields.CASCADE,
    )

    # --- Info de base ---
    note_name = fields.CharField(max_length=16)
    midi = fields.IntField()
    f0 = fields.FloatField()
    deviation_cents = fields.FloatField()
    confidence = fields.FloatField(null=True)

    # --- Inharmonicité globale (ex: moyenne) ---
    inharmonicity = fields.FloatField(null=True)

    # --- Coefficient B estimé pour cette note ---
    B_estimate = fields.FloatField(null=True)

    # --- Détail harmonique (pour analyse scientifique / fingerprint) ---
    # Liste des fréquences de partiels, ex: [f1, f2, f3, ...]
    partials = fields.JSONField(null=True)

    # Courbe d’inharmonicité par partiel, ex: [inh1, inh2, ...]
    inharmonicity_curve = fields.JSONField(null=True)

    # Empreinte spectrale compacte (vectorisée), ex: [0.12, 0.87, ...]
    spectral_fingerprint = fields.JSONField(null=True)

    # --- Analyse d'unisson (structure JSON venant du backend) ---
    unison = fields.JSONField(null=True)

    created_at = fields.DatetimeField(auto_now_add=True, timezone=True)

    class Meta:
        table = "diagnosis_note"

class TuningSession(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="tuning_sessions", on_delete=fields.CASCADE)
    pianomodel_user = fields.ForeignKeyField("models.UserPianoModel", related_name="tuning_sessions", on_delete=fields.CASCADE)
    status = fields.IntField(default=0)  # Peut devenir un Enum plus tard
    data = fields.JSONField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True, timezone=True)
    updated_at = fields.DatetimeField(auto_now=True, timezone=True)

    class Meta:
        table = "tuning_session"

class Conversation(Model):
    id = fields.UUIDField(pk=True)
    topic = fields.TextField(null=True)
    started_at = fields.DatetimeField(null=True)
    topic_tsv = fields.TextField(null=True)  # Peut être TextField même si c’est un TSVECTOR
    user = fields.ForeignKeyField(
        "models.User",
        related_name="conversations",
        null=True,
        on_delete=fields.SET_NULL
    )

    class Meta:
        table = "conversations"

    def __str__(self):
        return f"Conversation(id={self.id}, topic={self.topic})"

class PianoIdentificationSession(Model):
    id = fields.UUIDField(pk=True, default=uuid4)
    
    user = fields.ForeignKeyField(
        "models.User",
        related_name="guess_sessions",
        null=True,
        on_delete=fields.SET_NULL
    )
    conversation = fields.ForeignKeyField(
        "models.Conversation",         # nom  du modèle
        related_name="piano_sessions", # inverse FK 
        null=True,                     # ✅ rend la FK optionnelle
        on_delete=fields.SET_NULL      # ✅ comportement doux
    )


    image_urls = fields.JSONField(null=True)         # List[str]
    photo_metadata = fields.JSONField(default=list) 
    photo_labels = fields.JSONField(null=True)       # Dict[str, str]
    context_snapshot = fields.JSONField(null=True)   # dict
    model_hypothesis = fields.JSONField(null=True)   # dict
    metadata = fields.JSONField(null=True)   # dict
    report_url = fields.TextField(null=True)
    music_sources = fields.JSONField(null=True)
    
    extra_data = fields.JSONField(null=True)      # dict (JSONB)
    created_at = fields.DatetimeField(auto_now_add=True, timezone=True)

    class Meta:
        table = "piano_identification_sessions"

    def __str__(self):
        return f"PianoGuessSession(id={self.id})"

