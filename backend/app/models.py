import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, Numeric, Boolean, BigInteger, 
    DateTime, ForeignKey, Enum as SQLEnum, CheckConstraint, func
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base

# Enums
class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    ORGANISER = "ORGANISER"
    CUSTOMER = "CUSTOMER"

class EventType(str, enum.Enum):
    MOVIE = "MOVIE"
    CONCERT = "CONCERT"
    SPORTS = "SPORTS"
    THEATRE = "THEATRE"

class EventStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"

class ShowStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    ON_SALE = "ON_SALE"
    SOLD_OUT = "SOLD_OUT"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"

class SeatStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    HELD = "HELD"
    BOOKED = "BOOKED"
    OFFERED = "OFFERED"
    BLOCKED = "BLOCKED"

class HoldStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"
    CONVERTED = "CONVERTED"

class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"

class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"

class TicketStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    USED = "USED"
    CANCELLED = "CANCELLED"

class WaitlistStatus(str, enum.Enum):
    WAITING = "WAITING"
    OFFERED = "OFFERED"
    FULFILLED = "FULFILLED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"

class OfferStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ACCEPTED = "ACCEPTED"
    EXPIRED = "EXPIRED"
    DECLINED = "DECLINED"

class NotificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"

class OutboxStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


# ORM Models

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(Text, nullable=False)
    role = Column(SQLEnum(UserRole, name="user_role"), nullable=False, default=UserRole.CUSTOMER)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    events = relationship("Event", back_populates="organiser")
    holds = relationship("Hold", back_populates="user")
    bookings = relationship("Booking", back_populates="user")
    waitlist_entries = relationship("WaitlistEntry", back_populates="user")
    notifications = relationship("Notification", back_populates="user")


class Venue(Base):
    __tablename__ = "venues"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    address = Column(Text)
    city = Column(String)
    state = Column(String)
    country = Column(String, default="India")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    sections = relationship("VenueSection", back_populates="venue", cascade="all, delete-orphan")
    categories = relationship("SeatCategory", back_populates="venue", cascade="all, delete-orphan")
    venue_seats = relationship("VenueSeat", back_populates="venue", cascade="all, delete-orphan")
    shows = relationship("Show", back_populates="venue")


class VenueSection(Base):
    __tablename__ = "venue_sections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    section_type = Column(String)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    venue = relationship("Venue", back_populates="sections")
    venue_seats = relationship("VenueSeat", back_populates="section", cascade="all, delete-orphan")


class SeatCategory(Base):
    __tablename__ = "seat_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    venue = relationship("Venue", back_populates="categories")
    venue_seats = relationship("VenueSeat", back_populates="category")


