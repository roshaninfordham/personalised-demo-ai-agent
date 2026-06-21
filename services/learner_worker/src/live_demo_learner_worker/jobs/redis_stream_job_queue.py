"""Redis Streams learner job queue."""

from __future__ import annotations

from typing import Any, cast

from redis.asyncio import Redis
from redis.exceptions import ResponseError
from redis.exceptions import TimeoutError as RedisTimeoutError

from live_demo_learner_worker.jobs.learner_job_queue import LearnerJobQueue, ReceivedLearnerJob
from live_demo_learner_worker.jobs.learner_job_types import LearnerJobEnvelope


class RedisStreamLearnerJobQueue(LearnerJobQueue):
    def __init__(
        self,
        redis: Redis[bytes],
        *,
        stream: str,
        dead_letter_stream: str,
        group: str,
        consumer: str,
        count: int,
        block_ms: int,
        maxlen: int,
    ) -> None:
        self._redis = redis
        self._stream = stream
        self._dead_letter_stream = dead_letter_stream
        self._group = group
        self._consumer = consumer
        self._count = count
        self._block_ms = block_ms
        self._maxlen = maxlen

    async def ensure_group(self) -> None:
        try:
            await self._redis.xgroup_create(self._stream, self._group, id="0", mkstream=True)
        except ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    async def enqueue(self, job: LearnerJobEnvelope) -> str:
        message_id: Any = await self._redis.xadd(
            self._stream,
            job.to_mapping(),
            maxlen=self._maxlen,
            approximate=True,
        )
        return _decode(message_id)

    async def read(self) -> tuple[ReceivedLearnerJob, ...]:
        try:
            response = await self._redis.xreadgroup(
                self._group,
                self._consumer,
                {self._stream: ">"},
                count=self._count,
                block=self._block_ms,
            )
        except RedisTimeoutError:
            return ()
        jobs: list[ReceivedLearnerJob] = []
        for _, messages in response:
            for message_id, fields in messages:
                decoded = {_decode(key): _decode(value) for key, value in fields.items()}
                jobs.append(
                    ReceivedLearnerJob(
                        message_id=_decode(message_id),
                        job=LearnerJobEnvelope.from_mapping(decoded),
                    )
                )
        return tuple(jobs)

    async def ack(self, message_id: str) -> None:
        xack = cast(Any, self._redis.xack)
        await xack(self._stream, self._group, message_id)

    async def dead_letter(self, received: ReceivedLearnerJob, error_code: str) -> str:
        payload = received.job.to_mapping()
        payload["error_code"] = error_code
        message_id: Any = await self._redis.xadd(
            self._dead_letter_stream,
            payload,
            maxlen=self._maxlen,
            approximate=True,
        )
        return _decode(message_id)


def _decode(value: bytes | str | object) -> str:
    if isinstance(value, bytes):
        return value.decode()
    return value if isinstance(value, str) else str(value)
