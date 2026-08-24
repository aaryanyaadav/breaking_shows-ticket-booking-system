import io
import uuid
import base64
import qrcode
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import (
    User, Hold, HoldItem, Booking, BookingSeat, Payment, Ticket, ShowSeat, 
    WaitlistEntry, WaitlistOffer, Notification, OutboxEvent,
    HoldStatus, BookingStatus, PaymentStatus, TicketStatus, SeatStatus, WaitlistStatus, OfferStatus
)
from app.schemas import BookingCreateRequest, BookingResponse, MockPaymentRequest
from app.auth import get_current_user
from app.websockets import ws_manager
from app.config import settings
from app.services.email import send_email_notification

router = APIRouter(prefix="/api/v1/bookings", tags=["Bookings & Payments"])

def generate_qr_code_base64(data: str) -> str:
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        print(f"⚠️ QR generation fallback notice: {e}")
        safe_payload = base64.b64encode(data.encode()).decode()
        return f"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><rect width='160' height='160' fill='%23121826'/><text x='10' y='80' fill='%2393c5fd' font-size='10'>QR Ticket: {data[:16]}</text></svg>"

@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    req: BookingCreateRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Idempotency check
    if idempotency_key:
        stmt = select(Booking).where(Booking.idempotency_key == idempotency_key)
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return BookingResponse.model_validate(existing)

    # 2. Validate Hold
    stmt = select(Hold).options(
        selectinload(Hold.hold_items).selectinload(HoldItem.show_seat)
    ).where(
        Hold.id == req.hold_id,
        Hold.hold_token == req.hold_token,
        Hold.user_id == current_user.id
    )
    res = await db.execute(stmt)
    hold = res.scalar_one_or_none()

    if not hold:
        raise HTTPException(status_code=404, detail="Hold record not found or hold_token mismatch")

    if hold.status != HoldStatus.ACTIVE:
        raise HTTPException(status_code=400, detail=f"Hold is no longer active (status: {hold.status.value})")

    if hold.expires_at < datetime.now(timezone.utc):
        hold.status = HoldStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=400, detail="Hold has expired. Please select seats again.")

    # 3. Calculate Prices
    subtotal = sum(float(item.show_seat.price or 0.0) for item in hold.hold_items if item.show_seat)
    tax = round(subtotal * 0.18, 2) # 18% tax
    total_amount = round(subtotal + tax, 2)
    booking_ref = f"BK-{uuid.uuid4().hex[:8].upper()}"

    booking = Booking(
        booking_reference=booking_ref,
        user_id=current_user.id,
        show_id=req.show_id,
        hold_id=hold.id,
        status=BookingStatus.PENDING,
        subtotal=subtotal,
        tax=tax,
        discount=0,
        total_amount=total_amount,
        idempotency_key=idempotency_key
    )
    db.add(booking)
    await db.flush()

    for item in hold.hold_items:
        if item.show_seat:
            b_seat = BookingSeat(
                booking_id=booking.id,
                show_seat_id=item.show_seat_id,
                price=item.show_seat.price or 0.0
            )
            db.add(b_seat)

    payment = Payment(
        booking_id=booking.id,
        provider="MOCK_GATEWAY",
        amount=total_amount,
        status=PaymentStatus.PENDING
    )
    db.add(payment)

    await db.commit()
    await db.refresh(booking)
    return BookingResponse.model_validate(booking)


