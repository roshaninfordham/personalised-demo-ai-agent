"""Organization repository."""

from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import Organization, User
from live_demo_api.db.types import UserRole


class OrganizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_organization(
        self, *, name: str, slug: str, plan: str = "free"
    ) -> Organization:
        organization = Organization(name=name, slug=slug, plan=plan)
        self._session.add(organization)
        await self._session.flush()
        return organization

    async def get_organization(self, organization_id: UUID) -> Organization | None:
        statement = select(Organization).where(
            Organization.organization_id == organization_id,
            Organization.deleted_at.is_(None),
        )
        return cast(Organization | None, await self._session.scalar(statement))

    async def create_user(
        self,
        *,
        organization_id: UUID,
        email: str,
        display_name: str | None = None,
        role: UserRole = UserRole.VIEWER,
    ) -> User:
        user = User(
            organization_id=organization_id,
            email=email.lower(),
            display_name=display_name,
            role=role.value,
        )
        self._session.add(user)
        await self._session.flush()
        return user
