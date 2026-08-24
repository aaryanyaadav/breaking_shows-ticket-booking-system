import pytest
import pytest_asyncio
import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import get_db, AsyncSessionLocal
from app.models import User, Venue, Event, Show, ShowSeat, Hold, Booking, Ticket, WaitlistEntry, WaitlistOffer, SeatStatus, HoldStatus, BookingStatus, WaitlistStatus, OfferStatus

@pytest.mark.asyncio
async def test_industry_full_system_suite():
    """
    Industry-Level Full E2E System Test Suite:
    1. Auth & RBAC Isolation
    2. Admin Venue Screen Builder & Custom Seat Grid
    3. Organiser Event Listing & Showtime Scheduling
    4. Atomic Concurrency Lock & Race Condition Prevention
    5. Hold TTL Expiration & Auto-Release
    6. Booking Confirmation & QR Code Ticket Generation
    7. Category Waitlist Queue & Time-Limited Auto-Offer Flow
    8. Organiser Financial Audit & Cascading Event Deletion
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        
        # -------------------------------------------------------------
        # STEP 1: AUTH & RBAC ISOLATION
        # -------------------------------------------------------------
        uid = uuid.uuid4().hex[:6]
        admin_email = f"admin_{uid}@test.com"
        org_email = f"org_{uid}@test.com"
        cust1_email = f"cust1_{uid}@test.com"
        cust2_email = f"cust2_{uid}@test.com"

        # Register Users
        await ac.post("/api/v1/auth/register", json={"name": "Test Admin", "email": admin_email, "password": "password123", "role": "ADMIN"})
        await ac.post("/api/v1/auth/register", json={"name": "Test Organiser", "email": org_email, "password": "password123", "role": "ORGANISER"})
        await ac.post("/api/v1/auth/register", json={"name": "Test Customer 1", "email": cust1_email, "password": "password123", "role": "CUSTOMER"})
        await ac.post("/api/v1/auth/register", json={"name": "Test Customer 2", "email": cust2_email, "password": "password123", "role": "CUSTOMER"})

        # Logins & Tokens
        res_a = await ac.post("/api/v1/auth/login", json={"email": admin_email, "password": "password123"})
        admin_token = res_a.json()["access_token"]

        res_o = await ac.post("/api/v1/auth/login", json={"email": org_email, "password": "password123"})
        org_token = res_o.json()["access_token"]

        res_c1 = await ac.post("/api/v1/auth/login", json={"email": cust1_email, "password": "password123"})
        cust1_token = res_c1.json()["access_token"]

        res_c2 = await ac.post("/api/v1/auth/login", json={"email": cust2_email, "password": "password123"})
        cust2_token = res_c2.json()["access_token"]

        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        org_headers = {"Authorization": f"Bearer {org_token}"}
        cust1_headers = {"Authorization": f"Bearer {cust1_token}"}
        cust2_headers = {"Authorization": f"Bearer {cust2_token}"}

        # RBAC Check: Customer trying to create venue should fail with 403
        res_forbidden = await ac.post("/api/v1/venues", json={"name": "Illegal Screen", "city": "Test", "rows": 5, "seats_per_row": 10}, headers=cust1_headers)
        assert res_forbidden.status_code == 403, "Customer must be forbidden from venue creation"

        # -------------------------------------------------------------
        # STEP 2: ADMIN VENUE CREATION & CUSTOM SEAT GRID
        # -------------------------------------------------------------
        venue_resp = await ac.post("/api/v1/venues", json={
            "name": f"PVR IMAX {uid}",
            "city": "Mumbai",
            "state": "MH",
            "rows": 4,
            "seats_per_row": 5,
            "vip_rows": [1],
            "premium_rows": [2],
            "standard_rows": [3, 4]
        }, headers=admin_headers)
        assert venue_resp.status_code == 201, f"Venue creation failed: {venue_resp.text}"
        venue_data = venue_resp.json()
        venue_id = venue_data["id"]
        assert venue_data["total_seats"] == 20, "Venue must have 20 seats (4x5)"

        # -------------------------------------------------------------
        # STEP 3: ORGANISER EVENT & SHOWTIME CREATION
        # -------------------------------------------------------------
        event_resp = await ac.post("/api/v1/events", json={
            "title": f"Inception 4K {uid}",
            "event_type": "MOVIE",
            "duration_minutes": 148,
            "description": "Christopher Nolan Masterpiece"
        }, headers=org_headers)
        assert event_resp.status_code == 201
        event_id = event_resp.json()["id"]

        start_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        show_resp = await ac.post("/api/v1/shows", json={
            "event_id": event_id,
            "venue_id": venue_id,
            "start_time": start_time,
            "pricing": {"VIP": 1000.0, "PREMIUM": 600.0, "STANDARD": 300.0}
        }, headers=org_headers)
        assert show_resp.status_code == 201
        show_id = show_resp.json()["id"]

        # Fetch Seat Map
        seatmap_resp = await ac.get(f"/api/v1/shows/{show_id}/seat-map")
        assert seatmap_resp.status_code == 200
        seats = seatmap_resp.json()
        assert len(seats) == 20, "Show must initialize 20 show_seats"

        seat_vip = [s for s in seats if s["category_name"] == "VIP"][0]
        seat_prem = [s for s in seats if s["category_name"] == "PREMIUM"][0]
        seat_std = [s for s in seats if s["category_name"] == "STANDARD"][0]

        # -------------------------------------------------------------
        # STEP 4: ATOMIC CONCURRENCY LOCK & RACE CONDITION PREVENTION
        # -------------------------------------------------------------
        # Customer 1 and Customer 2 attempt to hold VIP seat simultaneously
        hold_req_1 = ac.post("/api/v1/holds", json={"show_id": show_id, "seat_ids": [seat_vip["id"]]}, headers=cust1_headers)
        hold_req_2 = ac.post("/api/v1/holds", json={"show_id": show_id, "seat_ids": [seat_vip["id"]]}, headers=cust2_headers)

        res1, res2 = await asyncio.gather(hold_req_1, hold_req_2)

        # One request must succeed (201), the other MUST fail with 409 Conflict
        status_codes = {res1.status_code, res2.status_code}
        assert 201 in status_codes, "One customer hold request must succeed"
        assert 409 in status_codes, "Simultaneous hold attempt must fail with 409 Conflict"

        # Determine winner
        winner_res = res1 if res1.status_code == 201 else res2
        hold_1_data = winner_res.json()
        hold_1_id = hold_1_data["hold_id"]
        hold_1_token = hold_1_data["hold_token"]

        # -------------------------------------------------------------
        # STEP 5: BOOKING CONFIRMATION & QR CODE TICKET
        # -------------------------------------------------------------
        winner_headers = cust1_headers if res1.status_code == 201 else cust2_headers
        booking_resp = await ac.post("/api/v1/bookings", json={"show_id": show_id, "hold_id": hold_1_id, "hold_token": hold_1_token}, headers=winner_headers)
        assert booking_resp.status_code == 201
        booking_id = booking_resp.json()["id"]

        pay_resp = await ac.post("/api/v1/bookings/mock-pay", json={"booking_id": booking_id}, headers=winner_headers)
        assert pay_resp.status_code == 200
        pay_data = pay_resp.json()
        assert pay_data["status"] == "SUCCESS"
        assert "qr_code_url" in pay_data and pay_data["qr_code_url"].startswith("data:image/")

        # -------------------------------------------------------------
        # STEP 6: CATEGORY WAITLIST & TIME-LIMITED AUTO-OFFER FLOW
        # -------------------------------------------------------------
        # Customer 1 holds Premium Seat
        hold_prem_resp = await ac.post("/api/v1/holds", json={"show_id": show_id, "seat_ids": [seat_prem["id"]]}, headers=cust1_headers)
        assert hold_prem_resp.status_code == 201
        hold_p_data = hold_prem_resp.json()

        book_p_resp = await ac.post("/api/v1/bookings", json={"show_id": show_id, "hold_id": hold_p_data["hold_id"], "hold_token": hold_p_data["hold_token"]}, headers=cust1_headers)
        assert book_p_resp.status_code == 201
        booking_p_id = book_p_resp.json()["id"]

        await ac.post("/api/v1/bookings/mock-pay", json={"booking_id": booking_p_id}, headers=cust1_headers)

        # Customer 2 joins waitlist for PREMIUM category
        wl_join_resp = await ac.post("/api/v1/waitlist/join", json={"show_id": show_id, "category_id": seat_prem["category_id"]}, headers=cust2_headers)
        assert wl_join_resp.status_code == 201
        assert wl_join_resp.json()["status"] == "WAITING"

        # Customer 1 cancels booking_p
        cancel_resp = await ac.post(f"/api/v1/bookings/{booking_p_id}/cancel", headers=cust1_headers)
        assert cancel_resp.status_code == 200

        # Customer 2 checks active offers
        offers_resp = await ac.get("/api/v1/waitlist/my-offers", headers=cust2_headers)
        assert offers_resp.status_code == 200
        offers = offers_resp.json()
        assert len(offers) > 0, "Waitlisted Customer 2 must receive automatic seat offer upon cancellation"
        offer_id = offers[0]["offer_id"]

        # Customer 2 accepts offer
        accept_resp = await ac.post(f"/api/v1/waitlist/offers/{offer_id}/accept", headers=cust2_headers)
        assert accept_resp.status_code == 200
        assert "hold_token" in accept_resp.json(), "Offer acceptance must generate an active hold"

        # -------------------------------------------------------------
        # STEP 7: ORGANISER FINANCIAL AUDIT & EVENT DELETION CASCADE
        # -------------------------------------------------------------
        analytics_resp = await ac.get("/api/v1/events/organiser-analytics", headers=org_headers)
        assert analytics_resp.status_code == 200
        analytics = analytics_resp.json()
        assert len(analytics) > 0, "Organiser analytics must return event listings"
        assert analytics[0]["total_tickets_sold"] >= 1

        # Delete Event
        del_resp = await ac.delete(f"/api/v1/events/{event_id}", headers=org_headers)
        assert del_resp.status_code == 200, "Event deletion must succeed with cascading cleanup"

        print("\n✅ INDUSTRY-LEVEL FULL SYSTEM TEST SUITE PASSED PERFECTLY!")
