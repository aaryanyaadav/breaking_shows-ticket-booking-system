import asyncio
import logging
from datetime import datetime, timedelta
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import engine, Base, AsyncSessionLocal
from app.redis_client import init_redis
from app.websockets import ws_manager
from app.worker import start_background_worker
from app.auth import get_password_hash
from app.models import User, UserRole, Venue, VenueSection, SeatCategory, VenueSeat, Event, EventType, EventStatus, Show, ShowStatus, ShowPrice, ShowSeat, SeatStatus

# Import Routers
from app.routers import auth, venues, events, shows, holds, bookings, waitlist, waiting_room, tickets, admin

logger = logging.getLogger("main")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="High-concurrency ticket allocation system with Redis atomic seat holds, virtual waiting room, and category-aware waitlist auto-reallocation."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router)
app.include_router(venues.router)
app.include_router(events.router)
app.include_router(shows.router)
app.include_router(holds.router)
app.include_router(bookings.router)
app.include_router(waitlist.router)
app.include_router(waiting_room.router)
app.include_router(tickets.router)
app.include_router(admin.router)

@app.websocket("/ws/shows/{show_id}")
async def websocket_show_seats(websocket: WebSocket, show_id: str):
    await ws_manager.connect(websocket, show_id)
    try:
        while True:
            # Keep connection open for push events
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, show_id)
    except Exception:
        ws_manager.disconnect(websocket, show_id)


async def seed_initial_data():
    """Populates initial seed data if DB is empty"""
    async with AsyncSessionLocal() as db:
        user_check = await db.execute(select(User))
        if user_check.scalars().first():
            logger.info("Database already seeded.")
            return

        logger.info("Seeding initial mock users, venues, events, and shows...")
        
        # 1. Users
        admin_user = User(
            name="Admin User",
            email="admin@ticketmaster.com",
            password_hash=get_password_hash("admin123"),
            role=UserRole.ADMIN
        )
        org_user = User(
            name="BookMyShow Organiser",
            email="org@bookmyshow.com",
            password_hash=get_password_hash("org123"),
            role=UserRole.ORGANISER
        )
        cust_user = User(
            name="Aryan Sharma",
            email="aryan@gmail.com",
            password_hash=get_password_hash("cust123"),
            role=UserRole.CUSTOMER
        )
        cust_user2 = User(
            name="Rahul Verma",
            email="rahul@gmail.com",
            password_hash=get_password_hash("cust123"),
            role=UserRole.CUSTOMER
        )
        db.add_all([admin_user, org_user, cust_user, cust_user2])
        await db.flush()

        # 2. Venue: Grand IMAX Theater
        venue = Venue(
            name="Grand IMAX Theater Screen 1",
            address="Lower Parel, Phoenix Mall",
            city="Mumbai",
            state="Maharashtra",
            country="India"
        )
        db.add(venue)
        await db.flush()

        sec = VenueSection(venue_id=venue.id, name="Auditorium 1", section_type="SEATED")
        db.add(sec)
        await db.flush()

        cat_vip = SeatCategory(venue_id=venue.id, name="VIP", description="Recliner Front Rows")
        cat_prem = SeatCategory(venue_id=venue.id, name="PREMIUM", description="Prime Viewing Center Rows")
        cat_std = SeatCategory(venue_id=venue.id, name="STANDARD", description="General Audience Seats")
        db.add_all([cat_vip, cat_prem, cat_std])
        await db.flush()

        # Generate 4 rows x 8 seats grid
        row_chars = ['A', 'B', 'C', 'D']
        venue_seats = []
        for r_idx, r_chr in enumerate(row_chars):
            if r_idx == 0:
                cat = cat_vip
            elif r_idx == 1:
                cat = cat_prem
            else:
                cat = cat_std

            for s_num in range(1, 9):
                v_seat = VenueSeat(
                    venue_id=venue.id,
                    section_id=sec.id,
                    category_id=cat.id,
                    row_label=r_chr,
                    seat_number=s_num,
                    seat_label=f"{r_chr}{s_num}",
                    x_position=(s_num - 1) * 60 + 50,
                    y_position=r_idx * 55 + 70
                )
                db.add(v_seat)
                venue_seats.append(v_seat)
        await db.flush()

        # 3. Events
        ev1 = Event(
            organiser_id=org_user.id,
            title="Coldplay - Music of the Spheres Tour",
            description="Live stadium concert with laser shows, fireworks, and hit songs Yellow, Fix You, Viva La Vida.",
            event_type=EventType.CONCERT,
            poster_url="https://images.unsplash.com/photo-1470225620780-dba8ba36b745?auto=format&fit=crop&w=800&q=80",
            duration_minutes=180,
            status=EventStatus.PUBLISHED
        )
        ev2 = Event(
            organiser_id=org_user.id,
            title="Avengers: Secret Wars (IMAX 3D)",
            description="The multiverse collides in the epic finale of the MCU phase 6.",
            event_type=EventType.MOVIE,
            poster_url="https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=800&q=80",
            duration_minutes=165,
            status=EventStatus.PUBLISHED
        )
        db.add_all([ev1, ev2])
        await db.flush()

        # 4. Shows
        show1 = Show(
            event_id=ev1.id,
            venue_id=venue.id,
            section_id=sec.id,
            start_time=datetime.utcnow() + timedelta(days=1, hours=4),
            status=ShowStatus.ON_SALE
        )
        show2 = Show(
            event_id=ev2.id,
            venue_id=venue.id,
            section_id=sec.id,
            start_time=datetime.utcnow() + timedelta(hours=6),
            status=ShowStatus.ON_SALE
        )
        db.add_all([show1, show2])
        await db.flush()

        # Pricing per category
        prices = {
            cat_vip.id: 1500.0,
            cat_prem.id: 850.0,
            cat_std.id: 450.0
        }
        for sh in [show1, show2]:
            for cat_id, price in prices.items():
                sp = ShowPrice(show_id=sh.id, category_id=cat_id, price=price)
                db.add(sp)

            for vs in venue_seats:
                ss = ShowSeat(
                    show_id=sh.id,
                    venue_seat_id=vs.id,
                    category_id=vs.category_id,
                    price=prices[vs.category_id],
                    status=SeatStatus.AVAILABLE,
                    version=0
                )
                db.add(ss)

        await db.commit()
        logger.info("Database seeding completed successfully!")


@app.on_event("startup")
async def on_startup():
    # 1. Initialize DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. Seed initial data if empty
    await seed_initial_data()

    # 3. Initialize Redis client
    try:
        await init_redis()
    except Exception as e:
        logger.warning(f"Redis initialization failed (Make sure Redis is running): {e}")

    # 4. Start background worker task
    asyncio.create_task(start_background_worker())


@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
        "api_v1_url": "/api/v1/events"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
