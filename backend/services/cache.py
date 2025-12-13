import json
import logging
from typing import Any, Optional

import redis
from flask import current_app

logger = logging.getLogger(__name__)


def get_redis_client() -> redis.Redis:
    url = current_app.config["REDIS_URL"]
    return redis.Redis.from_url(url, decode_responses=True)


def get_cache(key: str) -> Optional[Any]:
    try:
        client = get_redis_client()
        value = client.get(key)
        if value is None:
            return None
        return json.loads(value)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Redis get failed: %s", exc)
        return None


def set_cache(key: str, value: Any, ttl: Optional[int] = None) -> None:
    try:
        client = get_redis_client()
        ttl_seconds = ttl or current_app.config["CACHE_TTL_SECONDS"]
        client.setex(key, ttl_seconds, json.dumps(value))
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Redis set failed: %s", exc)
