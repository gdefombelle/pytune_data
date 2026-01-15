from typing import Dict, List
from pytune_data.db import init

from pytune_data.models import (
    User,
    UserEntitlement,
    UserQuota,
)
from pydantic import BaseModel


class UserSubscriptionSnapshot(BaseModel):
    """
    Snapshot read-only de la subscription utilisateur.
    Utilisé par UserContext, agents et UI.
    """
    plan_code: str
    role: str
    entitlements: List[str]
    quotas: Dict[str, UserQuota]

    class Config:
        arbitrary_types_allowed = True  # autorise les modèles Tortoise


async def get_user_subscription_snapshot(user: User) -> UserSubscriptionSnapshot:
    """
    Retourne l'état subscription courant d'un utilisateur.

    - Aucun effet de bord
    - Aucune logique de plan
    - Lecture DB uniquement
    """
    await init()
    # --- entitlements ---
    raw_entitlements = await UserEntitlement.filter(user=user) \
    .values_list("entitlement", flat=True)

    entitlements: list[str] = [str(e) for e in raw_entitlements]    

    # --- quotas ---
    quota_rows = await UserQuota.filter(user=user)
    quotas: Dict[str, UserQuota] = {
        q.quota_key: q
        for q in quota_rows
    }

    return UserSubscriptionSnapshot(
        plan_code=user.plan_code,
        role=user.role,
        entitlements=list(entitlements),
        quotas=quotas,
    )