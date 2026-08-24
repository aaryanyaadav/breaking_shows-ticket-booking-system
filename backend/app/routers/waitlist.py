import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import (
    User, WaitlistEntry, WaitlistOffer, SeatCategory, ShowSeat, Hold, HoldItem,
    WaitlistStatus, OfferStatus, SeatStatus, HoldStatus
)
from app.schemas import JoinWaitlistRequest, WaitlistEntryResponse, WaitlistOfferResponse
from app.auth import get_current_user
from app.config import settings

router = APIRouter(prefix="/api/v1/waitlist", tags=["Category-Aware Waitlist"])

@router.post("/join", response_model=WaitlistEntryResponse, status_code=status.HTTP_201_CREATED)
async def join_waitlist(
    req: JoinWaitlistRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Check if user already has active waitlist entry for this show & category
    stmt = select(WaitlistEntry).where(
        WaitlistEntry.show_id == req.show_id,
        WaitlistEntry.category_id == req.category_id,
        WaitlistEntry.user_id == current_user.id,
        WaitlistEntry.status.in_([WaitlistStatus.WAITING, WaitlistStatus.OFFERED])
    )
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()

    if existing:
        cat_stmt = select(SeatCategory).where(SeatCategory.id == req.category_id)
        cat_res = await db.execute(cat_stmt)
        cat = cat_res.scalar_one_or_none()
        resp = WaitlistEntryResponse.model_validate(existing)
        resp.category_name = cat.name if cat else "Category"
        return resp

    # Calculate position
    pos_stmt = select(func.count(WaitlistEntry.id)).where(
        WaitlistEntry.show_id == req.show_id,
        WaitlistEntry.category_id == req.category_id,
        WaitlistEntry.status == WaitlistStatus.WAITING
    )
    pos_res = await db.execute(pos_stmt)
    current_count = pos_res.scalar() or 0
    next_position = current_count + 1

    entry = WaitlistEntry(
        show_id=req.show_id,
        category_id=req.category_id,
        user_id=current_user.id,
        position=next_position,
        status=WaitlistStatus.WAITING
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    cat_stmt = select(SeatCategory).where(SeatCategory.id == req.category_id)
    cat_res = await db.execute(cat_stmt)
    cat = cat_res.scalar_one_or_none()

    resp = WaitlistEntryResponse.model_validate(entry)
    resp.category_name = cat.name if cat else "Category"
    return resp


@router.get("/my-entries", response_model=list[WaitlistEntryResponse])
async def list_my_waitlist_entries(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(WaitlistEntry).options(selectinload(WaitlistEntry.category)).where(
        WaitlistEntry.user_id == current_user.id
    ).order_by(WaitlistEntry.joined_at.desc())
    res = await db.execute(stmt)
    entries = res.scalars().all()

    output = []
    for e in entries:
        resp = WaitlistEntryResponse.model_validate(e)
        resp.category_name = e.category.name if e.category else "Category"
        output.append(resp)
    return output


@router.get("/my-offers", response_model=list[WaitlistOfferResponse])
async def list_my_waitlist_offers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(WaitlistOffer).join(WaitlistOffer.waitlist_entry).options(
        selectinload(WaitlistOffer.show_seat).selectinload(ShowSeat.venue_seat)
    ).where(
        WaitlistEntry.user_id == current_user.id,
        WaitlistOffer.status == OfferStatus.ACTIVE,
        WaitlistOffer.expires_at > datetime.now(timezone.utc)
    )
    res = await db.execute(stmt)
    offers = res.scalars().all()

    output = []
    for o in offers:
        resp = WaitlistOfferResponse.model_validate(o)
        resp.seat_label = o.show_seat.venue_seat.seat_label if o.show_seat and o.show_seat.venue_seat else "Offered Seat"
        output.append(resp)
    return output


@router.post("/offers/{offer_id}/accept")
async def accept_waitlist_offer(
    offer_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Accepts an active waitlist offer and creates an active hold for checkout
    """
    stmt = select(WaitlistOffer).options(
        selectinload(WaitlistOffer.waitlist_entry),
        selectinload(WaitlistOffer.show_seat)
    ).where(WaitlistOffer.id == offer_id)
    res = await db.execute(stmt)
    offer = res.scalar_one_or_none()

    if not offer:
        raise HTTPException(status_code=404, detail="Waitlist offer not found")

    if offer.waitlist_entry.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized to accept this offer")

    if offer.status != OfferStatus.ACTIVE or offer.expires_at < datetime.now(timezone.utc):
        offer.status = OfferStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=400, detail="Offer has expired")

    # Mark offer accepted & waitlist fulfilled
    offer.status = OfferStatus.ACCEPTED
    offer.accepted_at = datetime.now(timezone.utc)
    offer.waitlist_entry.status = WaitlistStatus.FULFILLED

    # Create active hold for the offered seat
    hold_token = uuid.uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.DEFAULT_HOLD_TTL_SECONDS)

    hold = Hold(
        user_id=current_user.id,
        show_id=offer.waitlist_entry.show_id,
        hold_token=hold_token,
        status=HoldStatus.ACTIVE,
        expires_at=expires_at
    )
    db.add(hold)
    await db.flush()

    hold_item = HoldItem(hold_id=hold.id, show_seat_id=offer.show_seat_id)
    db.add(hold_item)

    # Set show_seat status to HELD
    offer.show_seat.status = SeatStatus.HELD
    offer.show_seat.version += 1

    await db.commit()

    return {
        "message": "Waitlist offer accepted successfully! Seat reserved for checkout.",
        "hold_id": str(hold.id),
        "hold_token": str(hold_token),
        "expires_at": expires_at.isoformat()
    }
