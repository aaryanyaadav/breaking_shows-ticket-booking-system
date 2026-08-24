# 🎟️ Ticketsmith - Ticket Booking Platform

An enterprise-grade, high-concurrency event ticketing and seat allocation platform built with **FastAPI**, **PostgreSQL**, **Redis**, **WebSockets**, **Docker**, and **React**.

Designed to handle flash-sale ticket traffic with **zero double-bookings**, **atomic Redis Lua seat locking**, **10-minute hold TTLs**, **category-aware FIFO waitlists**, and **automated QR ticket pass dispatch**.

---

## 📸 Screenshots & Visual Tour

### 1. Customer Portal: Event Discovery & Booking Flow
Browse live movies, shows, and concerts, inspect showtimes, select multi-seat batches, and generate secure scannable digital QR passes.

![Customer UI & Event Discovery](docs/screenshots/customer_portal_ui.png)

---

### 2. Interactive Real-Time Seat Matrix (Customer UI)
Select VIP, Premium, or Standard seats with instant optimistic locking and live WebSocket occupancy updates across connected clients.

![Customer Seat Selection Matrix](docs/screenshots/screen.png)

---

### 3. Organiser Financial Dashboard & Customer Ticket Audit
Monitor real-time gross INR revenue, view per-tier sales distributions, and audit individual customer bookings with assigned seat numbers and payment statuses.

![Organiser Analytics Dashboard](docs/screenshots/portal.png)

---

## 🏗️ High-Level System Architecture

```mermaid
flowchart TD
    subgraph Clients["Client Layer"]
        C1["Customer Web App"]
        C2["Organiser Portal"]
        C3["Master Admin Console"]
    end

    subgraph AppServer["FastAPI Application Services"]
        API["FastAPI REST Endpoints"]
        WS["WebSocket Real-Time Manager"]
        Worker["Background Scheduler & TTL Cleaner"]
        EmailEngine["Transactional Cloud Email Engine"]
    end

    subgraph InMem["In-Memory & Distributed Locking"]
        Redis[("Redis In-Memory Database\nAtomic Lua Locks")]
    end

    subgraph DurableDB["Durable Persistence Layer"]
        Postgres[("PostgreSQL Database\nACID Ledger & Version Counters")]
    end

    C1 -->|JWT REST Calls| API
    C2 -->|Event & Sales Management| API
    C3 -->|Venue Layout Configuration| API

    API <-->|Atomic Lua Locks| Redis
    API <-->|Async ORM & SQL Ledger| Postgres
    API -->|Broadcast Seat Updates| WS
    WS -->|Live Seat Matrix Feeds| C1

    Worker <-->|Check Expired Holds & Offers| Postgres
    Worker -->|Trigger Auto-Assignment| EmailEngine
    EmailEngine -->|HTML Passes & QR Tickets| C1
```

---

## 🚀 Key Features & Capabilities

- **Strict Role-Based Access Control (RBAC)**:
  - **Master Admin**: Manage physical auditorium venues, build custom seat grid layouts (Rows, Seats per Row, VIP/Premium/Standard tiers), audit platform health, and oversee all organiser listings.
  - **Organisers**: Create, update, and delete events, schedule multi-screen showtimes, monitor gross INR revenue, and export customer ticket audit ledgers.
  - **Customers**: Search events, inspect real-time interactive seat maps, lock seats atomically, complete checkout, view digital QR tickets, and claim waitlist offers.
- **Atomic Multi-Seat Concurrency Protection**: Redis Lua scripts serialize concurrent seat selection requests, guaranteeing two customers can never hold or buy the same seat simultaneously.
- **Configurable Hold TTL (600s)**: 10-minute transient hold expiration with background worker cleanup and instant WebSocket seat matrix synchronization.
- **Category-Aware FIFO Waitlist**: Sold-out seat category queues (`VIP`, `PREMIUM`, `STANDARD`) with automated seat re-assignment upon cancellation.
- **15-Minute Exclusive Seat Offers**: Time-limited claim links sent to waitlisted customers with automatic cascading to the next user in line upon expiry.
- **Digital QR Ticket Passes**: High-resolution QR codes encoding booking reference, ticket reference, and customer email, attached to email confirmations and customer dashboards.
- **Multi-Channel Cloud Email Dispatch**: Resilient transactional email delivery supporting **MailerSend REST API**, **Resend HTTP API**, and **Brevo HTTP API** over Port 443 HTTPS.

