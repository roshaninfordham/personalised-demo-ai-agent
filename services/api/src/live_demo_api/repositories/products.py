"""Product repositories."""

from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import Product


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_product(
        self,
        *,
        organization_id: UUID,
        product_name: str,
        product_url: str,
        default_persona: str | None = None,
        product_summary: str | None = None,
        configuration: dict[str, object] | None = None,
    ) -> Product:
        product = Product(
            organization_id=organization_id,
            product_name=product_name,
            product_url=product_url,
            default_persona=default_persona,
            product_summary=product_summary,
            configuration=configuration or {},
        )
        self._session.add(product)
        await self._session.flush()
        return product

    async def get_product(self, *, organization_id: UUID, product_id: UUID) -> Product | None:
        statement = select(Product).where(
            Product.organization_id == organization_id,
            Product.product_id == product_id,
            Product.deleted_at.is_(None),
        )
        return cast(Product | None, await self._session.scalar(statement))

    async def list_products(
        self,
        *,
        organization_id: UUID,
        limit: int,
        cursor_created_at: datetime | None = None,
        cursor_product_id: UUID | None = None,
    ) -> list[Product]:
        statement = select(Product).where(
            Product.organization_id == organization_id,
            Product.deleted_at.is_(None),
        )
        if cursor_created_at is not None and cursor_product_id is not None:
            statement = statement.where(
                sa.or_(
                    Product.created_at < cursor_created_at,
                    sa.and_(
                        Product.created_at == cursor_created_at,
                        Product.product_id < cursor_product_id,
                    ),
                )
            )
        statement = statement.order_by(Product.created_at.desc(), Product.product_id.desc()).limit(
            limit
        )
        return list((await self._session.scalars(statement)).all())

    async def update_product(
        self,
        *,
        organization_id: UUID,
        product_id: UUID,
        patch: dict[str, object],
    ) -> Product | None:
        product = await self.get_product(organization_id=organization_id, product_id=product_id)
        if product is None:
            return None
        for field in (
            "product_name",
            "product_url",
            "default_persona",
            "product_summary",
            "configuration",
        ):
            if field in patch:
                setattr(product, field, patch[field])
        await self._session.flush()
        return product

    async def soft_delete_product(self, *, organization_id: UUID, product_id: UUID) -> bool:
        product = await self.get_product(organization_id=organization_id, product_id=product_id)
        if product is None:
            return False
        product.deleted_at = datetime.now(UTC)
        await self._session.flush()
        return True
