from typing import Optional, List
from datetime import datetime
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
        user = await User.get_or_none(id=user_id)
    elif email:
        user = await User.get_or_none(email=email)

    if not user:
        logger.warning("User not found for context fetch.")
        return None

    # 🔥 fetch la relation "pianos"
    await user.fetch_related("pianos")
    pianos = user.pianos

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

    # 🌟 Extraire le profil musical depuis extra_data (si présent)
    extra = user.extra_data or {}

    user_context = UserContext(
        firstname=user.first_name or "User",
        form_completed=bool(user.first_name and user.last_name and user.accepted_tos),
        pianos=pianos_data,
        last_diagnosis_exists=bool(last_diagnosis),
        tuning_session_exists=bool(last_tuning),
        language=user.language or "en",
        last_login=user.last_connection or datetime.utcnow(),  # fallback actuel
        subscription_level="free",  # Valeur par défaut pour l’instant

        # Profil musical émotionnel
        piano_years_playing=extra.get("piano_years_playing"),
        piano_study_started_as=extra.get("piano_study_started_as"),
        music_styles=extra.get("music_styles", []),
        favorite_composers=extra.get("favorite_composers", []),
        favorite_performers=extra.get("favorite_performers", []),
        current_piece=extra.get("current_piece"),
        piano_satisfaction=extra.get("piano_satisfaction"),
        wishes_to_change_piano=extra.get("wishes_to_change_piano"),
    )

    return user_context

