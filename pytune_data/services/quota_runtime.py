# pytune_data/services/quota_runtime.py
from pytune_data.db import init
from pytune_data.models import UserQuota

from tortoise.queryset import QuerySet

async def increment_quota(user, key: str, delta: int = 1):
    await init()

    if not hasattr(user, "id"):
        raise TypeError(f"user has no id attribute: {type(user)}")

    if not isinstance(user.id, int):
        raise TypeError(
            f"user.id is not int (got {type(user.id)}): user={user}"
        )

    quota, _ = await UserQuota.get_or_create(
        user=user,
        quota_key=key,
        defaults={"limit_value": 0, "used_value": 0},
    )

    quota.used_value += delta
    await quota.save(update_fields=["used_value"])