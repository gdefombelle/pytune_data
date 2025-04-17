from typing import Optional
from pytune_data.models import User, UserContext, UserPianoModel, UserTypeEnum
from pytune_data.db import init
from tortoise.exceptions import DoesNotExist
from pytune_data.crud import get_user_by_email, get_user_by_id
from simple_logger.logger import get_logger, SimpleLogger

logger : SimpleLogger = get_logger("data")

async def get_user_context(user_id: Optional[int] = None, email: Optional[str] = None) -> Optional[UserContext]:
    if not user_id and not email:
        raise ValueError("user_id or email must be provided")

    await init()  # Init ORM si nécessaire

    user: Optional[User] = None
    if user_id:
        user = await User.get_or_none(id=user_id).prefetch_related("pianos")
    elif email:
        user = await User.get_or_none(email=email).prefetch_related("pianos")

    if not user:
        return None

    pianos = await user.pianos.all()
    pianos_data = [
        {
            "id": p.id,
            "brand": getattr(p, "brand", None),
            "model": getattr(p, "model", None),
            "year": getattr(p, "year", None),
        } for p in pianos
    ]

    last_diag = await Diagnosis.filter(user_id=user.id).order_by("-created_at").first()
    last_tune = await TuningSession.filter(user_id=user.id).order_by("-created_at").first()

    return UserContext(
        firstname=user.first_name or "User",
        form_completed=bool(user.first_name and user.last_name and user.accepted_tos),
        pianos=pianos_data,
        last_diagnosis_exists=bool(last_diag),
        tuning_session_exists=bool(last_tune),
        language=user.language or "en"
    )

    if not user_id and not email:
        raise ValueError("user_id or email must be provided")

    await init()  
    user: Optional[User] = None
    if user_id:
        user = await User.get_or_none(id=user_id).prefetch_related("pianos")
    elif email:
        user = await User.get_or_none(email=email).prefetch_related("pianos")

    if not user:
        return None

    pianos = await user.pianos.all()
    piano_count = len(pianos)

    # On suppose que tu as une table Diagnosis liée à User (ajuste selon ta structure)
    last_diag = await Diagnosis.filter(user_id=user.id).order_by("-created_at").first()

    return UserContext(
        first_name=user.first_name or "User",
        form_completed=bool(user.first_name and user.last_name and user.accepted_tos),
        language=user.language or "en",
        piano_count=piano_count,
        last_diagnosis_exists=bool(last_diag)
    )