---

## 🗄️ Database Schema and Entity Relationships

The platform uses a relational PostgreSQL database schema with strict foreign key constraints, cascading rules, and optimistic locking version counters.

```mermaid
erDiagram
    USERS ||--o{ EVENTS : organizes
    USERS ||--o{ HOLDS : initiates
    USERS ||--o{ BOOKINGS : places
    USERS ||--o{ WAITLIST_ENTRIES : joins
    
    VENUES ||--o{ VENUE_SEATS : contains
    VENUES ||--o{ SEAT_CATEGORIES : defines
    VENUES ||--o{ SHOWS : hosts
    
    EVENTS ||--o{ SHOWS : schedules
    SHOWS ||--o{ SHOW_SEATS : allocates
    
    VENUE_SEATS ||--o{ SHOW_SEATS : templates
    SEAT_CATEGORIES ||--o{ VENUE_SEATS : classifies
    
    HOLDS ||--o{ HOLD_ITEMS : contains
    SHOW_SEATS ||--o{ HOLD_ITEMS : reserved_in
    
    BOOKINGS ||--o{ BOOKING_SEATS : contains
    BOOKINGS ||--o{ PAYMENTS : settles
    BOOKINGS ||--o{ TICKETS : issues
    SHOW_SEATS ||--o{ BOOKING_SEATS : booked_as
    
    SHOWS ||--o{ WAITLIST_ENTRIES : queues
    WAITLIST_ENTRIES ||--o{ WAITLIST_OFFERS : receives
```

### Table Definitions & Constraints

| Table | Description | Primary Key | Foreign Keys / Constraints |
| :--- | :--- | :--- | :--- |
| `users` | Customer, Organiser, and Master Admin accounts | `id` (UUID) | `email` UNIQUE, `role` ENUM (`CUSTOMER`, `ORGANISER`, `ADMIN`) |
| `venues` | Screen auditoriums and physical venues | `id` (UUID) | `name` UNIQUE, `created_by` -> `users.id` |
| `seat_categories` | Pricing and tier classifications | `id` (UUID) | `venue_id` -> `venues.id`, `name` (`VIP`, `PREMIUM`, `STANDARD`) |
| `venue_seats` | Base physical seating grid | `id` (UUID) | `venue_id` -> `venues.id`, `category_id` -> `seat_categories.id`, UNIQUE(`venue_id`, `seat_label`) |
| `events` | Movies, concerts, and live shows | `id` (UUID) | `organiser_id` -> `users.id` (ON DELETE CASCADE) |
| `shows` | Scheduled showtimes for events at venues | `id` (UUID) | `event_id` -> `events.id`, `venue_id` -> `venues.id` |
| `show_seats` | Real-time seat inventory per show | `id` (UUID) | `show_id` -> `shows.id`, `venue_seat_id` -> `venue_seats.id`, `version` INT (Optimistic Lock) |
| `holds` | 10-minute transient seat hold reservations | `id` (UUID) | `user_id` -> `users.id`, `show_id` -> `shows.id`, `hold_token` UNIQUE |
| `hold_items` | Individual seats locked under a hold | `id` (UUID) | `hold_id` -> `holds.id` (ON DELETE CASCADE), `show_seat_id` -> `show_seats.id` |
| `bookings` | Confirmed financial transactions | `id` (UUID) | `booking_reference` UNIQUE, `user_id` -> `users.id`, `show_id` -> `shows.id` |
| `booking_seats` | Confirmed seat items linked to booking | `id` (UUID) | `booking_id` -> `bookings.id` (ON DELETE CASCADE), `show_seat_id` -> `show_seats.id` |
| `payments` | Transaction receipts and payment audit | `id` (UUID) | `booking_id` -> `bookings.id`, `provider_payment_id` |
| `tickets` | QR payload and digital ticket passes | `id` (UUID) | `ticket_reference` UNIQUE, `booking_id` -> `bookings.id` |
| `waitlist_entries` | FIFO queue for sold-out seat tiers | `id` (UUID) | `show_id` -> `shows.id`, `category_id` -> `seat_categories.id`, `user_id` -> `users.id` |
| `waitlist_offers` | 15-minute time-limited claim offers | `id` (UUID) | `waitlist_entry_id` -> `waitlist_entries.id`, `show_seat_id` -> `show_seats.id` |

