from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Optional
from app.database import get_db
from app.models import User, UserRole, Show, Event, Venue, VenueSeat, SeatCategory, ShowPrice, ShowSeat, SeatStatus, ShowStatus
from app.schemas import ShowCreateRequest, ShowResponse, ShowSeatMapItem
from app.auth import get_current_user, get_optional_current_user, require_role

router = APIRouter(prefix="/api/v1/shows", tags=["Showtimes & Seat Inventory"])

@router.get("", response_model=list[ShowResponse])
async def list_shows(event_id: Optional[UUID] = None, db: AsyncSession = Depends(get_db)):
    stmt = select(Show).options(
        selectinload(Show.event),
        selectinload(Show.venue)
    )
    if event_id:
        stmt = stmt.where(Show.event_id == event_id)
    stmt = stmt.order_by(Show.start_time.asc())
    res = await db.execute(stmt)
    shows = res.scalars().all()
    
    output = []
    for s in shows:
        resp = ShowResponse.model_validate(s)
        resp.event_title = s.event.title if s.event else "Event"
        resp.venue_name = s.venue.name if s.venue else "Venue"
        output.append(resp)
    return output

@router.post("", response_model=ShowResponse, status_code=status.HTTP_201_CREATED)
async def create_show(
    req: ShowCreateRequest,
    current_user: User = Depends(require_role([UserRole.ORGANISER])),
    db: AsyncSession = Depends(get_db)
):
    # Verify event and venue exist
    event_res = await db.execute(select(Event).where(Event.id == req.event_id))
    event = event_res.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    venue_res = await db.execute(select(Venue).where(Venue.id == req.venue_id))
    venue = venue_res.scalar_one_or_none()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")

    show = Show(
        event_id=req.event_id,
        venue_id=req.venue_id,
        start_time=req.start_time,
        end_time=req.end_time,
        status=ShowStatus.ON_SALE
    )
    db.add(show)
    await db.flush()

    # Save category prices
    for cat_id_str, price in req.prices.items():
        cat_id = UUID(cat_id_str)
        show_price = ShowPrice(
            show_id=show.id,
            category_id=cat_id,
            price=price
        )
        db.add(show_price)

    # Instantiate show_seats for every venue seat
    seats_stmt = select(VenueSeat).where(
        VenueSeat.venue_id == req.venue_id,
        VenueSeat.is_active == True
    )
    venue_seats_res = await db.execute(seats_stmt)
    venue_seats = venue_seats_res.scalars().all()

    for vs in venue_seats:
        # Determine price based on seat's category_id
        cat_str = str(vs.category_id)
        price = req.prices.get(cat_str, 200.0)
        show_seat = ShowSeat(
            show_id=show.id,
            venue_seat_id=vs.id,
            category_id=vs.category_id,
            price=price,
            status=SeatStatus.AVAILABLE,
            version=0
        )
        db.add(show_seat)

    await db.commit()
    await db.refresh(show)

    resp = ShowResponse.model_validate(show)
    resp.event_title = event.title
    resp.venue_name = venue.name
    return resp

@router.get("/{show_id}", response_model=ShowResponse)
async def get_show(show_id: UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Show).options(
        selectinload(Show.event),
        selectinload(Show.venue)
    ).where(Show.id == show_id)
    res = await db.execute(stmt)
    show = res.scalar_one_or_none()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    resp = ShowResponse.model_validate(show)
    resp.event_title = show.event.title
    resp.venue_name = show.venue.name
    return resp

@router.get("/{show_id}/seats", response_model=list[ShowSeatMapItem])
async def get_show_seats(
    show_id: UUID, 
    current_user: Optional[User] = Depends(get_optional_current_user), 
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ShowSeat).options(
        selectinload(ShowSeat.venue_seat),
        selectinload(ShowSeat.category)
    ).where(ShowSeat.show_id == show_id)
    
    res = await db.execute(stmt)
    seats = res.scalars().all()

    seat_items = []
    for s in seats:
        vs = s.venue_seat
        item = ShowSeatMapItem(
            id=s.id,
            venue_seat_id=s.venue_seat_id,
            category_id=s.category_id,
            category_name=s.category.name if s.category else "Standard",
            row_label=vs.row_label,
            seat_number=vs.seat_number,
            seat_label=vs.seat_label,
            x_position=vs.x_position,
            y_position=vs.y_position,
            price=float(s.price),
            status=s.status,
            held_by_current_user=False # Calculated on frontend or via active hold token
        )
        seat_items.append(item)

    return seat_items
