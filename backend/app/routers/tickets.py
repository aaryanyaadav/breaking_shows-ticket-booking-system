import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import User, Ticket, Booking, BookingSeat, ShowSeat, VenueSeat
from app.schemas import TicketResponse
from app.auth import get_current_user

router = APIRouter(prefix="/api/v1/tickets", tags=["Tickets & QR"])

@router.get("", response_model=list[TicketResponse])
async def list_user_tickets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Ticket).join(Ticket.booking).options(
        selectinload(Ticket.booking).selectinload(Booking.seats).selectinload(BookingSeat.show_seat).selectinload(ShowSeat.venue_seat)
    ).where(Booking.user_id == current_user.id).order_by(Ticket.issued_at.desc())

    res = await db.execute(stmt)
    tickets = res.scalars().all()

    output = []
    for tkt in tickets:
        seat_labels = []
        if tkt.booking and tkt.booking.seats:
            seat_labels = [bs.show_seat.venue_seat.seat_label for bs in tkt.booking.seats if bs.show_seat and bs.show_seat.venue_seat]

        resp = TicketResponse(
            id=tkt.id,
            booking_id=tkt.booking_id,
            ticket_reference=tkt.ticket_reference,
            qr_payload=tkt.qr_payload,
            qr_code_url=tkt.qr_code_url or "",
            status=tkt.status.value,
            issued_at=tkt.issued_at,
            seats=seat_labels
        )
        output.append(resp)

    return output

@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Ticket).options(
        selectinload(Ticket.booking).selectinload(Booking.seats).selectinload(BookingSeat.show_seat).selectinload(ShowSeat.venue_seat)
    ).where(Ticket.id == ticket_id)
    res = await db.execute(stmt)
    tkt = res.scalar_one_or_none()

    if not tkt or tkt.booking.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Ticket not found")

    seat_labels = [bs.show_seat.venue_seat.seat_label for bs in tkt.booking.seats if bs.show_seat and bs.show_seat.venue_seat]

    return TicketResponse(
        id=tkt.id,
        booking_id=tkt.booking_id,
        ticket_reference=tkt.ticket_reference,
        qr_payload=tkt.qr_payload,
        qr_code_url=tkt.qr_code_url or "",
        status=tkt.status.value,
        issued_at=tkt.issued_at,
        seats=seat_labels
    )
