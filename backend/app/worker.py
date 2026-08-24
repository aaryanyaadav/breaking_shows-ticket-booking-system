import asyncio
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models import (
    Hold, HoldItem, ShowSeat, WaitlistEntry, WaitlistOffer, Notification,
    HoldStatus, SeatStatus, WaitlistStatus, OfferStatus
)
from app.redis_client import get_redis
from app.websockets import ws_manager
from app.config import settings

logger = logging.getLogger("worker")
logging.basicConfig(level=logging.INFO)

async def sweep_expired_holds():
    async with AsyncSessionLocal() as db:
        try:
            now = datetime.now(timezone.utc)
            stmt = select(Hold).options(
                selectinload(Hold.hold_items).selectinload(HoldItem.show_seat)
            ).where(
                Hold.status == HoldStatus.ACTIVE,
                Hold.expires_at < now
            )
            res = await db.execute(stmt)
            expired_holds = res.scalars().all()

            for hold in expired_holds:
                hold.status = HoldStatus.EXPIRED
                show_id_str = str(hold.show_id)
                freed_seat_ids = []

                # Also clear Redis keys
                redis = await get_redis()
                if redis:
                    redis_keys = [f"hold:{show_id_str}:{item.show_seat_id}" for item in hold.hold_items]
                    if redis_keys:
                        await redis.delete(*redis_keys)

                for item in hold.hold_items:
                    show_seat = item.show_seat
                    freed_seat_ids.append(str(show_seat.id))

                    # Category-aware waitlist check
                    wl_stmt = select(WaitlistEntry).where(
                        WaitlistEntry.show_id == hold.show_id,
                        WaitlistEntry.category_id == show_seat.category_id,
                        WaitlistEntry.status == WaitlistStatus.WAITING
                    ).order_by(WaitlistEntry.position.asc())
                    wl_res = await db.execute(wl_stmt)
                    next_waitlist = wl_res.scalars().first()

                    if next_waitlist:
                        # Offer to waitlisted customer!
                        show_seat.status = SeatStatus.OFFERED
                        show_seat.version += 1
                        next_waitlist.status = WaitlistStatus.OFFERED

                        offer = WaitlistOffer(
                            waitlist_entry_id=next_waitlist.id,
                            show_seat_id=show_seat.id,
                            status=OfferStatus.ACTIVE,
                            expires_at=now + timedelta(seconds=settings.OFFER_TTL_SECONDS)
                        )
                        db.add(offer)

                        # Notification
                        notif = Notification(
                            user_id=next_waitlist.user_id,
                            type="WAITLIST_OFFER",
                            channel="EMAIL",
                            reference_type="WAITLIST_OFFER",
                            reference_id=offer.id,
                            status="SENT",
                            sent_at=now
                        )
                        db.add(notif)
                    else:
                        show_seat.status = SeatStatus.AVAILABLE
                        show_seat.version += 1

                await db.commit()

                # Broadcast WebSocket update
                if freed_seat_ids:
                    await ws_manager.broadcast_seat_update(
                        show_id=show_id_str,
                        payload={
                            "event": "SEAT_STATUS_CHANGED",
                            "show_id": show_id_str,
                            "seat_ids": freed_seat_ids,
                            "status": "EXPIRED_RELEASED",
                            "timestamp": now.isoformat()
                        }
                    )
        except Exception as e:
            logger.error(f"Error in sweep_expired_holds: {e}")

async def sweep_expired_offers():
    async with AsyncSessionLocal() as db:
        try:
            now = datetime.now(timezone.utc)
            stmt = select(WaitlistOffer).options(
                selectinload(WaitlistOffer.waitlist_entry),
                selectinload(WaitlistOffer.show_seat)
            ).where(
                WaitlistOffer.status == OfferStatus.ACTIVE,
                WaitlistOffer.expires_at < now
            )
            res = await db.execute(stmt)
            expired_offers = res.scalars().all()

            for offer in expired_offers:
                offer.status = OfferStatus.EXPIRED
                entry = offer.waitlist_entry
                entry.status = WaitlistStatus.EXPIRED
                show_seat = offer.show_seat

                show_id = entry.show_id
                category_id = entry.category_id

                # Find NEXT customer in waitlist line for category!
                wl_stmt = select(WaitlistEntry).where(
                    WaitlistEntry.show_id == show_id,
                    WaitlistEntry.category_id == category_id,
                    WaitlistEntry.status == WaitlistStatus.WAITING
                ).order_by(WaitlistEntry.position.asc())
                wl_res = await db.execute(wl_stmt)
                next_in_line = wl_res.scalars().first()

                if next_in_line:
                    show_seat.status = SeatStatus.OFFERED
                    show_seat.version += 1
                    next_in_line.status = WaitlistStatus.OFFERED

                    new_offer = WaitlistOffer(
                        waitlist_entry_id=next_in_line.id,
                        show_seat_id=show_seat.id,
                        status=OfferStatus.ACTIVE,
                        expires_at=now + timedelta(seconds=settings.OFFER_TTL_SECONDS)
                    )
                    db.add(new_offer)

                    notif = Notification(
                        user_id=next_in_line.user_id,
                        type="WAITLIST_OFFER",
                        channel="EMAIL",
                        reference_type="WAITLIST_OFFER",
                        reference_id=new_offer.id,
                        status="SENT",
                        sent_at=now
                    )
                    db.add(notif)
                else:
                    show_seat.status = SeatStatus.AVAILABLE
                    show_seat.version += 1

                await db.commit()

                # Broadcast WebSocket update
                await ws_manager.broadcast_seat_update(
                    show_id=str(show_id),
                    payload={
                        "event": "SEAT_STATUS_CHANGED",
                        "show_id": str(show_id),
                        "seat_ids": [str(show_seat.id)],
                        "status": "OFFER_EXPIRED_ROLLOVER",
                        "timestamp": now.isoformat()
                    }
                )
        except Exception as e:
            logger.error(f"Error in sweep_expired_offers: {e}")

async def start_background_worker():
    logger.info("Background Worker Task Started (Hold Expiry & Waitlist Auto-Rollover Sweeper)")
    while True:
        await sweep_expired_holds()
        await sweep_expired_offers()
        await asyncio.sleep(5) # Runs sweep every 5 seconds
