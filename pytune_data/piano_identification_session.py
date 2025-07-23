# pytune_data/piano_guess_session.py

from tortoise.exceptions import DoesNotExist
from pytune_data.db import ensure_db_initialized, init
from pytune_data.models import PianoIdentificationSession
from typing import Optional, List
from uuid import UUID

@ensure_db_initialized
async def create_identification_session(
    user_id: Optional[UUID],
    image_urls: List[str],
    photo_labels: Optional[dict] = None,
    photo_metadata: Optional[list] = None,
    context_snapshot: Optional[dict] = None,
    model_hypothesis: Optional[dict] = None,
    metadata: Optional[dict] = None
) -> PianoIdentificationSession:
    return await PianoIdentificationSession.create(
        user_id=user_id,
        image_urls=image_urls,
        photo_labels=photo_labels or {},
        photo_metadata=photo_metadata or [],
        context_snapshot=context_snapshot or {},
        model_hypothesis=model_hypothesis or {},
        metadata=metadata or {}
    )


@ensure_db_initialized
async def get_identification_session(session_id: UUID) -> Optional[PianoIdentificationSession]:
    try:
        return await PianoIdentificationSession.get(id=session_id)
    except DoesNotExist:
        return None

@ensure_db_initialized
async def update_identification_session(session_id: UUID, **fields) -> Optional[PianoIdentificationSession]:
    session = await get_identification_session(session_id)
    if not session:
        return None

    for key, value in fields.items():
        setattr(session, key, value)
    await session.save()
    return session

@ensure_db_initialized
async def delete_identification_session(session_id: UUID) -> bool:
    session = await get_identification_session(session_id)
    if not session:
        return False
    await session.delete()
    return True
