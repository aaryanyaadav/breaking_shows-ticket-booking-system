import React, { useState, useEffect } from 'react';
import { Ticket as TicketIcon, Calendar, XCircle, QrCode, RefreshCw } from 'lucide-react';
import TicketModal from '../components/TicketModal';

export default function MyBookings({ currentUser }) {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTicket, setSelectedTicket] = useState(null);

  useEffect(() => {
    fetchBookings();
  }, []);

  const fetchBookings = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/bookings', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await res.json();
      setBookings(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleFetchTicket = async (bookingId) => {
    try {
      const res = await fetch('/api/v1/tickets', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const tickets = await res.json();
      const tkt = tickets.find(t => t.booking_id === bookingId);
      if (tkt) {
        setSelectedTicket(tkt);
      } else {
        alert("Ticket payload not found");
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleCancelBooking = async (bookingId) => {
    if (!confirm("Are you sure you want to cancel this booking? Held seats will be automatically offered to the waitlist queue!")) return;

    try {
      const res = await fetch(`/api/v1/bookings/${bookingId}/cancel`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await res.json();
      alert(data.message);
      fetchBookings();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '0 20px 60px 20px' }}>
      
      {selectedTicket && (
        <TicketModal ticket={selectedTicket} onClose={() => setSelectedTicket(null)} />
      )}

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '28px' }}>
        <div>
          <h2 style={{ fontSize: '1.8rem', fontWeight: 800 }}>My Booking History</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>View QR code tickets or process instant cancellations.</p>
        </div>
        <button onClick={fetchBookings} className="btn-secondary" style={{ padding: '8px 14px' }}>
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>Loading booking history...</div>
      ) : bookings.length === 0 ? (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
          No bookings found. Browse events to place a reservation!
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {bookings.map(b => (
            <div key={b.id} className="glass-panel" style={{ padding: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <div style={{ background: 'rgba(99, 102, 241, 0.15)', padding: '12px', borderRadius: '12px', border: '1px solid var(--primary)' }}>
                  <TicketIcon size={24} color="var(--accent-pink)" />
                </div>
                <div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 800 }}>Reference: {b.booking_reference}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Booked on: {new Date(b.created_at).toLocaleString()}
                  </div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--accent-amber)', marginTop: '4px' }}>
                    Total: ₹{b.total_amount.toFixed(2)}
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span className="badge" style={{
                  background: b.status === 'CONFIRMED' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                  color: b.status === 'CONFIRMED' ? '#34d399' : '#f87171',
                  border: `1px solid ${b.status === 'CONFIRMED' ? '#10b981' : '#ef4444'}`
                }}>
                  {b.status}
                </span>

                {b.status === 'CONFIRMED' && (
                  <>
                    <button className="btn-primary" style={{ padding: '6px 12px', fontSize: '0.8rem' }} onClick={() => handleFetchTicket(b.id)}>
                      <QrCode size={14} /> View QR Ticket
                    </button>
                    <button className="btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem', color: '#ef4444', borderColor: '#ef4444' }} onClick={() => handleCancelBooking(b.id)}>
                      <XCircle size={14} /> Cancel
                    </button>
                  </>
                )}
              </div>

            </div>
          ))}
        </div>
      )}

    </div>
  );
}
