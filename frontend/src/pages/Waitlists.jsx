import React, { useState, useEffect } from 'react';
import { Bookmark, Clock, CheckCircle2, AlertCircle, Sparkles } from 'lucide-react';
import { API_BASE } from '../config';

export default function Waitlists({ currentUser }) {
  const [entries, setEntries] = useState([]);
  const [offers, setOffers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchWaitlistData();
  }, []);

  const fetchWaitlistData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };

      const eRes = await fetch(`${API_BASE}/api/v1/waitlist/my-entries`, { headers });
      const eData = await eRes.json();
      setEntries(Array.isArray(eData) ? eData : []);

      const oRes = await fetch(`${API_BASE}/api/v1/waitlist/my-offers`, { headers });
      const oData = await oRes.json();
      setOffers(Array.isArray(oData) ? oData : []);

    } catch (e) {
      console.error(e);
      setEntries([]);
      setOffers([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptOffer = async (offerId) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/waitlist/offers/${offerId}/accept`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await res.json();
      if (!res.ok) {
        alert(data.detail || "Failed to accept offer");
        return;
      }
      alert(data.message);
      fetchWaitlistData();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '0 20px 60px 20px' }}>
      
      <div style={{ marginBottom: '28px' }}>
        <h2 style={{ fontSize: '1.8rem', fontWeight: 800 }}>Category Waitlists & Active Offers</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          When seats are cancelled, top waitlisted users receive 5-minute exclusive offers.
        </p>
      </div>

      {/* Active Time-Limited Offers Section */}
      {offers.length > 0 && (
        <div style={{ marginBottom: '36px' }}>
          <h3 style={{ fontSize: '1.2rem', color: 'var(--accent-pink)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={20} /> Exclusive Time-Limited Seat Offers ({offers.length})
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {offers.map(off => (
              <div key={off.id} className="glass-panel" style={{ padding: '20px', border: '1px solid var(--accent-pink)', background: 'rgba(236, 72, 153, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
                <div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#fff' }}>
                    Seat Offered: <span style={{ color: 'var(--accent-amber)' }}>{off.seat_label || 'Category Seat'}</span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
                    <Clock size={14} color="var(--accent-amber)" /> Expires: {new Date(off.expires_at).toLocaleTimeString()}
                  </div>
                </div>

                <button 
                  className="btn-primary" 
                  style={{ background: 'linear-gradient(135deg, #ec4899, #8b5cf6)' }}
                  onClick={() => handleAcceptOffer(off.id)}
                >
                  Accept Offer & Place Hold
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Waitlist Queue Entries */}
      <h3 style={{ fontSize: '1.2rem', marginBottom: '14px' }}>My Waitlist Positions</h3>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>Loading waitlist entries...</div>
      ) : entries.length === 0 ? (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
          No active waitlist queue entries.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {entries.map(ent => (
            <div key={ent.id} className="glass-panel" style={{ padding: '20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontSize: '1.05rem', fontWeight: 700 }}>
                  Category: {ent.category_name}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Joined: {new Date(ent.joined_at).toLocaleString()}
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Position in Line</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--accent-amber)' }}>#{ent.position}</div>
                </div>

                <span className="badge" style={{
                  background: ent.status === 'WAITING' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(236, 72, 153, 0.2)',
                  color: ent.status === 'WAITING' ? '#60a5fa' : '#f472b6',
                  border: `1px solid ${ent.status === 'WAITING' ? '#3b82f6' : '#ec4899'}`
                }}>
                  {ent.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

    </div>
  );
}
