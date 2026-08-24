-- PostgreSQL Database Schema for Ticket Booking Platform
-- Creates Enum Types, Tables, Foreign Keys, Indexes, and Initial Seed Data

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Create Custom ENUM Types
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('ADMIN', 'ORGANISER', 'CUSTOMER');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE event_type AS ENUM ('MOVIE', 'CONCERT', 'SPORTS', 'THEATRE');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE event_status AS ENUM ('DRAFT', 'PUBLISHED', 'CANCELLED', 'COMPLETED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE show_status AS ENUM ('SCHEDULED', 'ON_SALE', 'SOLD_OUT', 'CANCELLED', 'COMPLETED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE seat_status AS ENUM ('AVAILABLE', 'HELD', 'BOOKED', 'OFFERED', 'BLOCKED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE hold_status AS ENUM ('ACTIVE', 'RELEASED', 'EXPIRED', 'CONVERTED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE booking_status AS ENUM ('PENDING', 'CONFIRMED', 'CANCELLED', 'EXPIRED', 'FAILED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE payment_status AS ENUM ('PENDING', 'SUCCESS', 'FAILED', 'REFUNDED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE ticket_status AS ENUM ('ACTIVE', 'USED', 'CANCELLED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE waitlist_status AS ENUM ('WAITING', 'OFFERED', 'FULFILLED', 'EXPIRED', 'CANCELLED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE offer_status AS ENUM ('ACTIVE', 'ACCEPTED', 'EXPIRED', 'DECLINED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE notification_status AS ENUM ('PENDING', 'SENT', 'FAILED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE outbox_status AS ENUM ('PENDING', 'PROCESSED', 'FAILED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Create Tables

CREATE TABLE IF NOT EXISTS users (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name character varying NOT NULL,
  email character varying NOT NULL UNIQUE,
  password_hash text NOT NULL,
  role user_role NOT NULL DEFAULT 'CUSTOMER'::user_role,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT users_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS venues (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name character varying NOT NULL,
  address text,
  city character varying,
  state character varying,
  country character varying DEFAULT 'India'::character varying,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT venues_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS venue_sections (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  venue_id uuid NOT NULL,
  name character varying NOT NULL,
  section_type character varying,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT venue_sections_pkey PRIMARY KEY (id),
  CONSTRAINT venue_sections_venue_id_fkey FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS seat_categories (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  venue_id uuid NOT NULL,
  name character varying NOT NULL,
  description text,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT seat_categories_pkey PRIMARY KEY (id),
  CONSTRAINT seat_categories_venue_id_fkey FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS venue_seats (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  venue_id uuid NOT NULL,
  section_id uuid NOT NULL,
  category_id uuid NOT NULL,
  row_label character varying NOT NULL,
  seat_number integer NOT NULL,
  seat_label character varying NOT NULL,
  x_position integer NOT NULL,
  y_position integer NOT NULL,
  seat_type character varying DEFAULT 'REGULAR'::character varying,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT venue_seats_pkey PRIMARY KEY (id),
  CONSTRAINT venue_seats_venue_id_fkey FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE,
  CONSTRAINT venue_seats_section_id_fkey FOREIGN KEY (section_id) REFERENCES venue_sections(id) ON DELETE CASCADE,
  CONSTRAINT venue_seats_category_id_fkey FOREIGN KEY (category_id) REFERENCES seat_categories(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS events (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  organiser_id uuid NOT NULL,
  title character varying NOT NULL,
  description text,
  event_type event_type NOT NULL,
  poster_url text,
  duration_minutes integer CHECK (duration_minutes IS NULL OR duration_minutes > 0),
  status event_status NOT NULL DEFAULT 'DRAFT'::event_status,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT events_pkey PRIMARY KEY (id),
  CONSTRAINT events_organiser_id_fkey FOREIGN KEY (organiser_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS shows (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  event_id uuid NOT NULL,
  venue_id uuid NOT NULL,
  section_id uuid,
  start_time timestamp with time zone NOT NULL,
  end_time timestamp with time zone,
  status show_status NOT NULL DEFAULT 'SCHEDULED'::show_status,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT shows_pkey PRIMARY KEY (id),
  CONSTRAINT shows_event_id_fkey FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
  CONSTRAINT shows_venue_id_fkey FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE,
  CONSTRAINT shows_section_id_fkey FOREIGN KEY (section_id) REFERENCES venue_sections(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS show_prices (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  show_id uuid NOT NULL,
  category_id uuid NOT NULL,
  price numeric NOT NULL CHECK (price >= 0::numeric),
  currency character(3) NOT NULL DEFAULT 'INR',
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT show_prices_pkey PRIMARY KEY (id),
  CONSTRAINT show_prices_show_id_fkey FOREIGN KEY (show_id) REFERENCES shows(id) ON DELETE CASCADE,
  CONSTRAINT show_prices_category_id_fkey FOREIGN KEY (category_id) REFERENCES seat_categories(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS show_seats (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  show_id uuid NOT NULL,
  venue_seat_id uuid NOT NULL,
  category_id uuid NOT NULL,
  price numeric NOT NULL CHECK (price >= 0::numeric),
  status seat_status NOT NULL DEFAULT 'AVAILABLE'::seat_status,
  version bigint NOT NULL DEFAULT 0,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT show_seats_pkey PRIMARY KEY (id),
  CONSTRAINT show_seats_show_id_fkey FOREIGN KEY (show_id) REFERENCES shows(id) ON DELETE CASCADE,
  CONSTRAINT show_seats_venue_seat_id_fkey FOREIGN KEY (venue_seat_id) REFERENCES venue_seats(id) ON DELETE CASCADE,
  CONSTRAINT show_seats_category_id_fkey FOREIGN KEY (category_id) REFERENCES seat_categories(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS holds (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  show_id uuid NOT NULL,
  hold_token uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE,
  status hold_status NOT NULL DEFAULT 'ACTIVE'::hold_status,
  expires_at timestamp with time zone NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  released_at timestamp with time zone,
  CONSTRAINT holds_pkey PRIMARY KEY (id),
  CONSTRAINT holds_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT holds_show_id_fkey FOREIGN KEY (show_id) REFERENCES shows(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS hold_items (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  hold_id uuid NOT NULL,
  show_seat_id uuid NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT hold_items_pkey PRIMARY KEY (id),
  CONSTRAINT hold_items_hold_id_fkey FOREIGN KEY (hold_id) REFERENCES holds(id) ON DELETE CASCADE,
  CONSTRAINT hold_items_show_seat_id_fkey FOREIGN KEY (show_seat_id) REFERENCES show_seats(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS bookings (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  booking_reference character varying NOT NULL UNIQUE,
  user_id uuid NOT NULL,
  show_id uuid NOT NULL,
  hold_id uuid,
  status booking_status NOT NULL DEFAULT 'PENDING'::booking_status,
  subtotal numeric NOT NULL DEFAULT 0 CHECK (subtotal >= 0::numeric),
  tax numeric NOT NULL DEFAULT 0 CHECK (tax >= 0::numeric),
  discount numeric NOT NULL DEFAULT 0 CHECK (discount >= 0::numeric),
  total_amount numeric NOT NULL DEFAULT 0 CHECK (total_amount >= 0::numeric),
  currency character(3) NOT NULL DEFAULT 'INR',
  idempotency_key character varying UNIQUE,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  confirmed_at timestamp with time zone,
  cancelled_at timestamp with time zone,
  CONSTRAINT bookings_pkey PRIMARY KEY (id),
  CONSTRAINT bookings_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT bookings_show_id_fkey FOREIGN KEY (show_id) REFERENCES shows(id) ON DELETE CASCADE,
  CONSTRAINT bookings_hold_id_fkey FOREIGN KEY (hold_id) REFERENCES holds(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS booking_seats (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  booking_id uuid NOT NULL,
  show_seat_id uuid NOT NULL,
  price numeric NOT NULL CHECK (price >= 0::numeric),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT booking_seats_pkey PRIMARY KEY (id),
  CONSTRAINT booking_seats_booking_id_fkey FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
  CONSTRAINT booking_seats_show_seat_id_fkey FOREIGN KEY (show_seat_id) REFERENCES show_seats(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS payments (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  booking_id uuid NOT NULL,
  provider character varying NOT NULL,
  provider_payment_id character varying,
  amount numeric NOT NULL CHECK (amount >= 0::numeric),
  currency character(3) NOT NULL DEFAULT 'INR',
  status payment_status NOT NULL DEFAULT 'PENDING'::payment_status,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT payments_pkey PRIMARY KEY (id),
  CONSTRAINT payments_booking_id_fkey FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tickets (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  booking_id uuid NOT NULL,
  ticket_reference character varying NOT NULL UNIQUE,
  qr_payload text NOT NULL,
  qr_code_url text,
  status ticket_status NOT NULL DEFAULT 'ACTIVE'::ticket_status,
  issued_at timestamp with time zone NOT NULL DEFAULT now(),
  used_at timestamp with time zone,
  CONSTRAINT tickets_pkey PRIMARY KEY (id),
  CONSTRAINT tickets_booking_id_fkey FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS waitlist_entries (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  show_id uuid NOT NULL,
  category_id uuid NOT NULL,
  user_id uuid NOT NULL,
  position integer NOT NULL CHECK ("position" > 0),
  status waitlist_status NOT NULL DEFAULT 'WAITING'::waitlist_status,
  joined_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT waitlist_entries_pkey PRIMARY KEY (id),
  CONSTRAINT waitlist_entries_show_id_fkey FOREIGN KEY (show_id) REFERENCES shows(id) ON DELETE CASCADE,
  CONSTRAINT waitlist_entries_category_id_fkey FOREIGN KEY (category_id) REFERENCES seat_categories(id) ON DELETE CASCADE,
  CONSTRAINT waitlist_entries_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS waitlist_offers (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  waitlist_entry_id uuid NOT NULL,
  show_seat_id uuid NOT NULL,
  offer_token uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE,
  status offer_status NOT NULL DEFAULT 'ACTIVE'::offer_status,
  expires_at timestamp with time zone NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  accepted_at timestamp with time zone,
  CONSTRAINT waitlist_offers_pkey PRIMARY KEY (id),
  CONSTRAINT waitlist_offers_waitlist_entry_id_fkey FOREIGN KEY (waitlist_entry_id) REFERENCES waitlist_entries(id) ON DELETE CASCADE,
  CONSTRAINT waitlist_offers_show_seat_id_fkey FOREIGN KEY (show_seat_id) REFERENCES show_seats(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notifications (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  type character varying NOT NULL,
  channel character varying NOT NULL,
  reference_type character varying,
  reference_id uuid,
  status notification_status NOT NULL DEFAULT 'PENDING'::notification_status,
  error_message text,
  sent_at timestamp with time zone,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT notifications_pkey PRIMARY KEY (id),
  CONSTRAINT notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS outbox_events (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  aggregate_type character varying NOT NULL,
  aggregate_id uuid NOT NULL,
  event_type character varying NOT NULL,
  payload jsonb NOT NULL,
  status outbox_status NOT NULL DEFAULT 'PENDING'::outbox_status,
  retry_count integer NOT NULL DEFAULT 0 CHECK (retry_count >= 0),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  processed_at timestamp with time zone,
  last_error text,
  CONSTRAINT outbox_events_pkey PRIMARY KEY (id)
);

-- Indexes for fast query lookups
CREATE INDEX IF NOT EXISTS idx_show_seats_show_id ON show_seats(show_id);
CREATE INDEX IF NOT EXISTS idx_show_seats_status ON show_seats(status);
CREATE INDEX IF NOT EXISTS idx_holds_expires_at ON holds(expires_at) WHERE status = 'ACTIVE';
CREATE INDEX IF NOT EXISTS idx_waitlist_entries_show_cat ON waitlist_entries(show_id, category_id, position);
CREATE INDEX IF NOT EXISTS idx_waitlist_offers_expires ON waitlist_offers(expires_at) WHERE status = 'ACTIVE';
