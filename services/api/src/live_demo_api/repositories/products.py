"""Product and guidance repositories."""

from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import Product, ProductGuidance
from live_demo_api.db.types import ProductGuidanceType


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
    ) -> Product:
        product = Product(
            organization_id=organization_id,
            product_name=product_name,
            product_url=product_url,
            default_persona=default_persona,
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

    async def add_guidance(
        self,
        *,
        organization_id: UUID,
        product_id: UUID,
        guidance_type: ProductGuidanceType,
        content: dict[str, object],
        title: str | None = None,
    ) -> ProductGuidance:
        guidance = ProductGuidance(
            organization_id=organization_id,
            product_id=product_id,
            guidance_type=guidance_type.value,
            title=title,
            content=content,
        )
        self._session.add(guidance)
        await self._session.flush()
        return guidance
