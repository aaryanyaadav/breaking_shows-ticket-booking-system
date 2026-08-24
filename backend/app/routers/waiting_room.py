import time
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from app.redis_client import get_redis
import redis.asyncio as aioredis
from app.schemas import UserResponse
from app.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/api/v1/shows", tags=["Virtual Waiting Room"])

@router.post("/{show_id}/queue/join")
async def join_waiting_room(
    show_id: str,
    current_user: User = Depends(get_current_user),
    redis: aioredis.Redis = Depends(get_redis)
):
    """
    Meters user into the sale queue.
    Adds user ID to Redis Sorted Set queue:show:{show_id}
    """
    queue_key = f"queue:show:{show_id}"
    user_id_str = str(current_user.id)
    now = time.time()

    # Check if already in queue
    rank = await redis.zrank(queue_key, user_id_str)
    if rank is None:
        await redis.zadd(queue_key, {user_id_str: now})
        rank = await redis.zrank(queue_key, user_id_str)

    total_waiting = await redis.zcard(queue_key)
    
    # If position <= 100, user is ELIGIBLE immediately for demo responsiveness
    status = "ELIGIBLE" if rank < 100 else "WAITING"

    return {
        "show_id": show_id,
        "user_id": user_id_str,
        "queue_position": rank + 1,
        "total_in_queue": total_waiting,
        "status": status,
        "estimated_wait_seconds": max(0, (rank // 10) * 5)
    }

@router.get("/{show_id}/queue/status")
async def check_queue_status(
    show_id: str,
    current_user: User = Depends(get_current_user),
    redis: aioredis.Redis = Depends(get_redis)
):
    queue_key = f"queue:show:{show_id}"
    user_id_str = str(current_user.id)

    rank = await redis.zrank(queue_key, user_id_str)
    if rank is None:
        return {
            "show_id": show_id,
            "status": "NOT_IN_QUEUE",
            "queue_position": 0
        }

    total_waiting = await redis.zcard(queue_key)
    status = "ELIGIBLE" if rank < 100 else "WAITING"

    return {
        "show_id": show_id,
        "user_id": user_id_str,
        "queue_position": rank + 1,
        "total_in_queue": total_waiting,
        "status": status,
        "estimated_wait_seconds": max(0, (rank // 10) * 5)
    }