---

## 🔒 Seat Hold and Concurrency Control Logic

In flash-sale event ticketing, thousands of concurrent requests can target the exact same seat within milliseconds. Ticketsmith solves this using a **two-tier locking strategy**: **In-Memory Redis Lua Atomic Locks** + **Database Optimistic Concurrency Control**.

```mermaid
sequenceDiagram
    autonumber
    actor Customer1 as Customer A
    actor Customer2 as Customer B
    participant API as FastAPI Backend
    participant Redis as Redis (Atomic Lua)
    participant DB as PostgreSQL
    participant WS as WebSocket Broadcast
    
    Customer1->>API: POST /api/v1/holds (Seats A1, A2)
    Customer2->>API: POST /api/v1/holds (Seat A1)
    
    Note over API,Redis: Redis Lua Script Serialization
    API->>Redis: Execute Lua: EVAL hold_seats.lua
    Redis-->>API: 1 (SUCCESS - Customer A acquires keys)
    
    API->>Redis: Execute Lua: EVAL hold_seats.lua
    Redis-->>API: 0 (FAILED - Key 'hold:A1' already locked)
    
    API->>DB: INSERT INTO holds (expires_at = NOW() + 10m)
    API->>DB: UPDATE show_seats SET status='HELD', version=version+1
    
    API-->>Customer1: 201 Created (Hold Token Issued)
    API-->>Customer2: 409 Conflict ("Seat already reserved by another user")
    
    API->>WS: Broadcast SEAT_STATUS_CHANGED (A1, A2 = HELD)
    WS-->>Customer2: Real-time map updates A1 to HELD (Yellow)
```

### 1. Redis Lua Atomic Lock (`execute_atomic_hold`)
HTTP requests operate concurrently across multiple asynchronous worker processes. A naive check-then-set approach (`SELECT status FROM show_seats WHERE id = seat_id`) produces classic TOCTOU (Time-Of-Check to Time-Of-Use) race conditions. 

Ticketsmith executes an atomic Redis Lua script that checks and locks all requested seats in a single atomic CPU cycle:

```lua
-- Atomic Multi-Seat Hold Lua Script
for i, key in ipairs(KEYS) do
    if redis.call('EXISTS', key) == 1 then
        return {0, key} -- Seat already held by another customer
    end
end

for i, key in ipairs(KEYS) do
    redis.call('SET', key, ARGV[1], 'EX', ARGV[3]) -- Atomically lock seat with 600s TTL
end
return {1, "OK"}
```

Because Redis executes Lua scripts sequentially on its main thread, concurrent requests targeting overlapping seats are strictly serialized. The winning request acquires the lock; all losing requests fail immediately with **HTTP 409 Conflict**.

### 2. Database Optimistic Versioning
At the persistent database layer, each `show_seats` record maintains an integer `version` counter. When transitioning a seat from `HELD` to `BOOKED` during payment confirmation:

```sql
UPDATE show_seats 
SET status = 'BOOKED', version = version + 1 
WHERE id IN (:seat_ids) AND version = :expected_version;
```
If any concurrent mutation altered the seat version in between, the query affects 0 rows, triggering an automatic rollback to prevent double-allocation.

### 3. Background TTL Expiration Worker
A background async task runs periodically every 15 seconds:
- Queries active holds where `expires_at < NOW()`.
- Transitions expired holds to `EXPIRED`.
- Reverts the corresponding `show_seats` back to `AVAILABLE`.
- Emits real-time WebSocket events (`SEAT_STATUS_CHANGED`) to all connected browser clients.

---

## ⏳ Category-Aware Waitlist Queue & Auto-Assignment Logic

When an event or specific seat tier (`VIP`, `PREMIUM`, `STANDARD`) sells out (`AVAILABLE == 0`), customers can join a category-specific FIFO waitlist queue.

