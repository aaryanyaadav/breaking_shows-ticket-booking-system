from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from app.database import get_db
from app.models import User, UserRole, Venue, VenueSection, SeatCategory, VenueSeat
from app.schemas import VenueResponse, CreateVenueRequest
from app.auth import require_role, get_current_user

router = APIRouter(prefix="/api/v1/venues", tags=["Venues"])

@router.get("", response_model=list[VenueResponse])
async def list_venues(db: AsyncSession = Depends(get_db)):
    stmt = select(Venue).options(
        selectinload(Venue.sections),
        selectinload(Venue.categories)
    )
    res = await db.execute(stmt)
    venues = res.scalars().all()
    return [VenueResponse.model_validate(v) for v in venues]

@router.post("", response_model=VenueResponse, status_code=status.HTTP_201_CREATED)
async def create_venue(
    req: CreateVenueRequest,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    venue = Venue(
        name=req.name,
        address=req.address,
        city=req.city,
        state=req.state
    )
    db.add(venue)
    await db.flush()

    # Create default sections & categories
    sec_main = VenueSection(venue_id=venue.id, name="Main Screen Hall", section_type="SEATED")
    db.add(sec_main)
    await db.flush()

    cat_vip = SeatCategory(venue_id=venue.id, name="VIP", description="Recliner Front Rows")
    cat_prem = SeatCategory(venue_id=venue.id, name="PREMIUM", description="Front & Middle Central Rows")
    cat_std = SeatCategory(venue_id=venue.id, name="STANDARD", description="General Auditorium Seating")
    db.add_all([cat_vip, cat_prem, cat_std])
    await db.flush()

    vip_count = getattr(req, 'vip_rows', 1)
    prem_count = getattr(req, 'premium_rows', 1)

    # Generate seats grid layout (Rows A, B, C... x Seats 1..N)
    row_labels = [chr(65 + i) for i in range(req.rows)] # 'A', 'B', 'C', ...
    for r_idx, row_chr in enumerate(row_labels):
        if r_idx < vip_count:
            cat = cat_vip
        elif r_idx < (vip_count + prem_count):
            cat = cat_prem
        else:
            cat = cat_std

        for s_idx in range(1, req.seats_per_row + 1):
            seat = VenueSeat(
                venue_id=venue.id,
                section_id=sec_main.id,
                category_id=cat.id,
                row_label=row_chr,
                seat_number=s_idx,
                seat_label=f"{row_chr}{s_idx}",
                x_position=(s_idx - 1) * 55 + 50,
                y_position=r_idx * 55 + 70
            )
            db.add(seat)

    await db.commit()
    
    # Reload venue with relationships
    stmt = select(Venue).options(
        selectinload(Venue.sections),
        selectinload(Venue.categories)
    ).where(Venue.id == venue.id)
    res = await db.execute(stmt)
    created_venue = res.scalar_one()
    return VenueResponse.model_validate(created_venue)
