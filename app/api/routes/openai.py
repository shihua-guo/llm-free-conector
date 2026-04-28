from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.background import BackgroundTask
from starlette.responses import Response, StreamingResponse

from app.api.deps import require_connector_auth
from app.db.session import get_session
from app.services.openai_proxy import OpenAIProxy
from app.services.router import ModelRouter

router = APIRouter(prefix="/v1", tags=["openai"], dependencies=[Depends(require_connector_auth)])


async def _proxy(request: Request, capability: str, session: AsyncSession) -> Response:
    model_router = ModelRouter(session)
    proxy = OpenAIProxy(model_router)
    result = await proxy.forward(request, capability)

    if result.stream is not None:
        assert result.close_stream is not None
        return StreamingResponse(
            result.stream,
            status_code=result.status_code,
            media_type=result.media_type,
            background=BackgroundTask(result.close_stream),
            headers=result.headers,
        )

    return Response(
        content=result.content,
        status_code=result.status_code,
        media_type=result.media_type,
        headers=result.headers,
    )


@router.post("/chat/completions")
async def chat_completions(request: Request, session: AsyncSession = Depends(get_session)) -> Response:
    return await _proxy(request, "text", session)


@router.post("/completions")
async def completions(request: Request, session: AsyncSession = Depends(get_session)) -> Response:
    return await _proxy(request, "text", session)


@router.post("/responses")
async def responses(request: Request, session: AsyncSession = Depends(get_session)) -> Response:
    return await _proxy(request, "text", session)


@router.post("/embeddings")
async def embeddings(request: Request, session: AsyncSession = Depends(get_session)) -> Response:
    return await _proxy(request, "embedding", session)


@router.post("/images/generations")
async def images_generations(request: Request, session: AsyncSession = Depends(get_session)) -> Response:
    return await _proxy(request, "image", session)


@router.post("/audio/speech")
async def audio_speech(request: Request, session: AsyncSession = Depends(get_session)) -> Response:
    return await _proxy(request, "audio", session)


@router.post("/audio/transcriptions")
async def audio_transcriptions(request: Request, session: AsyncSession = Depends(get_session)) -> Response:
    return await _proxy(request, "audio", session)


@router.post("/audio/translations")
async def audio_translations(request: Request, session: AsyncSession = Depends(get_session)) -> Response:
    return await _proxy(request, "audio", session)


@router.post("/videos/generations")
async def videos_generations(request: Request, session: AsyncSession = Depends(get_session)) -> Response:
    return await _proxy(request, "video", session)