```mermaid
flowchart TD
    A[Booking Cancelled / Seat Released] --> B{Check Category Queue}
    B -->|Waitlist Entry Found| C[Select Lowest Position WAITING Customer]
    B -->|Queue Empty| D[Revert Seat Status to AVAILABLE]
    
    C --> E[Set ShowSeat Status = OFFERED]
    E --> F[Generate WaitlistOffer with 15-Minute TTL]
    F --> G[Send Email Notification with Claim Link]
    
    G --> H{Customer Claims Offer within 15 mins?}
    H -->|Yes: Click Link & Accept| I[Convert Offer to Active 10-Min Hold]
    I --> J[Proceed to Payment & Issue QR Ticket]
    
    H -->|No: TTL Expires| K[Mark Offer EXPIRED]
    K --> L[Select Next Customer in Queue: position + 1]
    L --> E
```

### Waitlist Lifecycle & Cascading Auto-Assignment

1. **Queue Registration**: Customer calls `POST /api/v1/waitlist/join`. The system records a `WaitlistEntry` with an incremental `position` index for that specific `(show_id, category_id)`.
2. **Seat Release Trigger**: When an existing booking is cancelled via `POST /api/v1/bookings/{id}/cancel` (or released due to payment failure):
   - The system inspects the `category_id` of the released seat.
   - Queries `waitlist_entries` for the lowest `position` where `status = 'WAITING'`.
3. **Offer Generation (15-Minute TTL)**:
   - Sets `ShowSeat.status = 'OFFERED'`.
   - Transitions `WaitlistEntry.status = 'OFFERED'`.
   - Creates a `WaitlistOffer` record with `expires_at = NOW() + 15 minutes`.
   - Dispatches an automated email notification containing an exclusive claim link.
4. **Offer Acceptance**:
   - Customer calls `POST /api/v1/waitlist/offers/{offer_id}/accept`.
   - Validates `status == 'ACTIVE'` and `expires_at > NOW()`.
   - Converts the offer into an active 10-minute hold and routes customer to checkout.
5. **Auto-Cascading on Expiry**:
   - If the 15-minute offer TTL expires without claim, the offer is marked `EXPIRED`.
   - The background scheduler automatically invokes the assignment engine to offer the seat to the next user in line (`position + 1`). This repeats recursively until the seat is claimed or the queue is exhausted.

---

## 📡 REST API Documentation

### 🔐 Authentication (`/api/v1/auth`)

| Method | Endpoint | Access | Description | Request Body / Parameters | Response |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Public | Register Customer or Organiser | `{ "name": "...", "email": "...", "password": "...", "role": "CUSTOMER" }` | `201 Created` (User Object) |
| `POST` | `/api/v1/auth/login` | Public | OAuth2 JWT Login | Form Data: `username`, `password` | `{ "access_token": "...", "token_type": "bearer", "user": {...} }` |
| `GET` | `/api/v1/auth/me` | Authenticated | Get current profile | Header: `Authorization: Bearer <token>` | `200 OK` (Current User Profile) |

---

### 🎭 Events & Organiser Management (`/api/v1/events`)

| Method | Endpoint | Access | Description | Request Body / Parameters | Response |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/events` | Public | List all active events | Query: `search`, `category` | `200 OK` (Array of Events) |
| `GET` | `/api/v1/events/{id}` | Public | Get event details with shows | Path: `id` | `200 OK` (Event with Shows & Venues) |
| `POST` | `/api/v1/events` | Organiser / Admin | Create a new event listing | `{ "title": "...", "description": "...", "banner_url": "...", "duration_minutes": 120 }` | `201 Created` |
| `GET` | `/api/v1/events/organiser-analytics` | Organiser / Admin | Financial revenue & customer ticket audit ledger | Header: `Authorization: Bearer <token>` | `200 OK` (Gross INR, bookings, seat numbers) |
| `DELETE` | `/api/v1/events/{id}` | Organiser / Admin | Delete event & cascade shows | Path: `id` | `200 OK` |

---

### 🏛️ Venues & Screen Auditoriums (`/api/v1/venues`)

| Method | Endpoint | Access | Description | Request Body / Parameters | Response |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/venues` | Authenticated | List all physical screen venues | Header: `Authorization: Bearer <token>` | `200 OK` (Array of Venues with Layouts) |
| `POST` | `/api/v1/venues` | Admin | Build custom auditorium grid | `{ "name": "Screen 1", "rows": 8, "seats_per_row": 12, "categories": [...] }` | `201 Created` |

---

### 🎬 Shows & Inventory (`/api/v1/shows`)

