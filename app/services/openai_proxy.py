import time
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from uuid import uuid4

import httpx
from fastapi import HTTPException, Request
from starlette.datastructures import UploadFile

from app.core.config import settings
from app.services.router import ModelCandidate, ModelRouter


@dataclass
class ProxyResult:
    status_code: int
    media_type: str | None = None
    headers: dict[str, str] | None = None
    content: bytes | None = None
    stream: AsyncIterator[bytes] | None = None
    close_stream: Callable[[], Awaitable[None]] | None = None


class OpenAIProxy:
    def __init__(self, model_router: ModelRouter) -> None:
        self.model_router = model_router
        self.base_url = str(settings.newapi_base_url).rstrip("/")
        self.timeout = httpx.Timeout(settings.http_timeout_seconds)

    async def forward(self, request: Request, capability: str) -> ProxyResult:
        inbound = await self._parse_inbound(request)
        if not inbound.model:
            raise HTTPException(status_code=400, detail="Request body must include a non-empty model")

        candidates = await self.model_router.resolve(inbound.model, capability)
        if not candidates:
            raise HTTPException(status_code=503, detail=f"No enabled models for alias '{inbound.model}'")

        request_id = uuid4().hex
        last_response: httpx.Response | None = None
        last_error = ""

        for candidate in candidates:
            started = time.perf_counter()

            try:
                result = await self._send(request, inbound, candidate.model_name)
            except httpx.HTTPError as exc:
                last_error = str(exc)
                await self.model_router.record_attempt(
                    request_id=request_id,
                    requested_model=inbound.model,
                    candidate=candidate,
                    status_code=None,
                    success=False,
                    latency_ms=self._elapsed_ms(started),
                    error=last_error,
                )
                continue

            if result.status_code < 400:
                await self.model_router.record_attempt(
                    request_id=request_id,
                    requested_model=inbound.model,
                    candidate=candidate,
                    status_code=result.status_code,
                    success=True,
                    latency_ms=self._elapsed_ms(started),
                    error="",
                )
                return result

            if result.content is not None:
                last_response = httpx.Response(result.status_code, content=result.content, headers=result.headers)
            await self.model_router.record_attempt(
                request_id=request_id,
                requested_model=inbound.model,
                candidate=candidate,
                status_code=result.status_code,
                success=False,
                latency_ms=self._elapsed_ms(started),
                error=(result.content or b"").decode("utf-8", errors="ignore")[:1000],
            )

            if result.status_code not in settings.retry_status_code_set:
                return result

        if last_response is not None:
            return ProxyResult(
                status_code=last_response.status_code,
                headers=self._response_headers(last_response.headers),
                media_type=last_response.headers.get("content-type"),
                content=last_response.content,
            )

        raise HTTPException(status_code=502, detail=last_error or "All candidate models failed")

    async def _send(self, request: Request, inbound: "_InboundRequest", routed_model: str) -> ProxyResult:
        url = f"{self.base_url}{request.url.path}"
        headers = self._request_headers(request)
        kwargs = inbound.to_httpx_kwargs(routed_model)

        if inbound.stream:
            client = httpx.AsyncClient(timeout=self.timeout)
            stream_context = client.stream(
                request.method,
                url,
                params=request.query_params,
                headers=headers,
                **kwargs,
            )
            response = await stream_context.__aenter__()
            if response.status_code >= 400:
                content = await response.aread()
                await stream_context.__aexit__(None, None, None)
                await client.aclose()
                return ProxyResult(
                    status_code=response.status_code,
                    headers=self._response_headers(response.headers),
                    media_type=response.headers.get("content-type"),
                    content=content,
                )

            async def close() -> None:
                await stream_context.__aexit__(None, None, None)
                await client.aclose()

            return ProxyResult(
                status_code=response.status_code,
                headers=self._response_headers(response.headers),
                media_type=response.headers.get("content-type"),
                stream=response.aiter_bytes(),
                close_stream=close,
            )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                request.method,
                url,
                params=request.query_params,
                headers=headers,
                **kwargs,
            )

        return ProxyResult(
            status_code=response.status_code,
            headers=self._response_headers(response.headers),
            media_type=response.headers.get("content-type"),
            content=response.content,
        )

    @staticmethod
    def _elapsed_ms(started: float) -> int:
        return int((time.perf_counter() - started) * 1000)

    @staticmethod
    def _request_headers(request: Request) -> dict[str, str]:
        headers: dict[str, str] = {}
        content_type = request.headers.get("content-type")
        if content_type and "multipart/form-data" not in content_type:
            headers["content-type"] = content_type
        if settings.relay_api_key:
            headers["authorization"] = f"Bearer {settings.relay_api_key}"
        return headers

    @staticmethod
    def _response_headers(headers: httpx.Headers) -> dict[str, str]:
        ignored = {"content-length", "content-encoding", "transfer-encoding", "connection"}
        return {key: value for key, value in headers.items() if key.lower() not in ignored}

    async def _parse_inbound(self, request: Request) -> "_InboundRequest":
        content_type = request.headers.get("content-type", "")
        if "multipart/form-data" in content_type:
            form = await request.form()
            data: list[tuple[str, str]] = []
            files: list[tuple[str, tuple[str | None, bytes, str | None]]] = []
            model = ""

            for key, value in form.multi_items():
                if isinstance(value, UploadFile):
                    files.append((key, (value.filename, await value.read(), value.content_type)))
                    continue

                text_value = str(value)
                if key == "model":
                    model = text_value
                data.append((key, text_value))

            return _InboundRequest(model=model, form_data=data, files=files)

        body = await request.json()
        model = body.get("model")
        if not isinstance(model, str):
            model = ""
        return _InboundRequest(model=model, json_body=body, stream=body.get("stream") is True)


@dataclass
class _InboundRequest:
    model: str
    json_body: dict | None = None
    form_data: list[tuple[str, str]] | None = None
    files: list[tuple[str, tuple[str | None, bytes, str | None]]] | None = None
    stream: bool = False

    def to_httpx_kwargs(self, routed_model: str) -> dict[str, object]:
        if self.json_body is not None:
            body = dict(self.json_body)
            body["model"] = routed_model
            return {"json": body}

        data = [(key, routed_model if key == "model" else value) for key, value in self.form_data or []]
        if not any(key == "model" for key, _ in data):
            data.append(("model", routed_model))
        return {"data": data, "files": self.files or []}
