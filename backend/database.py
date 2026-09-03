import json
import logging
import time
from typing import Optional, Dict, Any, List
import redis
import redis.asyncio as aioredis

from backend.config import settings

logger = logging.getLogger("ai_access.database")

class InMemoryStore:
    """In-memory key-value and document store fallback for local development or when Redis is offline."""
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._sets: Dict[str, set] = {}

    def get(self, key: str) -> Optional[str]:
        val = self._data.get(key)
        if val is None:
            return None
        if isinstance(val, (dict, list)):
            return json.dumps(val)
        return str(val)

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        if isinstance(value, (dict, list)):
            self._data[key] = json.dumps(value)
        else:
            self._data[key] = str(value)
        return True

    def delete(self, *keys: str) -> int:
        count = 0
        for k in keys:
            if k in self._data:
                del self._data[k]
                count += 1
        return count

    def keys(self, pattern: str = "*") -> List[str]:
        import fnmatch
        return [k for k in self._data.keys() if fnmatch.fnmatch(k, pattern)]

    def sadd(self, set_name: str, *members: str) -> int:
        if set_name not in self._sets:
            self._sets[set_name] = set()
        count = 0
        for m in members:
            if m not in self._sets[set_name]:
                self._sets[set_name].add(m)
                count += 1
        return count

    def smembers(self, set_name: str) -> set:
        return self._sets.get(set_name, set())

    def ping(self) -> bool:
        return True

