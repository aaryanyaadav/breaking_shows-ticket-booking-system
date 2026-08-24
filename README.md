# Ticketsmith - Ticket Booking Platform

High-concurrency ticket booking platform built with FastAPI, PostgreSQL, Redis, WebSockets, Docker, and React.

## Table of Contents
1. Features and Capabilities
2. Quickstart and Setup Guide
3. Database Structure Explanation & Local vs Production Setup
4. Production Deployment Guide (Cloud / VPS)
5. Environment Configuration (.env.example)
6. Database Schema and Relationships
7. REST API Documentation
8. System Design Write-Up & Mermaid Architecture Diagrams

---

## Features and Capabilities

- Role-Based Portals (CUSTOMER / ORGANISER / ADMIN):
  - Admin Console: Build custom physical screen venues (Rows, Seats per Row, VIP / Premium / Standard tiers), monitor global platform revenue, and audit registered Organisers & listings.
  - Organiser Portal: Financial control dashboard with total earnings (INR), customer ticket audit tables (Name, Email, Assigned Seat Numbers), per-category sales metrics, show scheduling, and event deletion.
  - Customer Flow: Browse events, interactive seat selection, atomic checkout, QR ticket generation, and waitlist management.
- Atomic Concurrency Protection: Multi-seat locking powered by Redis Lua scripts to guarantee two customers can never hold or book the same seat simultaneously.
- Configurable Hold TTL: 10-minute hold TTL with automated background expiration worker and WebSocket seat map broadcasts.
- Category-Aware Waitlist Queue: Sold-out seat category queues (VIP, PREMIUM, STANDARD) with automated seat re-assignment upon booking cancellation.
- Time-Limited Seat Offers: 15-minute exclusive claim link notifications sent to waitlisted users via free email notification service.
- QR Code Tickets: High-resolution QR codes encoding booking reference, ticket reference, and customer email, attached to confirmation emails and UI passes.

---

## Database Structure & Local vs Production Overview

### 1. Database Structure
The application uses a **relational database model** designed in **PostgreSQL** (managed asynchronously via SQLAlchemy ORM):

- **User Accounts (`users`)**: Stores Customer, Organiser, and Admin profiles, hashed passwords, and role ENUMs.
- **Auditoriums & Layout Grids (`venues`, `venue_seats`)**: Stores screen auditoriums and their seating grid coordinates (Row A, B, C... x Seat 1, 2, 3...).
- **Seat Category Tiers (`seat_categories`)**: Allocates `VIP`, `PREMIUM`, and `STANDARD` seat sections to screen venues.
- **Events & Shows (`events`, `shows`)**: Connects Organiser-created events to scheduled showtimes at screen venues.
- **Show Inventory (`show_seats`)**: Tracks real-time status (`AVAILABLE`, `HELD`, `BOOKED`, `OFFERED`), price, and optimistic locking `version` counter per seat.
- **Transient Holds (`holds`, `hold_items`)**: Stores 10-minute hold reservations with unique `hold_token` UUIDs.
- **Financial Ledger (`bookings`, `booking_seats`, `payments`, `tickets`)**: Stores booking references (`BK-XXXXXX`), confirmed seat items, payment status, and base64 QR tickets.
- **Category Waitlists (`waitlist_entries`, `waitlist_offers`)**: Tracks FIFO customer queue position per category and active 15-minute time-limited claim offers.

### 2. Is it Local?
- **Yes, for development**: By default, PostgreSQL runs locally inside a dedicated Docker container (`ticket_postgres`) on port `5432`.
- Data is persisted locally on your computer via Docker named volumes (`postgres_data`).
- Redis also runs locally inside container `ticket_redis` on port `6379`.

---

## Production Deployment Guide

Deploying Ticketsmith to production can be done in two ways:

### Option A: Managed Cloud Deployment (AWS / Render / Railway / Vercel) - Recommended

1. **Database**: Provision a managed PostgreSQL instance (e.g. AWS RDS PostgreSQL, Render PostgreSQL, or Railway Postgres). Obtain your production connection string:
   `postgresql+asyncpg://user:pass@production-db-host:5432/ticket_db`
