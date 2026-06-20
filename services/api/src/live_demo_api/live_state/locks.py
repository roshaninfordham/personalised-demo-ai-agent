"""Redis lock helpers using compare-and-delete Lua release."""

from __future__ import annotations

from redis.asyncio import Redis

RELEASE_LOCK_SCRIPT = """
if redis.call("GET", KEYS[1]) == ARGV[1] then
  return redis.call("DEL", KEYS[1])
else
  return 0
end
"""


async def acquire_lock(redis: Redis[bytes], key: str, owner_id: str, ttl_ms: int) -> bool:
    if not key or not owner_id:
        raise ValueError("Lock key and owner_id must be non-empty")
    if ttl_ms <= 0:
        raise ValueError("ttl_ms must be positive")
    result = await redis.set(key, owner_id, nx=True, px=ttl_ms)
    return result is True


async def release_lock(redis: Redis[bytes], key: str, owner_id: str) -> bool:
    if not key or not owner_id:
        raise ValueError("Lock key and owner_id must be non-empty")
    result = await redis.eval(RELEASE_LOCK_SCRIPT, 1, key, owner_id)  # type: ignore[no-untyped-call]
    return int(result) == 1
