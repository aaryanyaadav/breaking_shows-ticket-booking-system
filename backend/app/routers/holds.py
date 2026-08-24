import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import User, ShowSeat, Hold, HoldItem, HoldStatus, SeatStatus, WaitlistOffer, OfferStatus
from app.schemas import HoldCreateRequest, HoldResponse
from app.auth import get_current_user
from app.config import settings
from app.redis_client import execute_atomic_hold, execute_release_hold
from app.websockets import ws_manager

router = APIRouter(prefix="/api/v1/holds", tags=["Holds & Inventory"])

@router.post("", response_model=HoldResponse, status_code=status.HTTP_201_CREATED)
async def create_hold(
    req: HoldCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not req.show_seat_ids:
        raise HTTPException(status_code=400, detail="Must select at least one seat to hold")

    show_id_str = str(req.show_id)
    seat_ids_str = [str(sid) for sid in req.show_seat_ids]

    # 1. Fetch show_seats in DB to verify status and ownership
    stmt = select(ShowSeat).where(
        ShowSeat.show_id == req.show_id,
        ShowSeat.id.in_(req.show_seat_ids)
    )
    res = await db.execute(stmt)
    show_seats = res.scalars().all()

    if len(show_seats) != len(req.show_seat_ids):
        raise HTTPException(status_code=404, detail="One or more requested seats were not found for this show")

    for seat in show_seats:
        if seat.status == SeatStatus.BOOKED:
            raise HTTPException(status_code=409, detail=f"Seat {seat.id} is already BOOKED")
        elif seat.status == SeatStatus.HELD:
            raise HTTPException(status_code=409, detail=f"Seat {seat.id} is already HELD by another customer")
        elif seat.status == SeatStatus.OFFERED:
            # Check if current user is the owner of the active waitlist offer for this seat
            offer_stmt = select(WaitlistOffer).where(
                WaitlistOffer.show_seat_id == seat.id,
                WaitlistOffer.status == OfferStatus.ACTIVE
            ).options(selectinload(WaitlistOffer.waitlist_entry))
            offer_res = await db.execute(offer_stmt)
            offer = offer_res.scalar_one_or_none()
            if not offer or offer.waitlist_entry.user_id != current_user.id:
                raise HTTPException(status_code=409, detail="Seat is currently reserved for a waitlisted customer offer")

    # 2. Prepare Redis Keys & Hold Token
    hold_token = uuid.uuid4()
    redis_keys = [f"hold:{show_id_str}:{sid}" for sid in seat_ids_str]
    ttl = req.ttl_seconds or settings.DEFAULT_HOLD_TTL_SECONDS

    # 3. Execute Redis Lua Script for Atomic Multi-Seat Lock
    lua_res = await execute_atomic_hold(
        keys=redis_keys,
        hold_token=str(hold_token),
        user_id=str(current_user.id),
        ttl_seconds=ttl
    )

    if lua_res[0] == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Race condition detected! Seat '{lua_res[1]}' was just grabbed by another customer."
        )

    # 4. Save Durable State in PostgreSQL
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
    durable_hold = Hold(
        user_id=current_user.id,
        show_id=req.show_id,
        hold_token=hold_token,
        status=HoldStatus.ACTIVE,
        expires_at=expires_at
    )

    db.add(durable_hold)
    await db.flush()

    for seat in show_seats:
        hold_item = HoldItem(hold_id=durable_hold.id, show_seat_id=seat.id)
        db.add(hold_item)
        # Update show_seat state
        seat.status = SeatStatus.HELD
        seat.version += 1

    await db.commit()

    # 5. Broadcast real-time seat status update via WebSocket
    await ws_manager.broadcast_seat_update(
        show_id=show_id_str,
        payload={
            "event": "SEAT_STATUS_CHANGED",
            "show_id": show_id_str,
            "seat_ids": seat_ids_str,
            "status": "HELD",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    return HoldResponse(
        id=durable_hold.id,
        show_id=req.show_id,
        hold_token=hold_token,
        status=HoldStatus.ACTIVE,
        expires_at=expires_at,
        show_seat_ids=req.show_seat_ids
    )

@router.post("/{hold_id}/release")
async def release_hold(
    hold_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Hold).options(selectinload(Hold.hold_items)).where(Hold.id == hold_id)
    res = await db.execute(stmt)
    hold = res.scalar_one_or_none()

    if not hold or hold.user_id != current_user.id:
        raise HTTPException(status_code=44, detail="Hold not found or unauthorized")

    if hold.status != HoldStatus.ACTIVE:
        return {"message": f"Hold is already {hold.status.value}"}

    show_id_str = str(hold.show_id)
    seat_ids = [item.show_seat_id for item in hold.hold_items]
    seat_ids_str = [str(sid) for sid in seat_ids]
    redis_keys = [f"hold:{show_id_str}:{sid}" for sid in seat_ids_str]

    # Release in Redis
    await execute_release_hold(redis_keys, str(hold.hold_token))

    # Update DB state
    hold.status = HoldStatus.RELEASED
    hold.released_at = datetime.utcnow()

    # Revert show_seats status to AVAILABLE
    update_stmt = (
        update(ShowSeat)
        .where(ShowSeat.id.in_(seat_ids))
        .values(status=SeatStatus.AVAILABLE, version=ShowSeat.version + 1)
    )
    await db.execute(update_stmt)
    await db.commit()

    # Broadcast WebSocket update
    await ws_manager.broadcast_seat_update(
        show_id=show_id_str,
        payload={
            "event": "SEAT_STATUS_CHANGED",
            "show_id": show_id_str,
            "seat_ids": seat_ids_str,
            "status": "AVAILABLE",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    return {"message": "Hold released successfully", "released_seat_ids": seat_ids_str}