2. **In-Memory Redis**: Provision a managed Redis instance (e.g. AWS ElastiCache, Redis Cloud, or Upstash).
3. **Backend API (FastAPI)**: Deploy the backend container to AWS ECS, Render, or Railway. Set environment variables (`DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `SMTP_*`).
4. **Frontend UI (React Vite)**: Build the static bundle (`npm run build`) and deploy `dist/` to Vercel, Netlify, or AWS S3 + CloudFront.

### Option B: Single VPS Deployment (DigitalOcean / EC2 / Hetzner)

1. Provision a VPS running Ubuntu 22.04 LTS.
2. Install Docker and Docker Compose:
   ```bash
   sudo apt update && sudo apt install -y docker.io docker-compose
   ```
3. Clone the codebase and configure production passwords in `.env`:
   ```bash
   cp .env.example .env
   ```
4. Run in detached background mode:
   ```bash
   docker-compose up -d --build
   ```
5. Set up Nginx as a reverse proxy with Certbot for free SSL:
   ```bash
   sudo apt install -y nginx certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

---

## Environment Configuration (.env.example)

```env
POSTGRES_USER=ticket_user
POSTGRES_PASSWORD=ticket_password
POSTGRES_DB=ticket_booking_db
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://ticket_user:ticket_password@postgres:5432/ticket_booking_db

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0

SECRET_KEY=super-secret-jwt-key-for-ticket-booking-platform-2026
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

DEFAULT_HOLD_TTL_SECONDS=600
OFFER_TTL_SECONDS=900

BACKEND_URL=http://backend:8000
```

---

## Database Schema and Relationships

PostgreSQL relational integrity (FOREIGN KEY ... ON DELETE CASCADE):
- `users`: User accounts with role ENUM (CUSTOMER, ORGANISER, ADMIN).
- `venues`: Physical auditorium screens and layout dimensions.
- `venue_seats`: Base physical seating layout grid (row, number, category).
- `events`: Published movie/concert/event listings owned by Organiser.
- `shows`: Scheduled showtimes mapped to venues and events.
- `show_seats`: Per-show seat inventory, prices, status (AVAILABLE, HELD, BOOKED, OFFERED), and version counter.
- `holds`: Active transient seat holds with 10-minute TTL.
- `bookings`: Confirmed customer booking references and transaction amounts.
- `tickets`: QR payload passes issued upon payment.
- `waitlist_entries`: FIFO queue per category for sold-out shows.
- `waitlist_offers`: Time-limited (15-min) seat claim offers assigned to next-in-line waitlisted users.

---

## REST API Documentation

### Auth (/api/v1/auth)
- POST /api/v1/auth/register - Register customer/organiser/admin
- POST /api/v1/auth/login - Login and receive JWT
- GET /api/v1/auth/me - Authenticated user profile

### Events & Organiser Analytics (/api/v1/events)
- GET /api/v1/events - Browse published events
- GET /api/v1/events/organiser-analytics - Per-event earnings & customer ticket details
- POST /api/v1/events - Create new event (Organiser)
- DELETE /api/v1/events/{id} - Delete event & cascade bookings (Organiser/Admin)

### Venues & Seats (/api/v1/venues)
- GET /api/v1/venues - List screen venues
- POST /api/v1/venues - Build custom seat grid layout (Admin)

### Holds & Bookings (/api/v1/holds, /api/v1/bookings)
- POST /api/v1/holds - Atomic multi-seat lock with 10-min TTL
- POST /api/v1/bookings - Create pending booking
- POST /api/v1/bookings/mock-pay - Execute payment & generate QR ticket
- POST /api/v1/bookings/{id}/cancel - Cancel booking & auto-offer to waitlist

### Waitlist (/api/v1/waitlist)
- POST /api/v1/waitlist/join - Join category waitlist
- GET /api/v1/waitlist/my-offers - List active 15-min seat claim offers
- POST /api/v1/waitlist/offers/{id}/accept - Accept offer & claim seat hold

---

## System Design Write-Up & Mermaid Architecture Diagrams

### 🏗️ High-Level System Architecture Diagram

```mermaid
graph TD
    subgraph Clients["Client Layer"]
        C1["Customer Web Browser"]
        C2["Organiser Portal"]
        C3["Admin Console"]
    end

    subgraph AppServer["Application Services (FastAPI + Python)"]
        API["FastAPI REST Endpoints"]
        WS["WebSocket Manager"]
        BackgroundWorker["Background Scheduler & TTL Cleaner"]
        EmailSvc["Free Email Notification Service"]
    end

    subgraph InMem["In-Memory & Distributed Lock Layer"]
        Redis[("Redis Database\nAtomic Lua Scripting\nTransient Seat Holds TTL")]
    end

    subgraph RelationalDB["Durable Storage Layer"]
        Postgres[("PostgreSQL Database\nACID Transactions & Constraints\nOptimistic Version Counters")]
    end

    C1 -->|REST API Requests| API
    C2 -->|Manage Events & Financial Audit| API
    C3 -->|Build Venues & Screen Layouts| API
    
    API <-->|Atomic Lua Locks| Redis
    API <-->|Async ORM / SQL| Postgres
    API -->|Broadcast Seat Map Updates| WS
    WS -->|Real-Time Status Feeds| C1
    
    BackgroundWorker <-->|Check Expired Holds & Offers| Postgres
    BackgroundWorker -->|Trigger Auto-Offers| EmailSvc
    EmailSvc -->|HTML Ticket & Claim Links| C1
```

---

### 🔒 Atomic Seat Hold & Concurrency Control Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Customer1 as Customer A
    actor Customer2 as Customer B
    participant API as FastAPI Backend
    participant Redis as Redis (Atomic Lua)
    participant DB as PostgreSQL
    participant WS as WebSocket Clients

    Customer1->>API: POST /api/v1/holds (Seat A1)
    Customer2->>API: POST /api/v1/holds (Seat A1)
    
    Note over API,Redis: Redis Lua Script Serialization
    API->>Redis: Execute Lua: EXCLUDE_IF_EXISTS(A1)
    Redis-->>API: 1 (SUCCESS - Lock acquired by Customer A)
    
    API->>Redis: Execute Lua: EXCLUDE_IF_EXISTS(A1)
    Redis-->>API: 0 (FAILED - Key already exists)
    
    API->>DB: INSERT INTO holds (expires_at = NOW() + 10m)
    API->>DB: UPDATE show_seats SET status='HELD', version=version+1
    
    API-->>Customer1: 201 CREATED (Hold Token Issued)
    API-->>Customer2: 409 CONFLICT ("Race condition detected! Seat occupied")
    
    API->>WS: Broadcast SEAT_STATUS_CHANGED (Seat A1 = HELD)
    WS-->>Customer2: Visual Seat Map Updates to HELD
```

---

### ⏳ Category Waitlist Auto-Assignment Flowchart

```mermaid
flowchart TD
    A[Booking Cancelled / Seat Released] --> B{Check Category Queue}
    B -->|Waitlist Entry Found| C[Select Lowest Position WAITING Customer]
    B -->|Queue Empty| D[Revert Seat Status to AVAILABLE]
    
    C --> E[Set ShowSeat Status = OFFERED]
    E --> F[Generate WaitlistOffer with 15-Minute TTL]
    F --> G[Send Email Notification with Time-Limited Claim Link]
    
    G --> H{Customer Claims Offer within 15 mins?}
    H -->|Yes: Click Link & Accept| I[Convert Offer to Active 10-Min Hold]
    I --> J[Proceed to Payment & Issue QR Ticket]
    
    H -->|No: TTL Expires| K[Mark Offer EXPIRED]
    K --> L[Select Next Customer in Queue position+1]
    L --> E
```

---

### 1. Seat Hold and TTL Mechanism
In high-concurrency event ticketing systems, inventory reservations must remain transient until financial settlement. Ticketsmith implements a two-tier hold mechanism combining in-memory Redis key-space expiration with durable PostgreSQL transactions.

When a customer selects a batch of seats, the client requests a hold via POST /api/v1/holds. The backend assigns a unique hold_token (UUIDv4) and sets a configurable Time-To-Live (TTL) of 10 minutes (600 seconds). The hold record is written to PostgreSQL with status ACTIVE and expires_at = now() + interval '10 minutes'. Concurrently, transient keys (hold:{show_id}:{seat_id}) are populated in Redis with matching TTLs.

A background worker periodically scans for expired holds where expires_at < now() and status = 'ACTIVE'. Expired holds transition to EXPIRED, and the underlying show_seats are reverted from HELD back to AVAILABLE. Immediately following state transition, a WebSocket event (SEAT_STATUS_CHANGED) is broadcast to all active client sessions attached to that show room, updating visual seat maps in real time without client polling.

---

### 2. Concurrency Prevention and Atomic Locking
To guarantee that two customers attempting to hold or book the exact same seat simultaneously cannot both succeed, Ticketsmith enforces multi-layered concurrency protection using Redis Lua Scripting and Database Optimistic Locking.

#### Redis Lua Script Atomic Lock (execute_atomic_hold)
HTTP requests operate concurrently across multiple application workers. A naive check-then-set approach (SELECT status FROM show_seats WHERE id = seat_id) suffers from classic TOCTOU (Time-Of-Check to Time-Of-Use) race conditions under high traffic. To eliminate race conditions:

```lua
-- Atomic Multi-Seat Hold Lua Script
for i, key in ipairs(KEYS) do
    if redis.call('EXISTS', key) == 1 then
        return {0, key} -- Seat already locked by another customer
    end
end

for i, key in ipairs(KEYS) do
    redis.call('SET', key, ARGV[1], 'EX', ARGV[3]) -- Lock seat atomically
end
return {1, "OK"}
```

Because Redis executes Lua scripts single-threaded and atomically, concurrent requests targeting overlapping seat keys are serialized. The first request acquires the locks; subsequent requests fail instantly and return HTTP 409 CONFLICT ("Race condition detected! Seat was just grabbed by another customer").

#### Database Optimistic Concurrency Control
At the database layer, each show_seats row contains a version integer column. When updating seat status from HELD to BOOKED during payment confirmation:

```sql
UPDATE show_seats 
SET status = 'BOOKED', version = version + 1 
WHERE id IN (:seat_ids) AND version = :expected_version;
```
If another transaction mutated the seat version concurrently, the update returns zero affected rows, triggering a transaction rollback to prevent double booking.

---

### 3. Waitlist Auto-Assignment Queue
When an event or seat category (VIP, PREMIUM, STANDARD) sells out (AVAILABLE count = 0), customers can join a FIFO queue via POST /api/v1/waitlist/join. The system records a WaitlistEntry storing show_id, category_id, user_id, joined_at, and an incremental position index.

When an existing booking is cancelled via POST /api/v1/bookings/{id}/cancel (or a seat is released due to payment failure), the system executes an automated re-assignment routine:

1. Identifies the category of the freed seat (category_id).
2. Queries waitlist_entries for the lowest position where status = 'WAITING' for that specific show and category.
3. If a waiting customer exists:
   - Sets show_seat.status = 'OFFERED'.
   - Transitions WaitlistEntry.status = 'OFFERED'.
   - Creates a WaitlistOffer record with status ACTIVE and expires_at = now() + interval '15 minutes'.
   - Dispatches an automated email notification containing an exclusive claim link.
4. If no customer is waiting, show_seat.status reverts to AVAILABLE.

---

### 4. Time-Limited Offer Handling and Auto-Expiry
Offers assigned to waitlisted users carry a strict 15-minute time window (OFFER_TTL_SECONDS = 900).

- Offer Acceptance: The notified customer clicks the claim link (GET /waitlist?offer_id=...) and calls POST /api/v1/waitlist/offers/{offer_id}/accept. The system verifies Offer.status == 'ACTIVE' and expires_at > now(). Upon validation, WaitlistOffer.status transitions to ACCEPTED, WaitlistEntry.status transitions to FULFILLED, an active 10-minute hold is generated for the user, and the customer proceeds to checkout.
- Offer Expiry & Cascade: If the 15-minute TTL expires without acceptance, the offer transitions to EXPIRED. The background scheduler detects the expired offer, frees the seat, and automatically re-invokes the waitlist auto-assignment algorithm to offer the seat to the next customer in line (position + 1). This cycle repeats recursively until all available inventory is claimed or the waitlist queue is exhausted.

---

## License & Author
Built for production-grade ticket allocation standards by Ticketsmith Engineering. Open-source under the MIT License.
