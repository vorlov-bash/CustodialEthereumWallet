from redis import asyncio as aioredis

from src.core.config import settings

redis = aioredis.from_url(settings.REDIS_URI)
