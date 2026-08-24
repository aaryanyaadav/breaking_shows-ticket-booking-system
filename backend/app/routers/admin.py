from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import User, UserRole, Event, Show, Booking, BookingSeat, Ticket, BookingStatus
from app.schemas import RevenueAnalyticsResponse, UserResponse
from app.auth import require_role

router = APIRouter(prefix="/api/v1/admin", tags=["Admin & Analytics"])

@router.get("/analytics", response_model=RevenueAnalyticsResponse)
async def get_analytics(
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.ORGANISER])),
    db: AsyncSession = Depends(get_db)
):
    # Total events
    ev_count = (await db.execute(select(func.count(Event.id)))).scalar() or 0
    show_count = (await db.execute(select(func.count(Show.id)))).scalar() or 0

    # Confirmed bookings
    bk_stmt = select(
        func.count(Booking.id),
        func.coalesce(func.sum(Booking.total_amount), 0)
    ).where(Booking.status == BookingStatus.CONFIRMED)
    bk_res = await db.execute(bk_stmt)
    total_bks, total_rev = bk_res.one()

    # Total tickets sold
    tkt_count = (await db.execute(select(func.count(Ticket.id)))).scalar() or 0

    return RevenueAnalyticsResponse(
        total_events=ev_count,
        total_shows=show_count,
        total_bookings=total_bks,
        total_tickets_sold=tkt_count,
        total_revenue=float(total_rev)
    )

@router.get("/users", response_model=list[UserResponse])
async def list_users(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).order_by(User.created_at.desc())
    res = await db.execute(stmt)
    return [UserResponse.model_validate(u) for u in res.scalars().all()]

@router.get("/organisers")
async def list_organisers_with_events(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    # Fetch all organisers
    u_stmt = select(User).where(User.role == UserRole.ORGANISER).order_by(User.name.asc())
    u_res = await db.execute(u_stmt)
    organisers = u_res.scalars().all()

    # Fetch all events
    e_stmt = select(Event)
    e_res = await db.execute(e_stmt)
    all_events = e_res.scalars().all()

    result = []
    for org in organisers:
        org_events = [
            {
                "id": str(e.id),
                "title": e.title,
                "event_type": e.event_type.value,
                "duration_minutes": e.duration_minutes,
                "status": e.status.value
            }
            for e in all_events if e.organiser_id == org.id
        ]
        result.append({
            "id": str(org.id),
            "name": org.name,
            "email": org.email,
            "role": org.role.value,
            "created_at": org.created_at.isoformat(),
            "events_count": len(org_events),
            "events": org_events
        })
    return result