class DatabaseManager:
    """Manages Redis connection, RediSearch vector indexes, and fallbacks."""
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.async_redis: Optional[aioredis.Redis] = None
        self.memory_store: InMemoryStore = InMemoryStore()
        self.is_connected_to_redis: bool = False

    def connect(self):
        """Attempts to connect to Redis Stack."""
        try:
            client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=2.0
            )
            client.ping()
            self.redis_client = client
            self.is_connected_to_redis = True
            logger.info("Successfully connected to Redis Stack at %s", settings.REDIS_URL)
        except Exception as e:
            logger.warning(
                "Could not connect to Redis at %s: %s. Using In-Memory fallback store: %s",
                settings.REDIS_URL, e, settings.REDIS_FALLBACK_MEMORY
            )
            self.is_connected_to_redis = False

    async def connect_async(self):
        """Initializes asynchronous Redis client connection."""
        try:
            client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=2.0
            )
            await client.ping()
            self.async_redis = client
            self.is_connected_to_redis = True
            logger.info("Successfully connected async Redis Stack at %s", settings.REDIS_URL)
        except Exception as e:
            logger.warning("Async Redis connection failed (%s). Continuing with memory fallback.", e)
            self.is_connected_to_redis = False

    # --- Key-Value & JSON Operations ---

    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieves and deserializes JSON from Redis or fallback store."""
        try:
            if self.is_connected_to_redis and self.redis_client:
                data = self.redis_client.get(key)
            else:
                data = self.memory_store.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error("Error fetching JSON key '%s': %s", key, e)
        return None

    def set_json(self, key: str, value: Dict[str, Any], ex: Optional[int] = None) -> bool:
        """Serializes and stores JSON in Redis or fallback store."""
        try:
            payload = json.dumps(value)
            if self.is_connected_to_redis and self.redis_client:
                self.redis_client.set(key, payload, ex=ex)
            else:
                self.memory_store.set(key, payload, ex=ex)
            self.invalidate_cache()
            return True
        except Exception as e:
            logger.error("Error saving JSON key '%s': %s", key, e)
            return False

    def delete_key(self, key: str) -> bool:
        """Deletes a key from Redis or fallback store."""
        try:
            if self.is_connected_to_redis and self.redis_client:
                self.redis_client.delete(key)
            else:
                self.memory_store.delete(key)
            self.invalidate_cache()
            return True
        except Exception as e:
            logger.error("Error deleting key '%s': %s", key, e)
            return False

    def list_keys(self, pattern: str) -> List[str]:
        """Lists all keys matching a pattern."""
        try:
            if self.is_connected_to_redis and self.redis_client:
                return [k for k in self.redis_client.keys(pattern)]
            else:
                return self.memory_store.keys(pattern)
        except Exception as e:
            logger.error("Error listing keys with pattern '%s': %s", pattern, e)
            return []

    def get_many_json(self, keys: List[str]) -> List[Dict[str, Any]]:
        """Batch fetches multiple JSON documents in a single Redis MGET roundtrip."""
        if not keys:
            return []
        results = []
        try:
            if self.is_connected_to_redis and self.redis_client:
                raw_values = self.redis_client.mget(keys)
                for raw in raw_values:
                    if raw:
                        try:
                            results.append(json.loads(raw))
                        except Exception:
                            pass
            else:
                for k in keys:
                    v = self.memory_store.get(k)
                    if v:
                        try:
                            results.append(json.loads(v))
                        except Exception:
                            pass
        except Exception as e:
            logger.error("Error batch fetching keys: %s", e)
        return results

    def get_all_by_pattern(self, pattern: str, cache_ttl_sec: float = 2.0) -> List[Dict[str, Any]]:
        """High-speed batch fetch of all records matching pattern with automatic short TTL caching."""
        now = time.time()
        if hasattr(self, '_pattern_cache') and pattern in self._pattern_cache:
            cache_time, cached_data = self._pattern_cache[pattern]
            if (now - cache_time) < cache_ttl_sec:
                return cached_data

        keys = self.list_keys(pattern)
        data = self.get_many_json(keys)
        if not hasattr(self, '_pattern_cache'):
            self._pattern_cache = {}
        self._pattern_cache[pattern] = (now, data)
        return data

    def invalidate_cache(self):
        """Invalidates in-memory pattern query cache."""
        if hasattr(self, '_pattern_cache'):
            self._pattern_cache.clear()

    # --- Health Check ---

    def health_check(self) -> Dict[str, Any]:
        """Returns database connectivity and status."""
        connected = False
        try:
            if self.is_connected_to_redis and self.redis_client:
                connected = bool(self.redis_client.ping())
        except Exception:
            connected = False

        return {
            "redis_connected": connected,
            "mode": "redis" if connected else "in_memory_fallback",
            "fallback_enabled": settings.REDIS_FALLBACK_MEMORY,
            "timestamp": time.time()
        }

    # --- Initial Data Seeding ---

    def seed_initial_data(self):
        """Seeds default admin credentials and default camera if not already set."""
        from backend.auth import hash_password

        admin_key = f"auth:user:{settings.DEFAULT_ADMIN_USERNAME}"
        if not self.get_json(admin_key):
            admin_data = {
                "username": settings.DEFAULT_ADMIN_USERNAME,
                "email": settings.DEFAULT_ADMIN_EMAIL,
                "password_hash": hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                "role": "admin",
                "is_active": True,
                "created_at": time.time()
            }
            self.set_json(admin_key, admin_data)
            logger.info("Default admin user created: %s", settings.DEFAULT_ADMIN_USERNAME)

        default_cam_key = f"cam:{settings.DEFAULT_CAMERA_ID}"
        if not self.get_json(default_cam_key):
            cam_data = {
                "camera_id": settings.DEFAULT_CAMERA_ID,
                "name": "Front Door",
                "location": "Main Entrance",
                "floor": "Ground",
                "zone": "Entry Zone A",
                "ip_address": "192.168.1.100",
                "rtsp_url": settings.DEFAULT_CAMERA_RTSP,
                "status": "ACTIVE",
                "is_linked": True,
                "linked_at": time.time(),
                "last_heartbeat": time.time(),
                "error_message": "",
                "fps": 30.0
            }
            self.set_json(default_cam_key, cam_data)
            logger.info("Default camera initialized: %s", settings.DEFAULT_CAMERA_ID)

        default_zone_key = "zone:entry-zone-a"
        if not self.get_json(default_zone_key):
            zone_data = {
                "zone_id": "entry-zone-a",
                "name": "Entry Zone A",
                "description": "Main entrance security perimeter",
                "camera_ids": [settings.DEFAULT_CAMERA_ID]
            }
            self.set_json(default_zone_key, zone_data)
            logger.info("Default zone initialized: Entry Zone A")

db = DatabaseManager()
