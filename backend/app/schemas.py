from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models import UserRole, EventType, EventStatus, ShowStatus, SeatStatus, HoldStatus, BookingStatus, PaymentStatus, WaitlistStatus, OfferStatus

# User Schemas
class UserRegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Optional[UserRole] = UserRole.CUSTOMER

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Venue & Seat Schemas
class SeatCategoryResponse(BaseModel):
    id: UUID
    venue_id: UUID
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True

class VenueSectionResponse(BaseModel):
    id: UUID
    venue_id: UUID
    name: str
    section_type: Optional[str]

    class Config:
        from_attributes = True

class VenueSeatResponse(BaseModel):
    id: UUID
    venue_id: UUID
    section_id: UUID
    category_id: UUID
    row_label: str
    seat_number: int
    seat_label: str
    x_position: int
    y_position: int

    class Config:
        from_attributes = True

class VenueResponse(BaseModel):
    id: UUID
    name: str
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    sections: List[VenueSectionResponse] = []
    categories: List[SeatCategoryResponse] = []

    class Config:
        from_attributes = True

class CreateVenueRequest(BaseModel):
    name: str
    address: str
    city: str
    state: str
    rows: int = 4
    seats_per_row: int = 8
    vip_rows: int = 1
    premium_rows: int = 1

# Event & Show Schemas
class EventCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    event_type: EventType
    poster_url: Optional[str] = None
    duration_minutes: Optional[int] = 120

class EventResponse(BaseModel):
    id: UUID
    organiser_id: UUID
    title: str
    description: Optional[str]
    event_type: EventType
    poster_url: Optional[str]
    duration_minutes: Optional[int]
    status: EventStatus
    created_at: datetime

    class Config:
        from_attributes = True

class ShowCreateRequest(BaseModel):
    event_id: UUID
    venue_id: UUID
    start_time: datetime
    end_time: Optional[datetime] = None
    prices: dict[str, float] # category_id -> price

class ShowResponse(BaseModel):
    id: UUID
    event_id: UUID
    venue_id: UUID
    start_time: datetime
    end_time: Optional[datetime]
    status: ShowStatus
    event_title: Optional[str] = None
    venue_name: Optional[str] = None

    class Config:
        from_attributes = True

class ShowSeatMapItem(BaseModel):
    id: UUID # show_seat_id
    venue_seat_id: UUID
    category_id: UUID
    category_name: str
    row_label: str
    seat_number: int
    seat_label: str
    x_position: int
    y_position: int
    price: float
    status: SeatStatus
    held_by_current_user: bool = False

# Hold Schemas
class HoldCreateRequest(BaseModel):
    show_id: UUID
    show_seat_ids: List[UUID]
    ttl_seconds: Optional[int] = None

class HoldResponse(BaseModel):
    id: UUID
    show_id: UUID
    hold_token: UUID
    status: HoldStatus
    expires_at: datetime
    show_seat_ids: List[UUID]

    class Config:
        from_attributes = True

# Booking Schemas
class BookingCreateRequest(BaseModel):
    show_id: UUID
    hold_id: UUID
    hold_token: UUID

class BookingResponse(BaseModel):
    id: UUID
    booking_reference: str
    show_id: UUID
    status: BookingStatus
    subtotal: float
    tax: float
    discount: float
    total_amount: float
    currency: str
    created_at: datetime
    confirmed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MockPaymentRequest(BaseModel):
    booking_id: UUID
    payment_method: str = "CARD"
    card_number: Optional[str] = "4242424242424242"

# Waitlist Schemas
class JoinWaitlistRequest(BaseModel):
    show_id: UUID
    category_id: UUID

class WaitlistEntryResponse(BaseModel):
    id: UUID
    show_id: UUID
    category_id: UUID
    category_name: Optional[str] = None
    position: int
    status: WaitlistStatus
    joined_at: datetime

    class Config:
        from_attributes = True

class WaitlistOfferResponse(BaseModel):
    id: UUID
    waitlist_entry_id: UUID
    show_seat_id: UUID
    seat_label: Optional[str] = None
    offer_token: UUID
    status: OfferStatus
    expires_at: datetime

    class Config:
        from_attributes = True

# Ticket Schemas
class TicketResponse(BaseModel):
    id: UUID
    booking_id: UUID
    ticket_reference: str
    qr_payload: str
    qr_code_url: str
    status: str
    issued_at: datetime
    seats: List[str] = []

    class Config:
        from_attributes = True

# Admin Revenue Analytics Schema
class RevenueAnalyticsResponse(BaseModel):
    total_events: int
    total_shows: int
    total_bookings: int
    total_tickets_sold: int
    total_revenue: float
