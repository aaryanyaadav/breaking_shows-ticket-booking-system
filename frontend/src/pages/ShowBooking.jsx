import React, { useState, useEffect } from 'react';
import { ArrowLeft, Clock, MapPin, Sparkles, Shield, CheckCircle2, AlertCircle, ShoppingBag, CreditCard, Smartphone, Building2, Lock } from 'lucide-react';
import WaitingRoomModal from '../components/WaitingRoomModal';
import HoldTimer from '../components/HoldTimer';
import TicketModal from '../components/TicketModal';
import { API_BASE, WS_BASE } from '../config';

export default function ShowBooking({ event, currentUser, onBack, onOpenAuth }) {
  const [shows, setShows] = useState([]);
  const [selectedShow, setSelectedShow] = useState(null);
  const [seats, setSeats] = useState([]);
  const [selectedSeatIds, setSelectedSeatIds] = useState([]);
  const [loading, setLoading] = useState(true);

  // Waiting Room state
  const [inQueue, setInQueue] = useState(false);
  const [queueData, setQueueData] = useState(null);

  // Hold state
  const [activeHold, setActiveHold] = useState(null);

  // Checkout modal
  const [showCheckout, setShowCheckout] = useState(false);
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState('card');
  const [confirmedTicket, setConfirmedTicket] = useState(null);

  // Waitlist modal state
  const [waitlistCategory, setWaitlistCategory] = useState(null);
  const [waitlistSuccess, setWaitlistSuccess] = useState(null);

  useEffect(() => {
    fetchShows();
  }, [event.id]);

  useEffect(() => {
    if (selectedShow) {
      // Connect to WebSockets for live seat map updates
      const wsUrl = `${WS_BASE}/ws/shows/${selectedShow.id}`;
      const ws = new WebSocket(wsUrl);

      ws.onmessage = (evt) => {
        try {
          const data = JSON.parse(evt.data);
          if (data.event === 'SEAT_STATUS_CHANGED' && data.show_id === selectedShow.id) {
            // Refresh seat map dynamically
            fetchSeats(selectedShow.id);
          }
        } catch (e) {
          console.error("WebSocket message parse error:", e);
        }
      };

      return () => {
        ws.close();
      };
    }
  }, [selectedShow]);

  const fetchShows = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/shows?event_id=${event.id}`);
      const data = await res.json();
      if (Array.isArray(data)) {
        setShows(data);
        if (data.length > 0) {
          handleSelectShow(data[0]);
        } else {
          setLoading(false);
        }
      } else {
        setShows([]);
        setLoading(false);
      }
    } catch (e) {
      console.error(e);
      setShows([]);
      setLoading(false);
    }
  };

  const handleSelectShow = async (show) => {
    setSelectedShow(show);
    setSelectedSeatIds([]);
    setActiveHold(null);
    setLoading(true);

    if (!currentUser) {
      fetchSeats(show.id);
      return;
    }

    // Trigger Virtual Waiting Room queue join
    try {
      const res = await fetch(`${API_BASE}/api/v1/shows/${show.id}/queue/join`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token') || ''}` }
      });
      const qData = await res.json();
      if (qData.status === 'WAITING') {
        setQueueData(qData);
        setInQueue(true);
      } else {
        setInQueue(false);
        fetchSeats(show.id);
      }
    } catch (err) {
      console.error(err);
      fetchSeats(show.id);
    }
  };

  const fetchSeats = async (showId) => {
    try {
      const token = localStorage.getItem('token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      const res = await fetch(`${API_BASE}/api/v1/shows/${showId}/seats`, { headers });
      const data = await res.json();
      if (Array.isArray(data)) {
        setSeats(data);
      } else {
        setSeats([]);
      }
    } catch (e) {
      console.error(e);
      setSeats([]);
    } finally {
      setLoading(false);
    }
  };

  const toggleSeatSelection = (seat) => {
    if (seat.status !== 'AVAILABLE' && seat.status !== 'OFFERED') return;

    if (selectedSeatIds.includes(seat.id)) {
      setSelectedSeatIds(selectedSeatIds.filter(id => id !== seat.id));
    } else {
      if (selectedSeatIds.length >= 6) {
        alert("Maximum 6 seats per transaction");
        return;
      }
      setSelectedSeatIds([...selectedSeatIds, seat.id]);
    }
  };

  const handleAcquireAtomicHold = async () => {
    if (!currentUser) {
      if (onOpenAuth) onOpenAuth();
      return;
    }
    if (selectedSeatIds.length === 0) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/holds`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          show_id: selectedShow.id,
          show_seat_ids: selectedSeatIds,
          ttl_seconds: 600 // 10 minutes TTL
        })
      });

      const data = await res.json();

      if (!res.ok) {
        alert(data.detail || "Failed to hold seats");
        fetchSeats(selectedShow.id);
        setSelectedSeatIds([]);
        return;
      }

      setActiveHold(data);
      setShowCheckout(true);
      fetchSeats(selectedShow.id);
    } catch (err) {
      console.error(err);
      alert("Hold acquisition error");
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteCheckout = async () => {
    if (!activeHold) return;
    setPaymentLoading(true);

    const idempotencyKey = `IDEM-${Date.now()}-${activeHold.id.slice(0, 6)}`;

    try {
      // 1. Create Pending Booking with Idempotency-Key
      const bRes = await fetch(`${API_BASE}/api/v1/bookings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Idempotency-Key': idempotencyKey
        },
        body: JSON.stringify({
          show_id: selectedShow.id,
          hold_id: activeHold.id,
          hold_token: activeHold.hold_token
        })
      });
      const bData = await bRes.json();

      if (!bRes.ok) {
        alert(bData.detail || "Booking failed");
        setPaymentLoading(false);
        return;
      }

      // 2. Execute Mock Payment Webhook
      const pRes = await fetch(`${API_BASE}/api/v1/bookings/mock-pay`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          booking_id: bData.id,
          payment_method: 'CARD'
        })
      });

      const pData = await pRes.json();
      setShowCheckout(false);
      setActiveHold(null);
      setSelectedSeatIds([]);
      setConfirmedTicket({
        ticket_reference: pData.ticket_reference,
        booking_reference: pData.booking_reference,
        qr_code_url: pData.qr_code_url,
        status: 'CONFIRMED',
        seats: seats.filter(s => selectedSeatIds.includes(s.id)).map(s => s.seat_label)
      });
      fetchSeats(selectedShow.id);

    } catch (err) {
      console.error(err);
      alert("Payment processing failed");
    } finally {
      setPaymentLoading(false);
    }
  };

  const handleJoinCategoryWaitlist = async (categoryId) => {
    if (!currentUser) {
      onOpenAuth();
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/v1/waitlist/join`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          show_id: selectedShow.id,
          category_id: categoryId
        })
      });
      const data = await res.json();
      setWaitlistSuccess(data);
      setWaitlistCategory(null);
    } catch (e) {
      console.error(e);
    }
  };

  // Calculate pricing breakdown
  const selectedSeatsObj = seats.filter(s => selectedSeatIds.includes(s.id));
  const subtotal = selectedSeatsObj.reduce((acc, s) => acc + s.price, 0);
  const tax = Math.round(subtotal * 0.18 * 100) / 100;
  const totalAmount = Math.round((subtotal + tax) * 100) / 100;

  // Group seats by category for waitlist check
  const categoryGroups = {};
  const safeSeats = Array.isArray(seats) ? seats : [];
  safeSeats.forEach(s => {
    if (!categoryGroups[s.category_id]) {
      categoryGroups[s.category_id] = { id: s.category_id, name: s.category_name, total: 0, available: 0 };
    }
    categoryGroups[s.category_id].total += 1;
    if (s.status === 'AVAILABLE') categoryGroups[s.category_id].available += 1;
  });

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 20px 60px 20px' }}>

      {/* Waiting room modal */}
      {inQueue && (
        <WaitingRoomModal
          queueData={queueData}
          onEligible={() => {
            setInQueue(false);
            fetchSeats(selectedShow.id);
          }}
        />
      )}

      {/* Confirmed ticket modal */}
      {confirmedTicket && (
        <TicketModal ticket={confirmedTicket} onClose={() => setConfirmedTicket(null)} />
      )}

      {/* Floating Hold Timer */}
      {activeHold && (
        <HoldTimer
          expiresAt={activeHold.expires_at}
          onExpired={() => {
            alert("Hold time expired! Seats have been auto-released.");
            setActiveHold(null);
            setShowCheckout(false);
            fetchSeats(selectedShow.id);
          }}
        />
      )}

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
        <button onClick={onBack} className="btn-secondary" style={{ padding: '8px 12px' }}>
          <ArrowLeft size={18} /> Back to Events
        </button>
        <div>
          <h2 style={{ fontSize: '1.8rem', fontWeight: 800 }}>{event.title}</h2>
        </div>
      </div>

      {/* Guest Sign In Invitation Banner */}
      {!currentUser && (
        <div className="glass-panel" style={{ padding: '14px 20px', marginBottom: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', border: '1px solid rgba(99, 102, 241, 0.4)', background: 'rgba(99, 102, 241, 0.1)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Sparkles color="var(--primary)" size={20} />
            <span style={{ fontSize: '0.9rem', color: '#fff' }}>Browsing as Guest. Sign in to place seat holds, receive QR code tickets, and manage waitlists.</span>
          </div>
          <button className="btn-primary" style={{ padding: '8px 18px', fontSize: '0.85rem' }} onClick={onOpenAuth}>
            Sign In Now
          </button>
        </div>
      )}

      {/* Showtimes Selector */}
      <div className="glass-panel" style={{ padding: '16px 24px', marginBottom: '32px', display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
        <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent-cyan)', textTransform: 'uppercase', letterSpacing: '1px' }}>
          Select Showtime:
        </div>
        {shows.length === 0 ? (
          <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No showtimes currently scheduled for this event.</span>
        ) : (
          shows.map(s => {
            const isSel = selectedShow?.id === s.id;
            const timeStr = new Date(s.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            const dateStr = new Date(s.start_time).toLocaleDateString([], { month: 'short', day: 'numeric' });
            return (
              <button
                key={s.id}
                onClick={() => handleSelectShow(s)}
                className="btn-secondary"
                style={{
                  background: isSel ? 'linear-gradient(135deg, var(--primary), var(--accent-pink))' : 'rgba(255,255,255,0.05)',
                  borderColor: isSel ? 'transparent' : 'rgba(255,255,255,0.1)',
                  color: '#fff'
                }}
              >
                <Clock size={14} /> {dateStr} at {timeStr}
              </button>
            );
          })
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '28px' }}>

        {/* Main Seat Map Grid */}
        <div className="glass-panel" style={{ padding: '32px 24px', position: 'relative' }}>

          {/* Screen Banner */}
          <div className="screen-arc">AUDITORIUM SCREEN 1</div>

          {/* Seat Status Legend */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: '18px', flexWrap: 'wrap', marginBottom: '36px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div className="seat-button seat-available-vip" style={{ width: '20px', height: '20px' }} /> VIP (₹1500)
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div className="seat-button seat-available-premium" style={{ width: '20px', height: '20px' }} /> Premium (₹850)
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div className="seat-button seat-available-standard" style={{ width: '20px', height: '20px' }} /> Standard (₹450)
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div className="seat-button seat-selected" style={{ width: '20px', height: '20px' }} /> Selected
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div className="seat-button seat-held" style={{ width: '20px', height: '20px' }} /> Held (TTL)
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div className="seat-button seat-booked" style={{ width: '20px', height: '20px' }} /> Booked
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div className="seat-button seat-offered" style={{ width: '20px', height: '20px' }} /> Offered to You
            </div>
          </div>

          {/* Interactive Seat Grid Layout */}
          {loading ? (
            <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>Rendering live seat map...</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', alignItems: 'center' }}>
              {/* Group by Row Label */}
              {['A', 'B', 'C', 'D'].map(rowChr => {
                const rowSeats = seats.filter(s => s.row_label === rowChr);
                if (rowSeats.length === 0) return null;

                return (
                  <div key={rowChr} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{ width: '24px', fontWeight: 800, color: 'var(--accent-cyan)', textAlign: 'center' }}>
                      {rowChr}
                    </div>
                    <div style={{ display: 'flex', gap: '10px' }}>
                      {rowSeats.map(st => {
                        const isSel = selectedSeatIds.includes(st.id);

                        let seatClass = `seat-available-${st.category_name.toLowerCase()}`;
                        if (isSel) seatClass = 'seat-selected';
                        else if (st.status === 'HELD') seatClass = 'seat-held';
                        else if (st.status === 'BOOKED') seatClass = 'seat-booked';
                        else if (st.status === 'OFFERED') seatClass = 'seat-offered';

                        return (
                          <button
                            key={st.id}
                            className={`seat-button ${seatClass}`}
                            onClick={() => toggleSeatSelection(st)}
                            disabled={st.status === 'BOOKED' || st.status === 'HELD'}
                            title={`${st.seat_label} - ${st.category_name} (₹${st.price}) - Status: ${st.status}`}
                          >
                            {st.seat_number}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Waitlist Category Sold Out Notice */}
          <div style={{ marginTop: '40px', paddingTop: '20px', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
            <h4 style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '12px' }}>Category Waitlists (Auto-Assignment on Cancellation):</h4>
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              {Object.values(categoryGroups).map(cat => (
                <div key={cat.id} style={{ background: 'rgba(255,255,255,0.03)', padding: '10px 14px', borderRadius: '10px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div>
                    <span style={{ fontWeight: 700 }}>{cat.name}</span>: {cat.available} / {cat.total} Available
                  </div>
                  {cat.available === 0 && (
                    <button
                      onClick={() => handleJoinCategoryWaitlist(cat.id)}
                      className="btn-secondary"
                      style={{ padding: '4px 10px', fontSize: '0.7rem', color: 'var(--accent-pink)', borderColor: 'var(--accent-pink)' }}
                    >
                      Join Waitlist
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Sidebar Summary Drawer */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

          <div className="glass-panel" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShoppingBag size={18} color="var(--primary)" /> Booking Summary
            </h3>

            {selectedSeatIds.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Select seats from the grid to place a hold.</p>
            ) : (
              <div>
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '6px' }}>Selected Seats:</div>
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                    {selectedSeatsObj.map(s => (
                      <span key={s.id} className="badge" style={{ background: 'rgba(245, 158, 11, 0.2)', color: '#fbbf24', border: '1px solid #f59e0b' }}>
                        {s.seat_label} (₹{s.price})
                      </span>
                    ))}
                  </div>
                </div>

                <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '14px', marginBottom: '20px', fontSize: '0.85rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Subtotal:</span>
                    <span>₹{subtotal.toFixed(2)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ color: 'var(--text-muted)' }}>GST Tax (18%):</span>
                    <span>₹{tax.toFixed(2)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 800, fontSize: '1.1rem', color: 'var(--accent-amber)', marginTop: '8px' }}>
                    <span>Total Amount:</span>
                    <span>₹{totalAmount.toFixed(2)}</span>
                  </div>
                </div>

                {currentUser?.role === 'ORGANISER' || currentUser?.role === 'ADMIN' ? (
                  <button 
                    className="btn-secondary" 
                    disabled
                    style={{ width: '100%', justifyContent: 'center', opacity: 0.7, cursor: 'not-allowed' }}
                  >
                    Organiser Account (Management Mode)
                  </button>
                ) : !currentUser ? (
                  <button
                    className="btn-primary"
                    style={{ width: '100%', justifyContent: 'center' }}
                    onClick={onOpenAuth}
                  >
                    Sign In to Reserve & Book Seats
                  </button>
                ) : !activeHold ? (
                  <button
                    className="btn-primary"
                    style={{ width: '100%', justifyContent: 'center' }}
                    onClick={handleAcquireAtomicHold}
                  >
                    Continue to Payment
                  </button>
                ) : (
                  <button
                    className="btn-primary"
                    style={{ width: '100%', justifyContent: 'center', background: 'linear-gradient(135deg, #10b981, #059669)' }}
                    onClick={() => setShowCheckout(true)}
                  >
                    Proceed to Payment
                  </button>
                )}
              </div>
            )}

          </div>

        </div>

      </div>

      {/* Checkout Modal */}
      {showCheckout && (
        <div className="modal-backdrop">
          <div className="glass-panel" style={{ maxWidth: '480px', width: '100%', padding: '28px' }}>
            <h3 style={{ fontSize: '1.4rem', marginBottom: '4px', fontWeight: 800 }}>Payment Checkout</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '20px' }}>
              Select your preferred payment method to complete booking.
            </p>

            {/* Order Details Summary */}
            <div style={{ background: 'rgba(255,255,255,0.04)', padding: '16px', borderRadius: '12px', marginBottom: '20px', fontSize: '0.85rem', border: '1px solid rgba(255,255,255,0.08)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Event:</span>
                <span style={{ fontWeight: 700, color: '#fff' }}>{event.title}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Selected Seats:</span>
                <span style={{ fontWeight: 700, color: 'var(--accent-amber)' }}>
                  {selectedSeatsObj.map(s => s.seat_label).join(', ')} ({selectedSeatsObj.length} Seats)
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: '8px', borderTop: '1px solid rgba(255,255,255,0.08)', fontWeight: 800, fontSize: '1rem' }}>
                <span>Total Amount Payable:</span>
                <span style={{ color: 'var(--accent-amber)' }}>₹{totalAmount.toFixed(2)}</span>
              </div>
            </div>

            {/* Payment Method Selector */}
            <div style={{ marginBottom: '24px' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '10px', fontWeight: 600 }}>Payment Method:</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {[
                  { id: 'card', label: 'Credit / Debit Card', desc: 'Visa, Mastercard, RuPay', icon: CreditCard },
                  { id: 'upi', label: 'UPI / QR Code', desc: 'GPay, PhonePe, Paytm', icon: Smartphone },
                  { id: 'netbanking', label: 'Net Banking', desc: 'HDFC, ICICI, SBI, Axis', icon: Building2 }
                ].map(pm => {
                  const Icon = pm.icon;
                  const isSel = paymentMethod === pm.id;
                  return (
                    <div
                      key={pm.id}
                      onClick={() => setPaymentMethod(pm.id)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '12px 14px',
                        borderRadius: '10px',
                        background: isSel ? 'rgba(99, 102, 241, 0.15)' : 'rgba(255,255,255,0.02)',
                        border: isSel ? '1px solid var(--primary)' : '1px solid rgba(255,255,255,0.1)',
                        cursor: 'pointer'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <Icon size={18} color={isSel ? 'var(--primary)' : 'var(--text-muted)'} />
                        <div>
                          <div style={{ fontSize: '0.85rem', fontWeight: 700, color: isSel ? '#fff' : 'var(--text-muted)' }}>{pm.label}</div>
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{pm.desc}</div>
                        </div>
                      </div>
                      <div style={{
                        width: '16px',
                        height: '16px',
                        borderRadius: '50%',
                        border: isSel ? '5px solid var(--primary)' : '2px solid rgba(255,255,255,0.3)'
                      }} />
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Security Assurance Badge */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '20px' }}>
              <Lock size={12} color="#10b981" /> 256-Bit SSL Encrypted & Secure Payment
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', gap: '12px' }}>
              <button className="btn-secondary" style={{ flex: 1 }} onClick={() => setShowCheckout(false)}>
                Cancel
              </button>
              <button
                className="btn-primary"
                style={{ flex: 1.5, justifyContent: 'center', background: 'linear-gradient(135deg, #6366f1, #ec4899)' }}
                onClick={handleExecuteCheckout}
                disabled={paymentLoading}
              >
                <CreditCard size={16} /> {paymentLoading ? 'Processing Payment...' : `Pay ₹${totalAmount.toFixed(2)}`}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Waitlist Success Modal */}
      {waitlistSuccess && (
        <div className="modal-backdrop">
          <div className="glass-panel" style={{ maxWidth: '400px', width: '100%', padding: '28px', textAlign: 'center' }}>
            <CheckCircle2 size={40} color="#10b981" style={{ margin: '0 auto 12px auto' }} />
            <h3>Joined Waitlist!</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: '12px 0 20px 0' }}>
              You are position <strong>#{waitlistSuccess.position}</strong> in line for this category. If a customer cancels their booking, you will receive a 5-minute time-limited offer alert!
            </p>
            <button className="btn-primary" style={{ width: '100%', justifyContent: 'center' }} onClick={() => setWaitlistSuccess(null)}>
              Got it
            </button>
          </div>
        </div>
      )}

    </div>
  );
}