@router.post("/mock-pay")
async def mock_pay_booking(
    req: MockPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Simulates payment execution and confirms booking
    """
    stmt = select(Booking).options(
        selectinload(Booking.seats).selectinload(BookingSeat.show_seat).selectinload(ShowSeat.venue_seat),
        selectinload(Booking.hold)
    ).where(Booking.id == req.booking_id, Booking.user_id == current_user.id)
    res = await db.execute(stmt)
    booking = res.scalar_one_or_none()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status == BookingStatus.CONFIRMED:
        return {"message": "Booking is already confirmed", "booking_id": str(booking.id)}

    # 1. Update Booking & Payment Status
    booking.status = BookingStatus.CONFIRMED
    booking.confirmed_at = datetime.now(timezone.utc)

    payment_stmt = select(Payment).where(Payment.booking_id == booking.id)
    pay_res = await db.execute(payment_stmt)
    payment = pay_res.scalar_one_or_none()
    if payment:
        payment.status = PaymentStatus.SUCCESS
        payment.provider_payment_id = f"PAY-{uuid.uuid4().hex[:10].upper()}"

    if booking.hold:
        booking.hold.status = HoldStatus.CONVERTED

    # 2. Update Show Seats to BOOKED
    seat_ids = [bs.show_seat_id for bs in booking.seats if bs.show_seat]
    seat_ids_str = [str(sid) for sid in seat_ids]

    if seat_ids:
        update_seat_stmt = (
            update(ShowSeat)
            .where(ShowSeat.id.in_(seat_ids))
            .values(status=SeatStatus.BOOKED, version=ShowSeat.version + 1)
        )
        await db.execute(update_seat_stmt)

    # 3. Issue QR Ticket
    ticket_ref = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    qr_payload = f"TICKET_REF:{ticket_ref}|BOOKING:{booking.booking_reference}|USER:{current_user.email}"
    qr_code_b64 = generate_qr_code_base64(qr_payload)

    ticket = Ticket(
        booking_id=booking.id,
        ticket_reference=ticket_ref,
        qr_payload=qr_payload,
        qr_code_url=qr_code_b64,
        status=TicketStatus.ACTIVE
    )
    db.add(ticket)

    # 4. Outbox & Notification & Free Email Delivery
    notif = Notification(
        user_id=current_user.id,
        type="BOOKING_CONFIRMED",
        channel="EMAIL",
        reference_type="BOOKING",
        reference_id=booking.id,
        status="SENT",
        sent_at=datetime.now(timezone.utc)
    )
    db.add(notif)

    outbox = OutboxEvent(
        aggregate_type="BOOKING",
        aggregate_id=booking.id,
        event_type="BookingConfirmed",
        payload={
            "booking_reference": booking.booking_reference,
            "user_email": current_user.email,
            "total_amount": float(booking.total_amount),
            "ticket_reference": ticket_ref
        },
        status="PROCESSED"
    )
    db.add(outbox)

    await db.commit()

    # Dispatch Free Email with QR Code Ticket
    seat_labels = [
        bs.show_seat.venue_seat.seat_label 
        if (bs.show_seat and bs.show_seat.venue_seat) 
        else "Seat" 
        for bs in booking.seats if bs.show_seat
    ]
    email_html = f"""
    <h2>🎟️ Booking Confirmed!</h2>
    <p>Dear {current_user.name},</p>
    <p>Your booking <b>{booking.booking_reference}</b> is confirmed.</p>
    <ul>
      <li><b>Booking Reference:</b> {booking.booking_reference}</li>
      <li><b>Ticket Reference:</b> {ticket_ref}</li>
      <li><b>Seat Numbers:</b> {", ".join(seat_labels)}</li>
      <li><b>Total Amount Paid:</b> ₹{float(booking.total_amount):.2f}</li>
    </ul>
    <p>Scan the attached QR code ticket at the venue for entrance.</p>
    """
    try:
        await send_email_notification(
            to_email=current_user.email,
            subject=f"🎟️ Ticket Confirmed: {booking.booking_reference}",
            body_html=email_html,
            qr_code_b64=qr_code_b64
        )
    except Exception as email_err:
        print(f"⚠️ Non-blocking email dispatch notice: {email_err}")

    # 5. Broadcast WebSocket seat map update
    await ws_manager.broadcast_seat_update(
        show_id=str(booking.show_id),
        payload={
            "event": "SEAT_STATUS_CHANGED",
            "show_id": str(booking.show_id),
            "seat_ids": seat_ids_str,
            "status": "BOOKED",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

    return {
        "status": "SUCCESS",
        "booking_reference": booking.booking_reference,
        "ticket_reference": ticket_ref,
        "qr_code_url": qr_code_b64
    }


@router.post("/{booking_id}/cancel")
async def cancel_booking(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancels a confirmed booking and automatically offers freed seats to waitlisted customers
    """
    stmt = select(Booking).options(
        selectinload(Booking.seats).selectinload(BookingSeat.show_seat)
    ).where(Booking.id == booking_id, Booking.user_id == current_user.id)
    res = await db.execute(stmt)
    booking = res.scalar_one_or_none()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status == BookingStatus.CANCELLED:
        return {"message": "Booking is already cancelled"}

    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = datetime.now(timezone.utc)

    # Update payment to REFUNDED
    pay_stmt = select(Payment).where(Payment.booking_id == booking.id)
    pay_res = await db.execute(pay_stmt)
    payment = pay_res.scalar_one_or_none()
    if payment:
        payment.status = PaymentStatus.REFUNDED

    # Update tickets to CANCELLED
    tkt_stmt = select(Ticket).where(Ticket.booking_id == booking.id)
    tkt_res = await db.execute(tkt_stmt)
    tickets = tkt_res.scalars().all()
    for tkt in tickets:
        tkt.status = TicketStatus.CANCELLED

    freed_seat_ids = []
    # Process freed seats with category waitlist auto-assignment!
    for bs in booking.seats:
        show_seat = bs.show_seat
        if not show_seat:
            continue

        category_id = show_seat.category_id
        show_id = booking.show_id

        # Check if there is a customer waiting in waitlist for this specific category
        wl_stmt = select(WaitlistEntry).options(selectinload(WaitlistEntry.user)).where(
            WaitlistEntry.show_id == show_id,
            WaitlistEntry.category_id == category_id,
            WaitlistEntry.status == WaitlistStatus.WAITING
        ).order_by(WaitlistEntry.position.asc())
        wl_res = await db.execute(wl_stmt)
        next_waitlisted = wl_res.scalars().first()

        if next_waitlisted:
            show_seat.status = SeatStatus.OFFERED
            show_seat.version += 1
            next_waitlisted.status = WaitlistStatus.OFFERED

            expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.OFFER_TTL_SECONDS)
            offer = WaitlistOffer(
                waitlist_entry_id=next_waitlisted.id,
                show_seat_id=show_seat.id,
                offer_token=uuid.uuid4(),
                status=OfferStatus.ACTIVE,
                expires_at=expires_at
            )
            db.add(offer)

            notif = Notification(
                user_id=next_waitlisted.user_id,
                type="WAITLIST_OFFER",
                channel="EMAIL",
                reference_type="WAITLIST_OFFER",
                reference_id=offer.id,
                status="SENT",
                sent_at=datetime.now(timezone.utc)
            )
            db.add(notif)

            # Send Email notification with time-limited link
            claim_url = f"http://localhost:3000?offer_id={offer.id}"
            w_email = next_waitlisted.user.email if next_waitlisted.user else "customer@gmail.com"
            w_name = next_waitlisted.user.name if next_waitlisted.user else "Customer"
            email_html = f"""
            <h2>🎉 Seat Available from Waitlist!</h2>
            <p>Dear {w_name},</p>
            <p>A seat has become available for your requested show!</p>
            <p>You have <b>15 minutes</b> to claim your seat reservation:</p>
            <p><a href="{claim_url}" style="background:#6366f1;color:#ffffff;padding:12px 20px;border-radius:8px;text-decoration:none;font-weight:bold;display:inline-block;">Claim Offered Seat Now</a></p>
            <p>Expiration Time: {expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            """
            await send_email_notification(
                to_email=w_email,
                subject="🎉 Seat Available: Claim Your Waitlist Ticket!",
                body_html=email_html
            )
        else:
            show_seat.status = SeatStatus.AVAILABLE
            show_seat.version += 1

        freed_seat_ids.append(str(show_seat.id))

    await db.commit()

    # Broadcast seat map status update
    await ws_manager.broadcast_seat_update(
        show_id=str(booking.show_id),
        payload={
            "event": "SEAT_STATUS_CHANGED",
            "show_id": str(booking.show_id),
            "seat_ids": freed_seat_ids,
            "status": "AVAILABLE_OR_OFFERED",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

    return {
        "message": "Booking cancelled successfully and refund processed",
        "booking_reference": booking.booking_reference
    }

@router.get("", response_model=list[BookingResponse])
async def list_user_bookings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Booking).where(Booking.user_id == current_user.id).order_by(Booking.created_at.desc())
    res = await db.execute(stmt)
    bookings = res.scalars().all()
    return [BookingResponse.model_validate(b) for b in bookings]
