# pytune_data/services/plan_runtime.py

from typing import Dict, Any

from pytune_data.models import (
    User,
    UserEntitlement,
    UserQuota,
    UserPlanHistory,
)
from pytune_data.models import UserQuotaContext
from pytune_data.db import init
from datetime import datetime, timezone

async def resolve_user_plan(
    user: User,
    plans_catalog: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Résout le plan effectif de l'utilisateur.
    - Aucune lecture disque
    - Aucun HTTP
    - Aucun effet de bord
    """
    await init()
    plan_code = user.plan_code or "freemium"
    plan_def = plans_catalog.get(plan_code)

    if not plan_def:
        raise RuntimeError(f"Unknown plan: {plan_code}")

    # --- quotas ---
    quotas: Dict[str, UserQuotaContext] = {}

    await user.fetch_related("quotas")
    yaml_quotas = plan_def.get("quotas", {})

    for key, limit in yaml_quotas.items():
        row = next((q for q in user.quotas if q.quota_key == key), None)

        if limit == "unlimited":
            quotas[key] = UserQuotaContext(
                limit=-1,
                used=row.used_value if row else 0,
                remaining=-1,
            )
            continue

        used = row.used_value if row else 0
        remaining = max(int(limit) - used, 0)

        quotas[key] = UserQuotaContext(
            limit=int(limit),
            used=used,
            remaining=remaining,
        )

    return {
        "plan_code": plan_code,
        "role": plan_def.get("role"),
        "features": plan_def.get("features", {}),
        "ui": plan_def.get("ui", {}),
        "quotas": quotas,
    }

async def apply_plan_to_user(
    user: User,
    plan_code: str,
    plans_catalog: Dict[str, Any],
    *,
    source: str = "plan",
    reset_quotas: bool = True,
):
    """
    Applique un plan à un utilisateur.

    - Écrit DB (entitlements, quotas, plan_code)
    - Trace l'historique
    - Aucun YAML caché
    """

    await init()

    plan_def = plans_catalog.get(plan_code)
    if not plan_def:
        raise RuntimeError(f"Unknown plan: {plan_code}")

    assert user.id is not None
   
    now = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # 🔁 Historique : fermer plan précédent
    # ------------------------------------------------------------------
    await UserPlanHistory.filter(
        user_id=user.id,
        ended_at__isnull=True
    ).update(ended_at=now)

    await UserPlanHistory.create(
        user_id=user.id,
        plan_code=plan_code,
        started_at=now,
    )

    # ------------------------------------------------------------------
    # 👤 User core
    # ------------------------------------------------------------------
    user.plan_code = plan_code
    user.role = plan_def.get("role", user.role)
    user.plan_started_at = now
    user.plan_ends_at = None

    await user.save(update_fields=[
        "plan_code",
        "role",
        "plan_started_at",
        "plan_ends_at",
    ])

    # ------------------------------------------------------------------
    # 🔐 ENTITLEMENTS (reset + recreate)
    # ------------------------------------------------------------------
    await UserEntitlement.filter(user_id=user.id).delete()

    for key, value in plan_def.get("features", {}).items():
        if value is True:
            await UserEntitlement.create(
                user_id=user.id,
                entitlement=key,
                source=source,
            )

    # ------------------------------------------------------------------
    # 📊 QUOTAS
    # ------------------------------------------------------------------
    yaml_quotas = plan_def.get("quotas", {})

    for quota_key, limit in yaml_quotas.items():
        limit_value = -1 if limit == "unlimited" else int(limit)

        quota, created = await UserQuota.get_or_create(
            user_id=user.id,              # ✅ EXPLICITE
            quota_key=quota_key,
            defaults={
                "limit_value": limit_value,
                "used_value": 0,
            },
        )

        if not created and reset_quotas:
            quota.used_value = 0

        quota.limit_value = limit_value
        await quota.save(update_fields=["limit_value", "used_value"])