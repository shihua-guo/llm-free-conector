from typing import Any

import httpx

from app.core.config import settings


class NewAPIClient:
    def __init__(self) -> None:
        self.base_url = str(settings.newapi_base_url).rstrip("/")
        self.timeout = httpx.Timeout(settings.http_timeout_seconds)
        self._session_cookie = settings.newapi_session_cookie
        self._user_id = settings.newapi_user_id

    async def list_channels(self) -> list[dict[str, Any]]:
        channels: list[dict[str, Any]] = []
        page = 0

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            while True:
                response = await client.get(
                    settings.newapi_channel_list_path,
                    params={"p": page, "page_size": settings.newapi_channel_page_size},
                    headers=await self._admin_headers(client),
                )
                response.raise_for_status()
                payload = response.json()
                self._raise_for_newapi_error(payload)
                items = self._extract_items(payload)
                channels.extend(items)

                if not items or len(items) < settings.newapi_channel_page_size:
                    break
                page += 1

        return channels

    async def fetch_channel_models(self, channel_id: str) -> list[str]:
        path = settings.newapi_fetch_channel_models_path.format(channel_id=channel_id)
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.get(path, headers=await self._admin_headers(client))
            response.raise_for_status()
            payload = response.json()
            self._raise_for_newapi_error(payload)
        return self._extract_models(payload)

    async def list_channel_models(self) -> list[str]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.get(
                settings.newapi_channel_models_path,
                headers=await self._admin_headers(client),
            )
            response.raise_for_status()
            payload = response.json()
            self._raise_for_newapi_error(payload)
        return self._extract_models(payload)

    async def _admin_headers(self, client: httpx.AsyncClient) -> dict[str, str]:
        await self._ensure_login(client)

        headers: dict[str, str] = {}
        if settings.newapi_admin_token:
            headers["Authorization"] = f"Bearer {settings.newapi_admin_token}"
        if self._session_cookie:
            headers["Cookie"] = f"session={self._session_cookie}"
        if self._user_id:
            headers["New-Api-User"] = self._user_id
        return headers

    async def _ensure_login(self, client: httpx.AsyncClient) -> None:
        if settings.newapi_admin_token or self._session_cookie:
            return
        if not settings.newapi_username or not settings.newapi_password:
            return

        response = await client.post(
            settings.newapi_login_path,
            json={"username": settings.newapi_username, "password": settings.newapi_password},
        )
        response.raise_for_status()
        payload = response.json()
        self._raise_for_newapi_error(payload)

        data = payload.get("data") if isinstance(payload, dict) else None
        if isinstance(data, dict) and data.get("id") is not None:
            self._user_id = str(data["id"])

        session_cookie = response.cookies.get("session")
        if not session_cookie:
            raise RuntimeError("NewAPI login succeeded but did not return a session cookie")
        self._session_cookie = session_cookie

    @staticmethod
    def _raise_for_newapi_error(payload: Any) -> None:
        if isinstance(payload, dict) and payload.get("success") is False:
            message = payload.get("message") or "NewAPI request failed"
            raise RuntimeError(str(message))

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
