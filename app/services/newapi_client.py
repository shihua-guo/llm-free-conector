from typing import Any

import httpx

from app.core.config import settings


class NewAPIClient:
    def __init__(self) -> None:
        self.base_url = str(settings.newapi_base_url).rstrip("/")
        self.timeout = httpx.Timeout(settings.http_timeout_seconds)

    async def list_channels(self) -> list[dict[str, Any]]:
        channels: list[dict[str, Any]] = []
        page = 0

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            while True:
                response = await client.get(
                    settings.newapi_channel_list_path,
                    params={"p": page},
                    headers=self._admin_headers(),
                )
                response.raise_for_status()
                payload = response.json()
                items = self._extract_items(payload)
                channels.extend(items)

                if not items or len(items) < 10:
                    break
                page += 1

        return channels

    async def fetch_channel_models(self, channel_id: str) -> list[str]:
        path = settings.newapi_fetch_channel_models_path.format(channel_id=channel_id)
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.get(path, headers=self._admin_headers())
            response.raise_for_status()
            payload = response.json()
        return self._extract_models(payload)

    async def list_channel_models(self) -> list[str]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.get(settings.newapi_channel_models_path, headers=self._admin_headers())
            response.raise_for_status()
            payload = response.json()
        return self._extract_models(payload)

    def _admin_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if settings.newapi_admin_token:
            headers["Authorization"] = f"Bearer {settings.newapi_admin_token}"
        if settings.newapi_user_id:
            headers["New-Api-User"] = settings.newapi_user_id
        return headers

    @staticmethod
    def _extract_items(payload: Any) -> list[dict[str, Any]]:
        data = payload.get("data", payload) if isinstance(payload, dict) else payload
        if isinstance(data, dict):
            for key in ("items", "channels", "records", "data"):
                value = data.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
            return []
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return []

    @staticmethod
    def _extract_models(payload: Any) -> list[str]:
        data = payload.get("data", payload) if isinstance(payload, dict) else payload
        if isinstance(data, dict):
            for key in ("models", "model_names", "data"):
                value = data.get(key)
                models = NewAPIClient._coerce_models(value)
                if models:
                    return models
        return NewAPIClient._coerce_models(data)

    @staticmethod
    def _coerce_models(value: Any) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            models: list[str] = []
            for item in value:
                if isinstance(item, str) and item.strip():
                    models.append(item.strip())
                elif isinstance(item, dict):
                    name = item.get("id") or item.get("model") or item.get("name")
                    if isinstance(name, str) and name.strip():
                        models.append(name.strip())
            return models
        return []