class VenueSeat(Base):
    __tablename__ = "venue_seats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id", ondelete="CASCADE"), nullable=False)
    section_id = Column(UUID(as_uuid=True), ForeignKey("venue_sections.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("seat_categories.id", ondelete="CASCADE"), nullable=False)
    row_label = Column(String, nullable=False)
    seat_number = Column(Integer, nullable=False)
    seat_label = Column(String, nullable=False)
    x_position = Column(Integer, nullable=False)
    y_position = Column(Integer, nullable=False)
    seat_type = Column(String, default="REGULAR")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    venue = relationship("Venue", back_populates="venue_seats")
    section = relationship("VenueSection", back_populates="venue_seats")
    category = relationship("SeatCategory", back_populates="venue_seats")
    show_seats = relationship("ShowSeat", back_populates="venue_seat")


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organiser_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    event_type = Column(SQLEnum(EventType, name="event_type"), nullable=False)
    poster_url = Column(Text)
    duration_minutes = Column(Integer)
    status = Column(SQLEnum(EventStatus, name="event_status"), nullable=False, default=EventStatus.DRAFT)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    organiser = relationship("User", back_populates="events")
    shows = relationship("Show", back_populates="event", cascade="all, delete-orphan")


class Show(Base):
    __tablename__ = "shows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id", ondelete="CASCADE"), nullable=False)
    section_id = Column(UUID(as_uuid=True), ForeignKey("venue_sections.id", ondelete="SET NULL"), nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    status = Column(SQLEnum(ShowStatus, name="show_status"), nullable=False, default=ShowStatus.SCHEDULED)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    event = relationship("Event", back_populates="shows")
    venue = relationship("Venue", back_populates="shows")
    prices = relationship("ShowPrice", back_populates="show", cascade="all, delete-orphan")
    seats = relationship("ShowSeat", back_populates="show", cascade="all, delete-orphan")
    holds = relationship("Hold", back_populates="show", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="show", cascade="all, delete-orphan")
    waitlist_entries = relationship("WaitlistEntry", back_populates="show", cascade="all, delete-orphan")


class ShowPrice(Base):
    __tablename__ = "show_prices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    show_id = Column(UUID(as_uuid=True), ForeignKey("shows.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("seat_categories.id", ondelete="CASCADE"), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    show = relationship("Show", back_populates="prices")
    category = relationship("SeatCategory")


class ShowSeat(Base):
    __tablename__ = "show_seats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    show_id = Column(UUID(as_uuid=True), ForeignKey("shows.id", ondelete="CASCADE"), nullable=False)
    venue_seat_id = Column(UUID(as_uuid=True), ForeignKey("venue_seats.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("seat_categories.id", ondelete="CASCADE"), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    status = Column(SQLEnum(SeatStatus, name="seat_status"), nullable=False, default=SeatStatus.AVAILABLE)
    version = Column(BigInteger, nullable=False, default=0) # Optimistic locking counter
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    show = relationship("Show", back_populates="seats")
    venue_seat = relationship("VenueSeat", back_populates="show_seats")
    category = relationship("SeatCategory")
    hold_items = relationship("HoldItem", back_populates="show_seat")
    booking_seats = relationship("BookingSeat", back_populates="show_seat")


class Hold(Base):
    __tablename__ = "holds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    show_id = Column(UUID(as_uuid=True), ForeignKey("shows.id", ondelete="CASCADE"), nullable=False)
    hold_token = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4, unique=True)
    status = Column(SQLEnum(HoldStatus, name="hold_status"), nullable=False, default=HoldStatus.ACTIVE)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    released_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="holds")
    show = relationship("Show", back_populates="holds")
    hold_items = relationship("HoldItem", back_populates="hold", cascade="all, delete-orphan")


class HoldItem(Base):
    __tablename__ = "hold_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hold_id = Column(UUID(as_uuid=True), ForeignKey("holds.id", ondelete="CASCADE"), nullable=False)
    show_seat_id = Column(UUID(as_uuid=True), ForeignKey("show_seats.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    hold = relationship("Hold", back_populates="hold_items")
    show_seat = relationship("ShowSeat", back_populates="hold_items")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_reference = Column(String, nullable=False, unique=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    show_id = Column(UUID(as_uuid=True), ForeignKey("shows.id", ondelete="CASCADE"), nullable=False)
    hold_id = Column(UUID(as_uuid=True), ForeignKey("holds.id", ondelete="SET NULL"), nullable=True)
    status = Column(SQLEnum(BookingStatus, name="booking_status"), nullable=False, default=BookingStatus.PENDING)
    subtotal = Column(Numeric(10, 2), nullable=False, default=0)
    tax = Column(Numeric(10, 2), nullable=False, default=0)
    discount = Column(Numeric(10, 2), nullable=False, default=0)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="INR")
    idempotency_key = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="bookings")
    show = relationship("Show", back_populates="bookings")
    hold = relationship("Hold")
    seats = relationship("BookingSeat", back_populates="booking", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="booking", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="booking", cascade="all, delete-orphan")


class BookingSeat(Base):
    __tablename__ = "booking_seats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    show_seat_id = Column(UUID(as_uuid=True), ForeignKey("show_seats.id", ondelete="CASCADE"), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    booking = relationship("Booking", back_populates="seats")
    show_seat = relationship("ShowSeat", back_populates="booking_seats")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String, nullable=False)
    provider_payment_id = Column(String)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    status = Column(SQLEnum(PaymentStatus, name="payment_status"), nullable=False, default=PaymentStatus.PENDING)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    booking = relationship("Booking", back_populates="payments")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    ticket_reference = Column(String, nullable=False, unique=True)
    qr_payload = Column(Text, nullable=False)
    qr_code_url = Column(Text)
    status = Column(SQLEnum(TicketStatus, name="ticket_status"), nullable=False, default=TicketStatus.ACTIVE)
    issued_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    used_at = Column(DateTime(timezone=True))

    booking = relationship("Booking", back_populates="tickets")


class WaitlistEntry(Base):
    __tablename__ = "waitlist_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    show_id = Column(UUID(as_uuid=True), ForeignKey("shows.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("seat_categories.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    position = Column(Integer, nullable=False)
    status = Column(SQLEnum(WaitlistStatus, name="waitlist_status"), nullable=False, default=WaitlistStatus.WAITING)
    joined_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    show = relationship("Show", back_populates="waitlist_entries")
    category = relationship("SeatCategory")
    user = relationship("User", back_populates="waitlist_entries")
    offers = relationship("WaitlistOffer", back_populates="waitlist_entry", cascade="all, delete-orphan")


class WaitlistOffer(Base):
    __tablename__ = "waitlist_offers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    waitlist_entry_id = Column(UUID(as_uuid=True), ForeignKey("waitlist_entries.id", ondelete="CASCADE"), nullable=False)
    show_seat_id = Column(UUID(as_uuid=True), ForeignKey("show_seats.id", ondelete="CASCADE"), nullable=False)
    offer_token = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4, unique=True)
    status = Column(SQLEnum(OfferStatus, name="offer_status"), nullable=False, default=OfferStatus.ACTIVE)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    accepted_at = Column(DateTime(timezone=True))

    waitlist_entry = relationship("WaitlistEntry", back_populates="offers")
    show_seat = relationship("ShowSeat")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, nullable=False)
    channel = Column(String, nullable=False)
    reference_type = Column(String)
    reference_id = Column(UUID(as_uuid=True))
    status = Column(SQLEnum(NotificationStatus, name="notification_status"), nullable=False, default=NotificationStatus.PENDING)
    error_message = Column(Text)
    sent_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user = relationship("User", back_populates="notifications")


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregate_type = Column(String, nullable=False)
    aggregate_id = Column(UUID(as_uuid=True), nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSONB, nullable=False)
    status = Column(SQLEnum(OutboxStatus, name="outbox_status"), nullable=False, default=OutboxStatus.PENDING)
    retry_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    last_error = Column(Text)
