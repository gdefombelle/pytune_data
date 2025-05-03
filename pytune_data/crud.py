# crud.py
from datetime import datetime
from tortoise.timezone import now
from tortoise.transactions import in_transaction
from tortoise.exceptions import DoesNotExist
from pytune_data.models import Manufacturer, PianoModel, User, Session, UserStatusEnum
from pytune_data.schemas import (
    ManufacturerCreate, ManufacturerUpdate, ManufacturerInDB,
    PianoModelCreate, PianoModelUpdate, PianoModelInDB,
    UserCreateSchema, UserUpdate, UserInDB,
    SessionCreate, SessionUpdate, SessionInDB
)
from tortoise.queryset import Q
from pytune_data.db import init, close

async def get_user_by_id(user_id: int):
    try:
        user = await User.get(id=user_id)
        return user
    except DoesNotExist:
        return None
    
async def get_user_by_email(email: str):
    await init()
    return await User.get_or_none(email=email)

################ DELETE USER #####################
async def anonymize_user_related_data(user_id: int):
    # Anonymiser les sessions en mettant user_id à None
    await Session.filter(user_id=user_id).update(user_id=None)
    
    # Retirer l'utilisateur des pianos qu'il possède
    user = await User.get(id=user_id)
    pianos = await user.piano_models.all()
    for piano in pianos:
        await piano.owners.remove(user)
    
    # Si vous avez d'autres données personnelles dans le modèle User, vous pouvez les anonymiser :
    await user.update_from_dict({
        'username': f'anonymous_{user_id}',
        'email': f'anonymous_{user_id}@example.com',
        'first_name': '',
        'last_name': '',
        'phone_number': None,
        # Mettez à jour d'autres champs personnels si nécessaire
    })
    await user.save()


async def delete_user(user_id: int):
    async with in_transaction():
        # Supprimer l'utilisateur et ses information
        await User.filter(id=user_id).delete()

async def create_user(user: UserCreateSchema) -> UserInDB:
    await init()
    db_user = User(**user.model_dump())
    await db_user.save()
    return UserInDB.model_validate(db_user)

async def update_user(user_id: int, user: UserUpdate) -> UserInDB:
    print("🔥 pytune_data.services.user_service.update_user() loaded")  # tout en haut
    await init()
    db_user = await User.get(id=user_id)
    # Met à jour les champs de l'utilisateur avec ceux fournis dans le schéma
    await db_user.update_from_dict(user.model_dump(exclude_unset=True))
    await db_user.save()
    return db_user

async def update_user_status(user_id: int, new_status: UserStatusEnum) -> UserInDB:  # Type hint corrigé
    """
    Met à jour le statut d'un utilisateur dans la base de données.

    Args:
        user_id (int): L'ID de l'utilisateur à mettre à jour.
        status (UserStatusEnum): Le nouveau statut de l'utilisateur.

    Returns:
        UserInDB: L'objet UserInDB mis à jour.
    """
    await init()
    db_user = await User.get(id=user_id)
    db_user.status = new_status
    await db_user.save()  # Sauvegarde directe de l'objet
    return UserInDB.model_validate(db_user)

async def create_session(session: SessionCreate) -> SessionInDB:
    await init()
    db_session = Session(**session.model_dump())
    await db_session.save()
    return SessionInDB.model_validate(db_session)

async def update_session(session_id: int, session: SessionUpdate) -> SessionInDB:
    await init()
    db_session = await Session.get(id=session_id)
    await db_session.update_from_dict(session.model_dump())
    await db_session.save()
    return SessionInDB.model_validate(db_session)

async def update_user_last_connection(user_id: int):
    await init()
    user = await User.get(id=user_id)
    if user:
        user.last_connection = now()
        await user.save(update_fields=["last_connection"])