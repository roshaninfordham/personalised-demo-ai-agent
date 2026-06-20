"""Artifact metadata repository."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import ArtifactObject
from live_demo_api.db.types import ArtifactKind
from live_demo_api.storage.artifact_store import StoredObject


class ArtifactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def insert_artifact(
        self,
        *,
        organization_id: UUID,
        stored_object: StoredObject,
        kind: ArtifactKind,
        session_id: UUID | None = None,
        product_id: UUID | None = None,
        created_by: str | None = None,
        pii_level: str = "unknown",
    ) -> ArtifactObject:
        artifact = ArtifactObject(
            organization_id=organization_id,
            session_id=session_id,
            product_id=product_id,
            kind=kind.value,
            bucket=stored_object.bucket,
            object_key=stored_object.object_key,
            content_type=stored_object.content_type,
            size_bytes=stored_object.size_bytes,
            sha256_hex=stored_object.sha256_hex,
            created_by=created_by,
            pii_level=pii_level,
        )
        self._session.add(artifact)
        await self._session.flush()
        return artifact

    async def mark_deleted(self, *, organization_id: UUID, artifact_id: UUID) -> None:
        artifact = await self._session.get(ArtifactObject, artifact_id)
        if artifact is None or artifact.organization_id != organization_id:
            return
        artifact.deleted_at = datetime.now(UTC)

    async def find_by_session(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
        kind: ArtifactKind | None = None,
    ) -> list[ArtifactObject]:
        statement = select(ArtifactObject).where(
            ArtifactObject.organization_id == organization_id,
            ArtifactObject.session_id == session_id,
            ArtifactObject.deleted_at.is_(None),
        )
        if kind is not None:
            statement = statement.where(ArtifactObject.kind == kind.value)
        statement = statement.order_by(ArtifactObject.created_at.desc())
        return list((await self._session.scalars(statement)).all())
