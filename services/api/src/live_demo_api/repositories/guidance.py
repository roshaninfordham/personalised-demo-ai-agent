"""Product guidance repository."""

from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import ProductGuidance


class GuidanceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        organization_id: UUID,
        product_id: UUID,
        guidance_type: str,
        content: dict[str, object],
        title: str | None = None,
        source_uri: str | None = None,
        created_by: UUID | None = None,
    ) -> ProductGuidance:
        row = ProductGuidance(
            organization_id=organization_id,
            product_id=product_id,
            guidance_type=guidance_type,
            title=title,
            content=content,
            source_uri=source_uri,
            created_by=created_by,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get(
        self,
        *,
        organization_id: UUID,
        product_id: UUID,
        guidance_id: UUID,
    ) -> ProductGuidance | None:
        statement = select(ProductGuidance).where(
            ProductGuidance.organization_id == organization_id,
            ProductGuidance.product_id == product_id,
            ProductGuidance.guidance_id == guidance_id,
            ProductGuidance.deleted_at.is_(None),
        )
        return cast(ProductGuidance | None, await self._session.scalar(statement))

    async def list(
        self,
        *,
        organization_id: UUID,
        product_id: UUID,
        limit: int,
        guidance_type: str | None = None,
        cursor_created_at: datetime | None = None,
        cursor_guidance_id: UUID | None = None,
    ) -> list[ProductGuidance]:
        statement = select(ProductGuidance).where(
            ProductGuidance.organization_id == organization_id,
            ProductGuidance.product_id == product_id,
            ProductGuidance.deleted_at.is_(None),
        )
        if guidance_type is not None:
            statement = statement.where(ProductGuidance.guidance_type == guidance_type)
        if cursor_created_at is not None and cursor_guidance_id is not None:
            statement = statement.where(
                sa.or_(
                    ProductGuidance.created_at < cursor_created_at,
                    sa.and_(
                        ProductGuidance.created_at == cursor_created_at,
                        ProductGuidance.guidance_id < cursor_guidance_id,
                    ),
                )
            )
        statement = statement.order_by(
            ProductGuidance.created_at.desc(), ProductGuidance.guidance_id.desc()
        ).limit(limit)
        return list((await self._session.scalars(statement)).all())

    async def update(
        self,
        *,
        organization_id: UUID,
        product_id: UUID,
        guidance_id: UUID,
        patch: dict[str, object],
    ) -> ProductGuidance | None:
        row = await self.get(
            organization_id=organization_id,
            product_id=product_id,
            guidance_id=guidance_id,
        )
        if row is None:
            return None
        for field in ("guidance_type", "title", "content", "source_uri"):
            if field in patch:
                setattr(row, field, patch[field])
        await self._session.flush()
        return row

    async def soft_delete(
        self, *, organization_id: UUID, product_id: UUID, guidance_id: UUID
    ) -> bool:
        row = await self.get(
            organization_id=organization_id,
            product_id=product_id,
            guidance_id=guidance_id,
        )
        if row is None:
            return False
        row.deleted_at = datetime.now(UTC)
        await self._session.flush()
        return True
