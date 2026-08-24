import os
import redis.asyncio as aioredis
from app.config import settings

redis_client: aioredis.Redis = None
atomic_hold_script_sha = None
release_hold_script_sha = None

async def init_redis():
    global redis_client, atomic_hold_script_sha, release_hold_script_sha
    redis_client = aioredis.from_url(
        settings.REDIS_URL, 
        decode_responses=True, 
        encoding="utf-8"
    )
    
    # Load Lua scripts into Redis SHA cache
    lua_dir = os.path.join(os.path.dirname(__file__), "lua")
    
    atomic_hold_path = os.path.join(lua_dir, "atomic_hold.lua")
    if os.path.exists(atomic_hold_path):
        with open(atomic_hold_path, "r") as f:
            script_code = f.read()
            atomic_hold_script_sha = await redis_client.script_load(script_code)
            
    release_hold_path = os.path.join(lua_dir, "release_hold.lua")
    if os.path.exists(release_hold_path):
        with open(release_hold_path, "r") as f:
            script_code = f.read()
            release_hold_script_sha = await redis_client.script_load(script_code)

async def get_redis() -> aioredis.Redis:
    return redis_client

async def execute_atomic_hold(keys: list[str], hold_token: str, user_id: str, ttl_seconds: int):
    """Executes the atomic hold Lua script across multiple seat keys"""
    if not atomic_hold_script_sha:
        await init_redis()
    
    res = await redis_client.evalsha(
        atomic_hold_script_sha,
        len(keys),
        *keys,
        hold_token,
        user_id,
        str(ttl_seconds)
    )
    # Returns [status_code, detail] e.g. [1, "OK"] or [0, "hold:show_id:seat_id"]
    return res

async def execute_release_hold(keys: list[str], hold_token: str):
    """Executes the atomic release hold Lua script"""
    if not release_hold_script_sha:
        await init_redis()
        
    res = await redis_client.evalsha(
        release_hold_script_sha,
        len(keys),
        *keys,
        hold_token
    )
    return res
