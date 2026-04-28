from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_connector_auth
from app.db.models import ProviderModel
from app.db.session import get_session
from app.services.newapi_client import NewAPIClient
from app.services.sync import ModelSyncService

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_connector_auth)])


class ModelUpdate(BaseModel):
    manual_priority: int | None = Field(default=None, ge=1)
    enabled: bool | None = None


@router.post("/sync")
async def sync_models(session: AsyncSession = Depends(get_session)) -> dict[str, int]:
    return await ModelSyncService(session, NewAPIClient()).sync()


@router.get("/models")
async def list_admin_models(
    capability: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, object]]:
    stmt = select(ProviderModel).order_by(
        ProviderModel.capability,
        ProviderModel.manual_priority.asc().nulls_last(),
        ProviderModel.default_priority.asc(),
        ProviderModel.model_name.asc(),
    )
    if capability:
        stmt = stmt.where(ProviderModel.capability == capability)

    result = await session.execute(stmt)
    return [
        {
            "model": model.model_name,
            "capability": model.capability,
            "family": model.family,
            "enabled": model.enabled,
            "default_priority": model.default_priority,
            "manual_priority": model.manual_priority,
        }
        for model in result.scalars().all()
    ]


@router.patch("/models/{model_name:path}")
async def update_model(
    model_name: str,
    payload: ModelUpdate,
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    result = await session.execute(select(ProviderModel).where(ProviderModel.model_name == model_name))
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    if "manual_priority" in payload.model_fields_set:
        model.manual_priority = payload.manual_priority
    if payload.enabled is not None:
        model.enabled = payload.enabled

    await session.commit()
    return {
        "model": model.model_name,
        "enabled": model.enabled,
        "default_priority": model.default_priority,
        "manual_priority": model.manual_priority,
    }