| Method | Endpoint | Access | Description | Request Body / Parameters | Response |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/shows/{id}/seats` | Public | Get real-time seat status matrix | Path: `id` | `200 OK` (Seat grid with `status`, `tier`, `price`) |
| `POST` | `/api/v1/shows` | Organiser / Admin | Schedule showtime at venue | `{ "event_id": "...", "venue_id": "...", "start_time": "...", "pricing": {...} }` | `201 Created` |

---

### 🔒 Seat Holds (`/api/v1/holds`)

| Method | Endpoint | Access | Description | Request Body / Parameters | Response |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/holds` | Authenticated | Atomically reserve multi-seat batch (10-min TTL) | `{ "show_id": "...", "seat_ids": ["uuid-1", "uuid-2"] }` | `201 Created` (`hold_token`, `expires_at`) |
| `DELETE` | `/api/v1/holds/{hold_id}` | Authenticated | Release held seats manually | Path: `hold_id` | `200 OK` |

---

### 💳 Bookings & Checkout (`/api/v1/bookings`)

| Method | Endpoint | Access | Description | Request Body / Parameters | Response |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/bookings` | Authenticated | Create pending booking from hold | `{ "hold_token": "...", "idempotency_key": "IDEM-..." }` | `201 Created` (`booking_reference`, `total_amount`) |
| `POST` | `/api/v1/bookings/mock-pay` | Authenticated | Confirm payment, issue QR ticket & dispatch email | `{ "booking_id": "...", "payment_method": "CARD" }` | `200 OK` (`ticket_reference`, `qr_code_url`) |
| `GET` | `/api/v1/bookings/my` | Authenticated | List current user bookings | Header: `Authorization: Bearer <token>` | `200 OK` (Bookings list with QR codes) |
| `POST` | `/api/v1/bookings/{id}/cancel` | Authenticated | Cancel booking & trigger waitlist auto-offer | Path: `id` | `200 OK` (Seat offered to next in queue) |

---

### ⏳ Waitlists & Offers (`/api/v1/waitlist`)

| Method | Endpoint | Access | Description | Request Body / Parameters | Response |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/waitlist/join` | Authenticated | Join FIFO queue for sold-out tier | `{ "show_id": "...", "category_id": "..." }` | `201 Created` (`position`, `status`) |
| `GET` | `/api/v1/waitlist/my-offers` | Authenticated | List active 15-min claim offers | Header: `Authorization: Bearer <token>` | `200 OK` (Active offers with countdown) |
| `POST` | `/api/v1/waitlist/offers/{id}/accept` | Authenticated | Claim offer & convert to 10-min hold | Path: `id` | `200 OK` (Converted to active hold) |

---

### 🔌 WebSocket Real-Time Channel

- **Endpoint**: `WS /ws/shows/{show_id}`
- **Protocol**: JSON message broadcast
- **Event Payload Example**:
  ```json
  {
    "event": "SEAT_STATUS_CHANGED",
    "show_id": "e26836f9-0afb-4558-b137-fc13d89a14fb",
    "seat_ids": ["c1a82f34-3112-4c22-9599-281b90d3d512"],
    "status": "HELD",
    "timestamp": "2026-08-24T20:15:00Z"
  }
  ```

---

## ⚙️ Environment Configuration (`.env.example`)

```env
# Database Configuration (PostgreSQL)
POSTGRES_USER=ticket_user
POSTGRES_PASSWORD=ticket_password
POSTGRES_DB=ticket_booking_db
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://ticket_user:ticket_password@postgres:5432/ticket_booking_db

# Redis In-Memory & Atomic Lock Cache
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0

# Security & JWT Configuration
SECRET_KEY=super-secret-jwt-key-for-ticket-booking-platform-2026
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Hold & Waitlist Timers (Seconds)
DEFAULT_HOLD_TTL_SECONDS=600
OFFER_TTL_SECONDS=900

# Transactional Cloud Email API Keys (Port 443 HTTPS)
MAILERSEND_API_KEY=mlsn.your_mailersend_key_here
MAILERSEND_FROM=
RESEND_API_KEY=
BREVO_API_KEY=

# Local / VPS Fallback SMTP (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
SMTP_FROM=
```

---

## 📄 License & Standards

Built with enterprise concurrency and fault-tolerance patterns by **Ticketsmith Engineering**. 

Licensed under the **MIT License**. Open-source for high-scale event allocation architectures.
