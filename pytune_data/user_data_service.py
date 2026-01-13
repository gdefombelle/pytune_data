from typing import Optional, Dict
from datetime import datetime, timezone

from pytune_data.models import (
    User,
    UserContext,
    UserPianoModel,
    UserQuotaContext,
    TuningSession,
    DiagnosisSession,
)
from pytune_data.services.subscription import get_user_subscription
from pytune_data.db import init
from simple_logger.logger import get_logger, SimpleLogger

logger: SimpleLogger = get_logger("data")


async def get_user_context(
    user_id: Optional[int] = None,
    email: Optional[str] = None,
) -> Optional[UserContext]:
    """
    Build and return a full UserContext used by agents.
    Includes legacy fields, subscription snapshot, and emotional/musical profile.
    """

    if not user_id and not email:
        raise ValueError("user_id or email must be provided")

    await init()

    # --- fetch user ---
    user: Optional[User] = None
    if user_id:
        user = await User.get_or_none(id=user_id)
    elif email:
        user = await User.get_or_none(email=email)

    if not user:
        logger.warning("User not found for context fetch.")
        return None

    # --- pianos ---
    pianos = await UserPianoModel.filter(user=user).all()

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

    # --- sessions ---
    last_diagnosis = await DiagnosisSession.filter(
        user_id=user.id
    ).order_by("-created_at").first()

    last_tuning = await TuningSession.filter(
        user_id=user.id
    ).order_by("-created_at").first()

    # --- profil musical / émotionnel ---
    extra = user.extra_data or {}

    # 🔑 --- SUBSCRIPTION SNAPSHOT ---
    subscription = await get_user_subscription(user)

    # 🧾 quotas → UserQuotaContext (STRICT TYPING)
    quotas_ctx: Dict[str, UserQuotaContext] = {
        key: UserQuotaContext(
            limit=q.limit_value,
            used=q.used_value,
            remaining=max(q.limit_value - q.used_value, 0),
        )
        for key, q in subscription.quotas.items()
    }

    # --- build context ---
    user_context = UserContext(
        # --- legacy fields ---
        firstname=user.first_name or "User",
        form_completed=bool(
            user.first_name and user.last_name and user.accepted_tos
        ),
        pianos=pianos_data,
        last_diagnosis_exists=bool(last_diagnosis),
        tuning_session_exists=bool(last_tuning),
        language=user.language or "en",
        last_login=user.last_connection
        or datetime.now(timezone.utc),  # ✅ timezone-aware

        # --- 🧾 subscription ---
        plan_code=subscription.plan_code,
        role=subscription.role,
        entitlements=subscription.entitlements,
        quotas=quotas_ctx,

        # ⚠️ compat legacy agents
        subscription_level=subscription.plan_code,

        # --- 🎼 profil musical émotionnel ---
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