# schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Dict, List, Optional, Union
from pytune_data.models import ManufacturerStatus, PianoCategoryEnum, UserStatusEnum, ClientStatusEnum, UserTypeEnum
from datetime import datetime

class PianoManufacturer(BaseModel):
    id:int
    company: str
    normalized_name : str
    place: str
    country: str
    years_active: Optional[str]
    acquired_by: Optional[str]
    permanently_closed: bool
    notes: Optional[str]
    wiki_url: Optional[str]

# Pydantic modèle pour la réponse
class ManufacturerResponse(BaseModel):
    id: int
    name: str
    country: str | None
    founded_year: int | None

    class Config:
        from_attributes = True

class ManufacturerCreate(PianoManufacturer):
    company: str
    place: str
    country: str
    years_active: Optional[str]
    acquired_by: Optional[str]
    permanently_closed: bool
    notes: Optional[str]
    wiki_url: Optional[str]
    status: ManufacturerStatus = ManufacturerStatus.PENDING 


class UserManufacturerCreate(BaseModel):
    company: str
    permanently_closed: Optional[bool] = True
    notes: Optional[str]
    status: Optional[ManufacturerStatus] = None
    originated_by : Optional[EmailStr] = None

    

class ManufacturerUpdate(PianoManufacturer):
    pass

class ManufacturerInDB(BaseModel):
    id: int
    company: str
    
class ManufacturerSerialNumberBase(BaseModel):
    """Schéma de base pour un numéro de série."""
    manufacturer_id: int
    serial_number: str
    year: Optional[int]

class ManufacturerSerialNumberCreate(ManufacturerSerialNumberBase):
    """Schéma pour l'ajout d'un numéro de série."""
    pass

class ManufacturerSerialNumberResponse(ManufacturerSerialNumberBase):
    """Schéma pour la réponse API."""
    id: int

    class Config:
        from_attributes = True  # Permet de convertir un modèle Tortoise en Pydantic
class PianoModel(BaseModel):
    id : Optional[int]
    manufacturer_id: int
    serie: Optional[str]
    name: str
    kind: Optional[PianoCategoryEnum]
    notes: Optional[str]
    width_cm: Optional[float]
    length_cm: Optional[float]
    height_cm: Optional[float]
    weight_kg: Optional[float]
    str_length: Optional[str]
    str_height: Optional[str]
    str_weight: Optional[str]
    keys: Optional[int]
    status : Optional[int]

class UserPianoModel(BaseModel):
    pianomodel_id : int
    manufacturer_id:int
    name: Optional[str]
    location : Optional[str]
    serial_number:Optional[str]
    manufacture_year:Optional[int]
    purchase_year:Optional[int]
    notes:Optional[str]


class PianoModelCreate(BaseModel):
    pass

class PianoModelUpdate(BaseModel):
    pass

class PianoModelInDB(BaseModel):
    id: int
    created_at: str
    updated_at: str
    last_connection: str

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    id: int
    username: str
    email: str
    phone_number: Optional[str]
    password: Optional[str]
    status: UserStatusEnum
    client_status: ClientStatusEnum
    first_name: Optional[str]
    last_name: Optional[str]
    language: Optional[str]
    timezone: Optional[str]
    country: Optional[str]
    user_type: UserTypeEnum

class UserCreateSchema(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str]
    last_name: Optional[str]
    business_name : Optional[str] = None
    location: Optional[str] = None
    location_details:  Optional[Dict[str, str]] = None
    country: Optional[str] = None
    phone_number: Optional[str] 
    website : Optional[str] = None
    history : Optional[Dict[str, Optional[str]]] = {}
    social_networks: Optional[str] = None
    services_offered: Optional[List[str]] = []
    user_type : Optional[UserTypeEnum] = UserTypeEnum.INDIVIDUAL
    website : Optional[str] = None
    additional_services : Optional[str] = None
    oauth_provider  : Optional[str] = None
    accepted_tos : bool
    accepted_privacy_policy : bool
    extra_data : Optional[Union[str, Dict[str, Union[str, int, bool, None]]]] = None
    
class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    language: Optional[str] = Field(default='en', max_length=8)
    timezone: Optional[str] = Field(default='UTC', max_length=50)
    country: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = None  # Ajouté comme optionnel
    client_status: Optional[str] = None  # Ajouté comme optionnel
    user_type : Optional[UserTypeEnum] = UserTypeEnum.INDIVIDUAL
    extra_data: Optional[Union[str, Dict[str, Union[str, int, bool, None]]]] = None
    location: Optional[str] = None
    location_details: Optional[Dict[str, str]] = None
    services_offered: Optional[List[str]] = None
    additional_services: Optional[str] = None
    business_name: Optional[str] = None
    website: Optional[str] = None
    history: Optional[str] = None
    social_networks: Optional[str] = None
    # extra_data : Optional[Union[str, Dict[str, Union[str, int, bool, None]]]]
    class Config:
        from_attributes = True



class OnlineUserPydantic(BaseModel):
    user_email: EmailStr
    platform: str
    last_seen: datetime

    class Config:
        from_attributes = True

class UserInDB(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_connection: datetime
    user_type: UserTypeEnum
    status:UserStatusEnum

    class Config:
        from_attributes = True

class SessionBase(BaseModel):
    user_id: int
    piano_model_id: int
    ip_address: str
    numeric_data: dict
    lists: dict
    acoustic_signals: Optional[str]

class SessionCreate(SessionBase):
    pass

class SessionUpdate(SessionBase):
    pass

class SessionInDB(SessionBase):
    id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
from pydantic import BaseModel
from typing import List, Optional

class ClientAPICreate(BaseModel):
    client_name: str
    client_id: str
    client_secret: str
    redirect_uris: List[str]
    client_type: str = "confidential"
    scope: str = "read write"
    grant_types: str = "authorization_code"
    token_endpoint_auth_method: str = "client_secret_basic"

class ClientAPIOut(BaseModel):
    id: int
    client_name: str
    client_id: str
    redirect_uris: List[str]
    client_type: str
    scope: str
    grant_types: str
    token_endpoint_auth_method: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class ClientAPIUpdate(BaseModel):
    client_name: Optional[str]
    redirect_uris: Optional[List[str]]
    client_type: Optional[str]
    scope: Optional[str]
    grant_types: Optional[str]
    token_endpoint_auth_method: Optional[str]
