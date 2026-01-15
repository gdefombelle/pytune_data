from fastapi import HTTPException
from pytune_data.models import User
from pytune_data.services.plan_runtime import resolve_user_plan
from pytune_data.db import init

async def assert_can_create_piano(
    user: User,
    plans_catalog: dict,
):
    """
    Lève une HTTPException si l'utilisateur ne peut pas créer un nouveau piano.
    """
    plan = await resolve_user_plan(user, plans_catalog)
    quotas = plan["quotas"]

    piano_quota = quotas.get("pianos")
    if not piano_quota:
        # Pas défini = pas autorisé
        raise HTTPException(
            status_code=403,
            detail="Piano creation not allowed for your plan",
        )

    # limit = -1 => unlimited
    if piano_quota.limit == -1:
        return

    if piano_quota.remaining <= 0:
        raise HTTPException(
            status_code=403,
            detail="Piano limit reached for your plan",
        )