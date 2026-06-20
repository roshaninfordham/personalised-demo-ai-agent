"""Product guidance API business logic."""

from __future__ import annotations

from datetime import datetime
from typing import cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.config import get_settings
from live_demo_api.errors import NotFoundError, ValidationAppError
from live_demo_api.events.event_bus import EventBus
from live_demo_api.pagination import clamp_limit, decode_cursor, encode_cursor
from live_demo_api.repositories.guidance import GuidanceRepository
from live_demo_api.repositories.products import ProductRepository
from live_demo_api.security import (
    Principal,
    RequestContext,
    normalize_product_url,
    serialized_json_size,
    validate_no_secret_keys,
)
from live_demo_api.services.audit_service import AuditService, publish_event
from live_demo_api.services.mappers import guidance_to_response
from live_demo_contracts.common import (
    CreateProductGuidanceRequest,
    ListProductGuidanceResponse,
    ProductGuidanceResponse,
    UpdateProductGuidanceRequest,
)


def _cursor_parts(cursor: str | None) -> tuple[datetime | None, UUID | None]:
    if cursor is None:
        return None, None
    decoded = decode_cursor(cursor, max_length=get_settings().max_cursor_length)
    if "created_at" not in decoded or "id" not in decoded:
        return None, None
    return datetime.fromisoformat(decoded["created_at"]), UUID(decoded["id"])


class GuidanceService:
    def __init__(self) -> None:
        self._audit = AuditService()

    async def _ensure_product(
        self, db: AsyncSession, principal: Principal, product_id: UUID
    ) -> None:
        product = await ProductRepository(db).get_product(
            organization_id=principal.organization_id, product_id=product_id
        )
        if product is None:
            raise NotFoundError("Product not found.", code="product_not_found")

    def _validate_content(
        self, request: CreateProductGuidanceRequest | UpdateProductGuidanceRequest
    ) -> None:
        settings = get_settings()
        content = getattr(request, "content", None)
        if content is None:
            return
        if serialized_json_size(content) > settings.guidance_max_content_bytes:
            raise ValidationAppError("Guidance content is too large.", code="guidance_too_large")
        validate_no_secret_keys(
            content,
            max_depth=settings.guidance_max_json_depth,
            max_keys=settings.guidance_max_json_keys,
        )
        guidance_type = getattr(request, "guidance_type", None)
        if str(guidance_type) == "forbidden_actions":
            never_click = content.get("never_click")
            if not isinstance(never_click, list) or not all(
                isinstance(item, str) for item in never_click
            ):
                raise ValidationAppError(
                    "Forbidden actions guidance must include never_click strings.",
                    code="invalid_forbidden_actions_guidance",
                )

    async def create_guidance(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        principal: Principal,
        product_id: UUID,
        request: CreateProductGuidanceRequest,
        request_context: RequestContext,
    ) -> ProductGuidanceResponse:
        self._validate_content(request)
        source_uri = (
            normalize_product_url(request.source_uri, get_settings())
            if request.source_uri
            else None
        )
        async with db.begin():
            await self._ensure_product(db, principal, product_id)
            row = await GuidanceRepository(db).create(
                organization_id=principal.organization_id,
                product_id=product_id,
                guidance_type=str(request.guidance_type),
                title=request.title,
                content=cast(dict[str, object], request.content),
                source_uri=source_uri,
                created_by=principal.user_id,
            )
            await self._audit.audit(
                db,
                principal=principal,
                action="product_guidance.create",
                resource_type="product_guidance",
                resource_id=row.guidance_id,
            )
        await publish_event(
            event_bus,
            organization_id=principal.organization_id,
            session_id=None,
            event_type="product_guidance.created",
            request_context=request_context,
            payload={"product_id": str(product_id), "guidance_id": str(row.guidance_id)},
        )
        return guidance_to_response(row)

    async def get_guidance(
        self, db: AsyncSession, principal: Principal, product_id: UUID, guidance_id: UUID
    ) -> ProductGuidanceResponse:
        row = await GuidanceRepository(db).get(
            organization_id=principal.organization_id,
            product_id=product_id,
            guidance_id=guidance_id,
        )
        if row is None:
            raise NotFoundError("Guidance not found.", code="guidance_not_found")
        return guidance_to_response(row)

    async def list_guidance(
        self,
        db: AsyncSession,
        principal: Principal,
        product_id: UUID,
        *,
        guidance_type: str | None,
        limit: int | None,
        cursor: str | None,
    ) -> ListProductGuidanceResponse:
        await self._ensure_product(db, principal, product_id)
        settings = get_settings()
        page_limit = clamp_limit(
            limit, default=settings.default_page_limit, maximum=settings.max_page_limit
        )
        cursor_created_at, cursor_guidance_id = _cursor_parts(cursor)
        rows = await GuidanceRepository(db).list(
            organization_id=principal.organization_id,
            product_id=product_id,
            guidance_type=guidance_type,
            limit=page_limit + 1,
            cursor_created_at=cursor_created_at,
            cursor_guidance_id=cursor_guidance_id,
        )
        next_cursor = None
        if len(rows) > page_limit:
            last = rows[page_limit - 1]
            next_cursor = encode_cursor(
                {"created_at": last.created_at.isoformat(), "id": str(last.guidance_id)}
            )
            rows = rows[:page_limit]
        return ListProductGuidanceResponse(
            items=[guidance_to_response(row) for row in rows],
            next_cursor=next_cursor,
        )

    async def update_guidance(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        principal: Principal,
        product_id: UUID,
        guidance_id: UUID,
        request: UpdateProductGuidanceRequest,
        request_context: RequestContext,
    ) -> ProductGuidanceResponse:
        self._validate_content(request)
        patch = request.model_dump(exclude_unset=True, mode="json")
        if "source_uri" in patch and isinstance(patch["source_uri"], str):
            patch["source_uri"] = normalize_product_url(patch["source_uri"], get_settings())
        async with db.begin():
            row = await GuidanceRepository(db).update(
                organization_id=principal.organization_id,
                product_id=product_id,
                guidance_id=guidance_id,
                patch=patch,
            )
            if row is None:
                raise NotFoundError("Guidance not found.", code="guidance_not_found")
            await self._audit.audit(
                db,
                principal=principal,
                action="product_guidance.update",
                resource_type="product_guidance",
                resource_id=row.guidance_id,
            )
        await publish_event(
            event_bus,
            organization_id=principal.organization_id,
            session_id=None,
            event_type="product_guidance.updated",
            request_context=request_context,
            payload={"product_id": str(product_id), "guidance_id": str(guidance_id)},
        )
        return guidance_to_response(row)

    async def delete_guidance(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        principal: Principal,
        product_id: UUID,
        guidance_id: UUID,
        request_context: RequestContext,
    ) -> None:
        async with db.begin():
            deleted = await GuidanceRepository(db).soft_delete(
                organization_id=principal.organization_id,
                product_id=product_id,
                guidance_id=guidance_id,
            )
            if not deleted:
                raise NotFoundError("Guidance not found.", code="guidance_not_found")
            await self._audit.audit(
                db,
                principal=principal,
                action="product_guidance.delete",
                resource_type="product_guidance",
                resource_id=guidance_id,
            )
        await publish_event(
            event_bus,
            organization_id=principal.organization_id,
            session_id=None,
            event_type="product_guidance.deleted",
            request_context=request_context,
            payload={"product_id": str(product_id), "guidance_id": str(guidance_id)},
        )
