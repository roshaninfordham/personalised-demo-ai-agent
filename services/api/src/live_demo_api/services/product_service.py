"""Product API business logic."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.config import get_settings
from live_demo_api.errors import NotFoundError
from live_demo_api.events.event_bus import EventBus
from live_demo_api.pagination import clamp_limit, decode_cursor, encode_cursor
from live_demo_api.repositories.products import ProductRepository
from live_demo_api.security import Principal, RequestContext, normalize_product_url
from live_demo_api.services.audit_service import AuditService, publish_event
from live_demo_api.services.mappers import product_to_response
from live_demo_contracts.common import (
    CreateProductRequest,
    ListProductsResponse,
    ProductResponse,
    UpdateProductRequest,
)


def _cursor_parts(cursor: str | None) -> tuple[datetime | None, UUID | None]:
    if cursor is None:
        return None, None
    decoded = decode_cursor(cursor, max_length=get_settings().max_cursor_length)
    if "created_at" not in decoded or "id" not in decoded:
        return None, None
    return datetime.fromisoformat(decoded["created_at"]), UUID(decoded["id"])


class ProductService:
    def __init__(self) -> None:
        self._audit = AuditService()

    async def create_product(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        principal: Principal,
        request: CreateProductRequest,
        request_context: RequestContext,
    ) -> ProductResponse:
        settings = get_settings()
        normalized_url = normalize_product_url(request.product_url, settings)
        async with db.begin():
            await self._audit.ensure_local_organization(db, principal)
            product = await ProductRepository(db).create_product(
                organization_id=principal.organization_id,
                product_name=request.product_name,
                product_url=normalized_url,
                default_persona=request.default_persona,
                product_summary=request.product_summary,
                configuration=(
                    request.configuration.model_dump(mode="json") if request.configuration else {}
                ),
            )
            await self._audit.audit(
                db,
                principal=principal,
                action="product.create",
                resource_type="product",
                resource_id=product.product_id,
            )
        response = product_to_response(product)
        await publish_event(
            event_bus,
            organization_id=principal.organization_id,
            session_id=None,
            event_type="product.created",
            request_context=request_context,
            payload={"product_id": str(product.product_id)},
        )
        return response

    async def get_product(
        self, db: AsyncSession, principal: Principal, product_id: UUID
    ) -> ProductResponse:
        product = await ProductRepository(db).get_product(
            organization_id=principal.organization_id, product_id=product_id
        )
        if product is None:
            raise NotFoundError("Product not found.", code="product_not_found")
        return product_to_response(product)

    async def list_products(
        self,
        db: AsyncSession,
        principal: Principal,
        *,
        limit: int | None,
        cursor: str | None,
    ) -> ListProductsResponse:
        settings = get_settings()
        page_limit = clamp_limit(
            limit, default=settings.default_page_limit, maximum=settings.max_page_limit
        )
        cursor_created_at, cursor_product_id = _cursor_parts(cursor)
        rows = await ProductRepository(db).list_products(
            organization_id=principal.organization_id,
            limit=page_limit + 1,
            cursor_created_at=cursor_created_at,
            cursor_product_id=cursor_product_id,
        )
        next_cursor = None
        if len(rows) > page_limit:
            last = rows[page_limit - 1]
            next_cursor = encode_cursor(
                {"created_at": last.created_at.isoformat(), "id": str(last.product_id)}
            )
            rows = rows[:page_limit]
        return ListProductsResponse(
            items=[product_to_response(row) for row in rows], next_cursor=next_cursor
        )

    async def update_product(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        principal: Principal,
        product_id: UUID,
        request: UpdateProductRequest,
        request_context: RequestContext,
    ) -> ProductResponse:
        patch = request.model_dump(exclude_unset=True, mode="json")
        if "product_url" in patch and isinstance(patch["product_url"], str):
            patch["product_url"] = normalize_product_url(patch["product_url"], get_settings())
        async with db.begin():
            product = await ProductRepository(db).update_product(
                organization_id=principal.organization_id,
                product_id=product_id,
                patch=patch,
            )
            if product is None:
                raise NotFoundError("Product not found.", code="product_not_found")
            await self._audit.audit(
                db,
                principal=principal,
                action="product.update",
                resource_type="product",
                resource_id=product.product_id,
            )
        response = product_to_response(product)
        await publish_event(
            event_bus,
            organization_id=principal.organization_id,
            session_id=None,
            event_type="product.updated",
            request_context=request_context,
            payload={"product_id": str(product.product_id)},
        )
        return response

    async def delete_product(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        principal: Principal,
        product_id: UUID,
        request_context: RequestContext,
    ) -> None:
        async with db.begin():
            deleted = await ProductRepository(db).soft_delete_product(
                organization_id=principal.organization_id, product_id=product_id
            )
            if not deleted:
                raise NotFoundError("Product not found.", code="product_not_found")
            await self._audit.audit(
                db,
                principal=principal,
                action="product.delete",
                resource_type="product",
                resource_id=product_id,
            )
        await publish_event(
            event_bus,
            organization_id=principal.organization_id,
            session_id=None,
            event_type="product.deleted",
            request_context=request_context,
            payload={"product_id": str(product_id)},
        )
