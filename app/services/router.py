from dataclasses import dataclass

from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.aliases import FIXED_ALIASES
from app.db.models import InvocationAttempt, ProviderModel


@dataclass(frozen=True)
class ModelCandidate:
    model_name: str
    capability: str


class ModelRouter:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def resolve(self, requested_model: str, endpoint_capability: str) -> list[ModelCandidate]:
        alias_capability = FIXED_ALIASES.get(requested_model)
        if alias_capability:
            capability = alias_capability
            result = await self.session.execute(
                select(ProviderModel)
                .where(ProviderModel.enabled.is_(True), ProviderModel.capability == capability)
                .order_by(
                    case((ProviderModel.manual_priority.is_(None), 1), else_=0),
                    ProviderModel.manual_priority.asc(),
                    ProviderModel.default_priority.asc(),
                    ProviderModel.model_name.asc(),
                )
            )
            return [
                ModelCandidate(model_name=model.model_name, capability=model.capability)
                for model in result.scalars().all()
            ]

        return [ModelCandidate(model_name=requested_model, capability=endpoint_capability)]

    async def record_attempt(
        self,
        *,
        request_id: str,
        requested_model: str,
        candidate: ModelCandidate,
        status_code: int | None,
        success: bool,
        latency_ms: int,
        error: str,
    ) -> None:
        self.session.add(
            InvocationAttempt(
                request_id=request_id,
                requested_model=requested_model,
                routed_model=candidate.model_name,
                capability=candidate.capability,
                status_code=status_code,
                success=success,
                latency_ms=latency_ms,
                error=error,
            )
        )
        await self.session.commit()
