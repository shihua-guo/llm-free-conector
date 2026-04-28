from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_connector_auth
from app.core.aliases import FIXED_ALIASES
from app.db.models import ProviderModel
from app.db.session import get_session

router = APIRouter(prefix="/v1", tags=["models"], dependencies=[Depends(require_connector_auth)])


@router.get("/models")
async def list_models(session: AsyncSession = Depends(get_session)) -> dict[str, object]:
    result = await session.execute(
        select(ProviderModel)
        .where(ProviderModel.enabled.is_(True))
        .order_by(ProviderModel.capability, ProviderModel.model_name)
    )
    models = result.scalars().all()

    now = int(datetime.now(timezone.utc).timestamp())
    alias_items = [
        {
            "id": alias,
            "object": "model",
            "created": now,
            "owned_by": "llm-free-conector",
            "capability": capability,
        }
        for alias, capability in FIXED_ALIASES.items()
    ]
    model_items = [
        {
            "id": model.model_name,
            "object": "model",
            "created": int((model.created_at or datetime.now(timezone.utc)).timestamp()),
            "owned_by": model.source,
            "capability": model.capability,
        }
        for model in models
    ]
    return {"object": "list", "data": alias_items + model_items}
