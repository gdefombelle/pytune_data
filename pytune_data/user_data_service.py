from typing import Optional, List
from pytune_data.models import User, UserContext, UserPianoModel, UserTypeEnum, Diagnosis, TuningSession
from pytune_data.db import init
from simple_logger.logger import get_logger, SimpleLogger

logger: SimpleLogger = get_logger("data")

async def get_user_context(user_id: Optional[int] = None, email: Optional[str] = None) -> Optional[UserContext]:
    if not user_id and not email:
        raise ValueError("user_id or email must be provided")

    await init()

    user: Optional[User] = None
    if user_id:
        user = await User.get_or_none(id=user_id)  # sans prefetch_related
    elif email:
        user = await User.get_or_none(email=email)

    if not user:
        logger.warning("User not found for context fetch.")
        return None

    pianos = await user.pianos.all()
    pianos_data = [
        {
            "id": piano.id,
            "name": piano.name,
            "location": piano.location,
            "purchase_year": piano.purchase_year,
            "serial_number": piano.serial_number,
        }
        for piano in pianos
    ]

    last_diagnosis = await Diagnosis.filter(user_id=user.id).order_by("-created_at").first()
    last_tuning = await TuningSession.filter(user_id=user.id).order_by("-created_at").first()

    user_context = UserContext(
        firstname=user.first_name or "User",
        form_completed=bool(user.first_name and user.last_name and user.accepted_tos),
        pianos=pianos_data,
        last_diagnosis_exists=bool(last_diagnosis),
        tuning_session_exists=bool(last_tuning),
        language=user.language or "en",
    )

    return user_context
