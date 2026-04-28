from datetime import datetime, timezone
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Channel, ChannelModel, ProviderModel
from app.services.model_classifier import classify_model
from app.services.newapi_client import NewAPIClient


class ModelSyncService:
    def __init__(self, session: AsyncSession, client: NewAPIClient) -> None:
        self.session = session
        self.client = client

    async def sync(self) -> dict[str, int]:
        channels = await self.client.list_channels()
        channel_count = 0
        model_names: set[str] = set()
        channel_model_count = 0

        for channel in channels:
            external_id = self._channel_id(channel)
            if not external_id:
                continue

            await self._upsert_channel(external_id, channel)
            channel_count += 1

            models = await self._models_for_channel(external_id, channel)
            for model_name in models:
                classification = classify_model(model_name)
                await self._upsert_model(model_name, classification, channel)
                await self._upsert_channel_model(external_id, model_name, channel)
                model_names.add(model_name)
                channel_model_count += 1

        await self.session.commit()
        return {
            "channels": channel_count,
            "models": len(model_names),
            "channel_models": channel_model_count,
        }

    async def _models_for_channel(self, external_id: str, channel: dict[str, Any]) -> list[str]:
        try:
            fetched = await self.client.fetch_channel_models(external_id)
            if fetched:
                return fetched
        except Exception:
            pass

        raw_models = channel.get("models") or channel.get("model_mapping") or channel.get("model")
        return NewAPIClient._coerce_models(raw_models)

    async def _upsert_channel(self, external_id: str, channel: dict[str, Any]) -> None:
        stmt = insert(Channel).values(
            external_id=external_id,
            name=str(channel.get("name") or channel.get("channel_name") or ""),
            channel_type=str(channel.get("type") or channel.get("channel_type") or ""),
            status=str(channel.get("status") or ""),
            enabled=self._is_enabled(channel),
            raw=channel,
            last_synced_at=datetime.now(timezone.utc),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[Channel.external_id],
            set_={
                "name": stmt.excluded.name,
                "channel_type": stmt.excluded.channel_type,
                "status": stmt.excluded.status,
                "enabled": stmt.excluded.enabled,
                "raw": stmt.excluded.raw,
                "last_synced_at": stmt.excluded.last_synced_at,
            },
        )
        await self.session.execute(stmt)

    async def _upsert_model(self, model_name: str, classification: Any, raw: dict[str, Any]) -> None:
        stmt = insert(ProviderModel).values(
            model_name=model_name,
            capability=classification.capability,
            family=classification.family,
            source="newapi",
            enabled=True,
            default_priority=classification.default_priority,
            raw={"last_channel": raw},
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[ProviderModel.model_name],
            set_={
                "capability": stmt.excluded.capability,
                "family": stmt.excluded.family,
                "default_priority": stmt.excluded.default_priority,
                "raw": stmt.excluded.raw,
            },
        )
        await self.session.execute(stmt)

    async def _upsert_channel_model(self, external_id: str, model_name: str, raw: dict[str, Any]) -> None:
        stmt = insert(ChannelModel).values(
            channel_external_id=external_id,
            model_name=model_name,
            enabled=True,
            raw=raw,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_channel_model",
            set_={
                "enabled": stmt.excluded.enabled,
                "raw": stmt.excluded.raw,
            },
        )
        await self.session.execute(stmt)

    @staticmethod
    def _channel_id(channel: dict[str, Any]) -> str:
        value = channel.get("id") or channel.get("channel_id") or channel.get("key")
        return str(value) if value is not None else ""

    @staticmethod
    def _is_enabled(channel: dict[str, Any]) -> bool:
        if "enabled" in channel:
            return bool(channel["enabled"])
        status = str(channel.get("status") or "").lower()
        if status in {"disabled", "disable", "false", "0"}:
            return False
        return True
