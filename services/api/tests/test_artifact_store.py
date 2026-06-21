from __future__ import annotations

from uuid import uuid4

import pytest
from botocore.exceptions import ClientError  # type: ignore[import-untyped]
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import DemoSession, Organization, Product
from live_demo_api.db.session import dispose_database_engine, get_sessionmaker
from live_demo_api.db.types import ArtifactKind
from live_demo_api.repositories.artifacts import ArtifactRepository
from live_demo_api.repositories.demo_sessions import DemoSessionRepository
from live_demo_api.repositories.organizations import OrganizationRepository
from live_demo_api.repositories.products import ProductRepository
from live_demo_api.storage.bucket_initializer import ensure_artifact_bucket_if_allowed
from live_demo_api.storage.object_keys import generated_report_key, screenshot_key
from live_demo_api.storage.s3_artifact_store import S3ArtifactStore

pytestmark = pytest.mark.integration


def test_object_key_generation_rejects_invalid_values() -> None:
    valid_uuid = str(uuid4())
    with pytest.raises(ValueError):
        screenshot_key("not-a-uuid", valid_uuid, valid_uuid)
    with pytest.raises(ValueError):
        screenshot_key(valid_uuid, valid_uuid, valid_uuid, extension="exe")
    with pytest.raises(ValueError):
        generated_report_key(valid_uuid, valid_uuid, "../secret")


async def _create_session(session: AsyncSession) -> tuple[Organization, Product, DemoSession]:
    organization_repo = OrganizationRepository(session)
    product_repo = ProductRepository(session)
    demo_session_repo = DemoSessionRepository(session)

    organization = await organization_repo.create_organization(
        name="Artifact Test",
        slug=f"artifact-test-{uuid4().hex}",
    )
    product = await product_repo.create_product(
        organization_id=organization.organization_id,
        product_name="Artifact Product",
        product_url="https://example.test",
    )
    demo_session = await demo_session_repo.create_session(
        organization_id=organization.organization_id,
        product_id=product.product_id,
        start_url=product.product_url,
    )
    return organization, product, demo_session


async def test_s3_artifact_store_and_metadata_repository() -> None:
    store = S3ArtifactStore()
    object_key = screenshot_key(str(uuid4()), str(uuid4()), str(uuid4()))
    try:
        await ensure_artifact_bucket_if_allowed(store)

        content = b"x" * 200_000
        stored = await store.put_bytes(
            object_key,
            content,
            "image/webp",
            metadata={"phase": "2"},
        )
        assert stored.sha256_hex
        assert await store.get_bytes(object_key) == content
        assert await store.create_presigned_get_url(object_key, 60)

        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session, session.begin():
            organization, product, demo_session = await _create_session(session)
            artifact_repo = ArtifactRepository(session)
            artifact = await artifact_repo.insert_artifact(
                organization_id=organization.organization_id,
                session_id=demo_session.session_id,
                product_id=product.product_id,
                stored_object=stored,
                kind=ArtifactKind.SCREENSHOT,
            )
            found = await artifact_repo.find_by_session(
                organization_id=organization.organization_id,
                session_id=demo_session.session_id,
                kind=ArtifactKind.SCREENSHOT,
            )
            assert found[0].artifact_id == artifact.artifact_id

        await store.delete_object(object_key)
        with pytest.raises(ClientError):
            await store.get_bytes(object_key)
    finally:
        await dispose_database_engine()
