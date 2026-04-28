from fastapi import Header, HTTPException, status

from app.core.config import settings


async def require_connector_auth(authorization: str | None = Header(default=None)) -> None:
    if not settings.connector_api_key:
        return

    expected = f"Bearer {settings.connector_api_key}"
    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid connector API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
