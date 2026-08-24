import React, { useState, useEffect } from 'react';
import { Wallet, Ticket, Calendar, Building2, Plus, Sparkles, TrendingUp, Users, Film, ChevronDown, ChevronUp, ShieldCheck, Eye, LayoutGrid, CheckCircle2, Trash2, Mail, UserCheck } from 'lucide-react';

export default function Dashboard({ currentUser }) {
  const [analytics, setAnalytics] = useState(null);
  const [venues, setVenues] = useState([]);
  const [events, setEvents] = useState([]);
  const [organisersList, setOrganisersList] = useState([]);
  const [selectedOrganiser, setSelectedOrganiser] = useState(null);
  
  // Detailed Organiser Analytics
  const [organiserData, setOrganiserData] = useState(null);
  const [expandedEventId, setExpandedEventId] = useState(null);
  const [loading, setLoading] = useState(true);

  // New Event Form State (Organiser Only)
  const [eventForm, setEventForm] = useState({
    title: '',
    description: '',
    event_type: 'MOVIE',
    duration_minutes: '120',
    poster_url: 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=800&q=80'
  });

  // New Show Form state (Organiser Only)
  const [showForm, setShowForm] = useState({
    event_id: '',
    venue_id: '',
    start_time: '',
    price_vip: '1500',
    price_prem: '850',
    price_std: '450'
  });

  // Custom Venue Form state (Admin Only)
  const [venueName, setVenueName] = useState('');
  const [venueCity, setVenueCity] = useState('');
  const [venueRows, setVenueRows] = useState(4);
  const [venueSeatsPerRow, setVenueSeatsPerRow] = useState(8);
  const [venueVipRows, setVenueVipRows] = useState(1);
  const [venuePremiumRows, setVenuePremiumRows] = useState(1);

  const isAdmin = currentUser?.role === 'ADMIN';

  useEffect(() => {
    fetchDashboardData();
  }, [currentUser]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };

      // Fetch Global analytics
      const aRes = await fetch('/api/v1/admin/analytics', { headers });
      if (aRes.ok) {
        const aData = await aRes.json();
        setAnalytics(aData);
      }

      // Fetch venues
      const vRes = await fetch('/api/v1/venues', { headers });
      if (vRes.ok) {
        const vData = await vRes.json();
        if (Array.isArray(vData)) setVenues(vData);
      }

      // Fetch events
      const eRes = await fetch('/api/v1/events', { headers });
      if (eRes.ok) {
        const eData = await eRes.json();
        if (Array.isArray(eData)) {
          setEvents(eData);
          if (eData.length > 0 && !showForm.event_id) {
            setShowForm(f => ({ ...f, event_id: eData[0].id }));
          }
        }
      }

      // Fetch Organiser Analytics
      const orgRes = await fetch('/api/v1/events/organiser-analytics', { headers });
      if (orgRes.ok) {
        const orgData = await orgRes.json();
        setOrganiserData(orgData);
      }

      // Fetch organisers with event listings for Admin
      if (isAdmin) {
        const oRes = await fetch('/api/v1/admin/organisers', { headers });
        if (oRes.ok) {
          const oData = await oRes.json();
          if (Array.isArray(oData)) setOrganisersList(oData);
        }
      }
    } catch (e) {
      console.error("Dashboard fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateEvent = async (e) => {
    e.preventDefault();
    if (!eventForm.title) {
      alert("Please enter event title");
      return;
    }

    try {
      const res = await fetch('/api/v1/events', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          title: eventForm.title,
          description: eventForm.description,
          event_type: eventForm.event_type,
          poster_url: eventForm.poster_url,
          duration_minutes: parseInt(eventForm.duration_minutes) || 120
        })
      });

      if (res.ok) {
        alert("Event Created Successfully!");
        setEventForm({
          title: '',
          description: '',
          event_type: 'MOVIE',
          duration_minutes: '120',
          poster_url: 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=800&q=80'
        });
        fetchDashboardData();
      } else {
        const err = await res.json();
        alert(err.detail || "Only Organisers can create events.");
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteEvent = async (eventId, title) => {
    if (!window.confirm(`Are you sure you want to delete "${title}"? All associated showtimes, seat holds, and customer booking data will be deleted.`)) {
      return;
    }

    try {
      const res = await fetch(`/api/v1/events/${eventId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (res.ok) {
        alert(`Event "${title}" deleted successfully.`);
        fetchDashboardData();
      } else {
        const err = await res.json();
        alert(err.detail || "Failed to delete event.");
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateVenue = async (e) => {
    e.preventDefault();
    if (!venueName || !venueCity) {
      alert("Please enter venue name and city");
      return;
    }

    const rows = parseInt(venueRows) || 4;
    const seatsPerRow = parseInt(venueSeatsPerRow) || 8;
    const vipRows = Math.min(parseInt(venueVipRows) || 0, rows);
    const premRows = Math.min(parseInt(venuePremiumRows) || 0, rows - vipRows);

    try {
      const res = await fetch('/api/v1/venues', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          name: venueName,
          address: 'Main Street Auditorium',
          city: venueCity,
          state: 'State',
          rows: rows,
          seats_per_row: seatsPerRow,
          vip_rows: vipRows,
          premium_rows: premRows
        })
      });
      if (res.ok) {
        const total = rows * seatsPerRow;
        alert(`Venue Screen & Custom ${total}-Seat Layout Grid Created!`);
        setVenueName('');
        setVenueCity('');
        fetchDashboardData();
      } else {
        const err = await res.json();
        alert(err.detail || "Only Admin can create venues.");
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateShow = async (e) => {
    e.preventDefault();
    const selVenue = venues.find(v => v.id === showForm.venue_id);
    if (!showForm.event_id || !showForm.venue_id) {
      alert("Select an Event and a Venue Screen");
      return;
    }
    if (!selVenue || !selVenue.categories || selVenue.categories.length === 0) {
      alert("Select a valid venue with seat categories");
      return;
    }

    const pricesMap = {};
    selVenue.categories.forEach(cat => {
      if (cat.name === 'VIP') pricesMap[cat.id] = parseFloat(showForm.price_vip);
      else if (cat.name === 'PREMIUM') pricesMap[cat.id] = parseFloat(showForm.price_prem);
      else pricesMap[cat.id] = parseFloat(showForm.price_std);
    });

    try {
      const res = await fetch('/api/v1/shows', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          event_id: showForm.event_id,
          venue_id: showForm.venue_id,
          start_time: showForm.start_time || new Date(Date.now() + 3600000 * 4).toISOString(),
          prices: pricesMap
        })
      });
      if (res.ok) {
        alert("Show Showtime & Seat Inventory Published!");
        fetchDashboardData();
      } else {
        const err = await res.json();
        alert(err.detail || "Failed to schedule show.");
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Helper computations for Admin Seat Layout Preview
  const totalRowsNum = parseInt(venueRows) || 4;
  const seatsPerRowNum = parseInt(venueSeatsPerRow) || 8;
  const vipRowsNum = Math.min(parseInt(venueVipRows) || 0, totalRowsNum);
  const premRowsNum = Math.min(parseInt(venuePremiumRows) || 0, totalRowsNum - vipRowsNum);
  const stdRowsNum = Math.max(0, totalRowsNum - vipRowsNum - premRowsNum);
  
  const totalCapacity = totalRowsNum * seatsPerRowNum;
  const vipCapacity = vipRowsNum * seatsPerRowNum;
  const premCapacity = premRowsNum * seatsPerRowNum;
  const stdCapacity = stdRowsNum * seatsPerRowNum;

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '0 20px 60px 20px' }}>
      
      {/* Role Header */}
      <div style={{ marginBottom: '28px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '1.8rem', fontWeight: 800 }}>
            {isAdmin ? 'Admin Console & Governance' : 'Organiser Portal & Financial Control'}
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            {isAdmin 
              ? 'Configure venue screen layouts, seat categories (VIP, Premium, Standard), global metrics & organisers.'
              : 'Full financial control: track earnings, customer booking details, seat numbers, publish events & schedule showtimes.'}
          </p>
        </div>
        <div style={{ background: isAdmin ? 'rgba(236, 72, 153, 0.15)' : 'rgba(99, 102, 241, 0.15)', padding: '8px 14px', borderRadius: '20px', border: `1px solid ${isAdmin ? 'var(--accent-pink)' : 'var(--primary)'}`, fontSize: '0.8rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px' }}>
          <ShieldCheck size={16} color={isAdmin ? 'var(--accent-pink)' : 'var(--primary)'} />
          {isAdmin ? 'ADMIN ROLE' : 'ORGANISER ROLE'}
        </div>
      </div>

      {/* Analytics Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px', marginBottom: '40px' }}>
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '8px' }}>
            <span>{isAdmin ? 'Global Platform Revenue' : 'My Total Earnings'}</span>
            <Wallet size={18} color="var(--accent-amber)" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-amber)' }}>
            ₹{(isAdmin ? (analytics?.total_revenue || 0) : (organiserData?.total_earnings || 0)).toFixed(2)}
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '8px' }}>
            <span>{isAdmin ? 'Total Registered Organisers' : 'Total Confirmed Bookings'}</span>
            {isAdmin ? <Users size={18} color="#93c5fd" /> : <Ticket size={18} color="#10b981" />}
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: isAdmin ? '#93c5fd' : '#34d399' }}>
            {isAdmin ? organisersList.length : (organiserData?.total_bookings || 0)}
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '8px' }}>
            <span>{isAdmin ? 'Venues Created' : 'My Listed Events'}</span>
            {isAdmin ? <Building2 size={18} color="var(--accent-cyan)" /> : <Calendar size={18} color="var(--primary)" />}
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#93c5fd' }}>
            {isAdmin ? venues.length : (organiserData?.total_events || 0)}
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '8px' }}>
            <span>{isAdmin ? 'Total Published Shows' : 'Tickets Sold'}</span>
            <TrendingUp size={18} color="var(--accent-pink)" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f472b6' }}>
            {isAdmin ? (analytics?.total_shows || 0) : (organiserData?.total_tickets_sold || 0)}
          </div>
        </div>
      </div>

      {/* ADMIN VIEW */}
      {isAdmin ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
          
          {/* Customizable Venue & Seat Layout Builder (Admin Only) */}
          <div className="glass-panel" style={{ padding: '28px' }}>
            <h3 style={{ fontSize: '1.3rem', marginBottom: '6px', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <LayoutGrid size={20} color="var(--accent-cyan)" /> Create & Customize Screen Venue Layout
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '24px' }}>
              Define venue screen details, total rows, seats per row, and assign VIP / Premium / Standard category tiers.
            </p>

            <form onSubmit={handleCreateVenue} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              
              {/* Basic Details */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px', fontWeight: 600 }}>Venue Screen Name</label>
                  <input 
                    type="text" 
                    required
                    placeholder="e.g. PVR Director's Cut Screen 1" 
                    value={venueName}
                    onChange={e => setVenueName(e.target.value)}
                    style={{ width: '100%', padding: '12px', borderRadius: '10px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', fontSize: '0.9rem' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px', fontWeight: 600 }}>City / Location</label>
                  <input 
                    type="text" 
                    required
                    placeholder="e.g. Mumbai / Delhi / Bangalore" 
                    value={venueCity}
                    onChange={e => setVenueCity(e.target.value)}
                    style={{ width: '100%', padding: '12px', borderRadius: '10px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', fontSize: '0.9rem' }}
                  />
                </div>
              </div>

              {/* Custom Grid Controls */}
              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '18px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.08)' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '14px', color: '#fff' }}>
                  ⚙️ Seat Grid & Category Tier Allocator:
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '14px' }}>
                  <div>
                    <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Total Rows (A, B, C...)</label>
                    <input 
                      type="number" 
                      min="1"
                      max="10"
                      value={venueRows}
                      onChange={e => setVenueRows(e.target.value)}
                      style={{ width: '100%', padding: '10px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(99,102,241,0.4)', color: '#fff', fontWeight: 700 }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Seats Per Row</label>
                    <input 
                      type="number" 
                      min="2"
                      max="12"
                      value={venueSeatsPerRow}
                      onChange={e => setVenueSeatsPerRow(e.target.value)}
                      style={{ width: '100%', padding: '10px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(99,102,241,0.4)', color: '#fff', fontWeight: 700 }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '0.7rem', color: 'var(--accent-amber)', display: 'block', marginBottom: '4px' }}>VIP Rows (Recliner Front)</label>
                    <input 
                      type="number" 
                      min="0"
                      max={totalRowsNum}
                      value={venueVipRows}
                      onChange={e => setVenueVipRows(e.target.value)}
                      style={{ width: '100%', padding: '10px', borderRadius: '8px', background: 'rgba(245, 158, 11, 0.1)', border: '1px solid #f59e0b', color: '#fbbf24', fontWeight: 700 }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '0.7rem', color: 'var(--primary)', display: 'block', marginBottom: '4px' }}>Premium Rows (Prime)</label>
                    <input 
                      type="number" 
                      min="0"
                      max={Math.max(0, totalRowsNum - vipRowsNum)}
                      value={venuePremiumRows}
                      onChange={e => setVenuePremiumRows(e.target.value)}
                      style={{ width: '100%', padding: '10px', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.1)', border: '1px solid var(--primary)', color: '#93c5fd', fontWeight: 700 }}
                    />
                  </div>
                </div>

                {/* Seat Capacity Live Summary Breakdown */}
                <div style={{ marginTop: '16px', paddingTop: '14px', borderTop: '1px solid rgba(255,255,255,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Calculated Capacity: <strong style={{ color: '#fff', fontSize: '1rem' }}>{totalCapacity} Seats</strong> ({totalRowsNum} Rows × {seatsPerRowNum} Seats)
                  </div>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <span className="badge" style={{ background: 'rgba(245, 158, 11, 0.2)', color: '#fbbf24', border: '1px solid #f59e0b' }}>
                      VIP: {vipCapacity} Seats ({vipRowsNum} {vipRowsNum === 1 ? 'Row' : 'Rows'})
                    </span>
                    <span className="badge" style={{ background: 'rgba(99, 102, 241, 0.2)', color: '#93c5fd', border: '1px solid var(--primary)' }}>
                      Premium: {premCapacity} Seats ({premRowsNum} {premRowsNum === 1 ? 'Row' : 'Rows'})
                    </span>
                    <span className="badge" style={{ background: 'rgba(255, 255, 255, 0.08)', color: '#fff', border: '1px solid rgba(255,255,255,0.2)' }}>
                      Standard: {stdCapacity} Seats ({stdRowsNum} {stdRowsNum === 1 ? 'Row' : 'Rows'})
                    </span>
                  </div>
                </div>

              </div>

              <button className="btn-primary" type="submit" style={{ justifyContent: 'center', padding: '14px' }}>
                <Plus size={18} /> Build & Save Custom Screen Layout Grid
              </button>
            </form>
          </div>

          {/* Existing Venues List */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Building2 size={18} color="var(--accent-cyan)" /> Configured Screen Venues ({venues.length})
            </h3>
            {venues.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No venues built yet.</p>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '14px' }}>
                {venues.map(v => (
                  <div key={v.id} style={{ background: 'rgba(255,255,255,0.03)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.08)' }}>
                    <div style={{ fontWeight: 700, fontSize: '1rem', marginBottom: '4px' }}>{v.name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '10px' }}>{v.city}, {v.state}</div>
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                      {v.categories?.map(c => (
                        <span key={c.id} className="badge" style={{ fontSize: '0.65rem', background: 'rgba(255,255,255,0.05)', color: 'var(--text-muted)' }}>
                          {c.name}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Manage Organisers & View Listings (Admin Only) */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Users size={18} color="var(--accent-pink)" /> Registered Organisers & Event Listings Audit
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '20px' }}>
              View how many organisers are registered and inspect their listed movies & events.
            </p>

            {organisersList.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No registered organisers found.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {organisersList.map(org => {
                  const isExpanded = selectedOrganiser === org.id;
                  return (
                    <div 
                      key={org.id} 
                      style={{ 
                        background: 'rgba(255,255,255,0.03)', 
                        border: '1px solid rgba(255,255,255,0.08)',
                        borderRadius: '14px', 
                        padding: '16px',
                        overflow: 'hidden'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <h4 style={{ fontSize: '1.05rem', fontWeight: 700 }}>{org.name}</h4>
                            <span className="badge" style={{ background: 'rgba(99,102,241,0.2)', color: '#93c5fd' }}>
                              ORGANISER
                            </span>
                          </div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                            {org.email} • Registered {new Date(org.created_at).toLocaleDateString()}
                          </div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                          <div style={{ textAlign: 'right' }}>
                            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--accent-amber)' }}>{org.events_count}</div>
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Listings</div>
                          </div>

                          <button 
                            className="btn-secondary" 
                            style={{ padding: '6px 12px', fontSize: '0.75rem' }}
                            onClick={() => setSelectedOrganiser(isExpanded ? null : org.id)}
                          >
                            <Eye size={14} /> {isExpanded ? 'Hide Listings' : 'View Listings'}
                            {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                          </button>
                        </div>
                      </div>

                      {/* Organiser's Event Listings Details */}
                      {isExpanded && (
                        <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                          <h5 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '10px' }}>
                            Event Listings by {org.name}:
                          </h5>
                          {org.events.length === 0 ? (
                            <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', italic: 'true' }}>No events listed by this organiser yet.</p>
                          ) : (
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '12px' }}>
                              {org.events.map(ev => (
                                <div key={ev.id} style={{ background: 'rgba(18, 24, 38, 0.8)', padding: '12px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.1)' }}>
                                  <div style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: '4px' }}>{ev.title}</div>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                    <span>Type: {ev.event_type}</span>
                                    <span>{ev.duration_minutes} Mins</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

        </div>
      ) : (
        /* ORGANISER VIEW */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '28px' }}>
            
            {/* Create Event Form (Organiser Only) */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '1.2rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Film size={18} color="var(--primary)" /> Add New Movie / Event Listing
              </h3>
              <form onSubmit={handleCreateEvent} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Event / Movie Title</label>
                  <input 
                    type="text" 
                    required
                    placeholder="e.g. Interstellar IMAX Special" 
                    value={eventForm.title}
                    onChange={e => setEventForm({ ...eventForm, title: e.target.value })}
                    style={{ width: '100%', padding: '10px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff' }}
                  />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>
                    <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Category</label>
                    <select 
                      value={eventForm.event_type}
                      onChange={e => setEventForm({ ...eventForm, event_type: e.target.value })}
                      style={{ width: '100%', padding: '10px', borderRadius: '8px', background: '#121826', border: '1px solid rgba(255,255,255,0.15)', color: '#fff' }}
                    >
                      <option value="MOVIE">Movie</option>
                      <option value="CONCERT">Concert</option>
                      <option value="SPORTS">Sports</option>
                      <option value="THEATRE">Theatre</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Duration (Mins)</label>
                    <input 
                      type="number" 
                      value={eventForm.duration_minutes}
                      onChange={e => setEventForm({ ...eventForm, duration_minutes: e.target.value })}
                      style={{ width: '100%', padding: '10px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff' }}
                    />
                  </div>
                </div>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Description</label>
                  <input 
                    type="text" 
                    placeholder="Short description of show"
                    value={eventForm.description}
                    onChange={e => setEventForm({ ...eventForm, description: e.target.value })}
                    style={{ width: '100%', padding: '10px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff' }}
                  />
                </div>
                <button className="btn-primary" type="submit" style={{ justifyContent: 'center', marginTop: '8px' }}>
                  <Plus size={16} /> Publish Event Listing
                </button>
              </form>
            </div>

            {/* Schedule Show & Set Pricing Form (Organiser Only) */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '1.2rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Calendar size={18} color="var(--accent-pink)" /> Schedule Show & Set Pricing
              </h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginBottom: '14px' }}>
                Pick an existing venue screen and set per-category ticket prices.
              </p>
              <form onSubmit={handleCreateShow} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Select Event</label>
                  <select 
                    value={showForm.event_id} 
                    onChange={e => setShowForm({ ...showForm, event_id: e.target.value })}
                    style={{ width: '100%', padding: '10px', borderRadius: '8px', background: '#121826', border: '1px solid rgba(255,255,255,0.15)', color: '#fff' }}
                  >
                    <option value="">-- Choose Event --</option>
                    {events.map(ev => <option key={ev.id} value={ev.id}>{ev.title}</option>)}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Select Venue Screen</label>
                  <select 
                    value={showForm.venue_id} 
                    onChange={e => setShowForm({ ...showForm, venue_id: e.target.value })}
                    style={{ width: '100%', padding: '10px', borderRadius: '8px', background: '#121826', border: '1px solid rgba(255,255,255,0.15)', color: '#fff' }}
                  >
                    <option value="">-- Choose Listed Venue --</option>
                    {venues.map(v => <option key={v.id} value={v.id}>{v.name} ({v.city})</option>)}
                  </select>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px' }}>
                  <div>
                    <label style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>VIP (₹)</label>
                    <input type="number" value={showForm.price_vip} onChange={e => setShowForm({ ...showForm, price_vip: e.target.value })} style={{ width: '100%', padding: '8px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff' }} />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Premium (₹)</label>
                    <input type="number" value={showForm.price_prem} onChange={e => setShowForm({ ...showForm, price_prem: e.target.value })} style={{ width: '100%', padding: '8px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff' }} />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Standard (₹)</label>
                    <input type="number" value={showForm.price_std} onChange={e => setShowForm({ ...showForm, price_std: e.target.value })} style={{ width: '100%', padding: '8px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff' }} />
                  </div>
                </div>
                <button className="btn-primary" type="submit" style={{ justifyContent: 'center', marginTop: '8px' }}>
                  <Sparkles size={16} /> Publish Show & Initialize Seats
                </button>
              </form>
            </div>

          </div>

          {/* Organiser Detailed Per-Event Analytics & Category-Wise Breakdown Table */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '1.3rem', marginBottom: '8px', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <TrendingUp size={20} color="var(--accent-amber)" /> Event Earnings & Seat Category Breakdown
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '20px' }}>
              Track earnings per event, customer names & emails, booked seat numbers, and manage listings.
            </p>

            {!organiserData || organiserData.events?.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No listed events found for this organiser yet.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {organiserData.events.map(ev => {
                  const isExpanded = expandedEventId === ev.event_id;
                  return (
                    <div 
                      key={ev.event_id} 
                      style={{ 
                        background: 'rgba(255,255,255,0.03)', 
                        border: '1px solid rgba(255,255,255,0.08)',
                        borderRadius: '14px', 
                        padding: '20px',
                        overflow: 'hidden'
                      }}
                    >
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '16px', alignItems: 'center' }}>
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                            <h4 style={{ fontSize: '1.15rem', fontWeight: 800 }}>{ev.title}</h4>
                            <span className="badge" style={{ background: 'rgba(16,185,129,0.2)', color: '#10b981' }}>{ev.status}</span>
                            <span className="badge" style={{ background: 'rgba(99,102,241,0.2)', color: '#93c5fd' }}>{ev.event_type}</span>
                          </div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                            {ev.duration_minutes} Mins • {ev.shows_count} Scheduled Showtimes
                          </div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', whiteSpace: 'nowrap' }}>
                          <div style={{ textAlign: 'right' }}>
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Event Earnings</div>
                            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--accent-amber)' }}>₹{ev.total_revenue.toFixed(2)}</div>
                          </div>

                          <div style={{ textAlign: 'right' }}>
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Tickets Sold</div>
                            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#34d399' }}>{ev.total_tickets_sold}</div>
                          </div>

                          <button 
                            className="btn-secondary" 
                            style={{ padding: '8px 14px', fontSize: '0.8rem', whiteSpace: 'nowrap' }}
                            onClick={() => setExpandedEventId(isExpanded ? null : ev.event_id)}
                          >
                            <Eye size={14} /> {isExpanded ? 'Hide Details' : 'View Breakdown & Customers'}
                            {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                          </button>

                          <button 
                            className="btn-secondary" 
                            style={{ padding: '8px 12px', fontSize: '0.8rem', color: '#f87171', border: '1px solid rgba(239,68,68,0.3)', background: 'rgba(239,68,68,0.1)' }}
                            onClick={() => handleDeleteEvent(ev.event_id, ev.title)}
                            title="Delete Event & Associated Customer Bookings"
                          >
                            <Trash2 size={14} color="#f87171" /> Delete
                          </button>
                        </div>
                      </div>

                      {/* Detailed Seat Category, Customer Bookings & Showtimes Breakdown */}
                      {isExpanded && (
                        <div style={{ marginTop: '20px', paddingTop: '20px', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                          
                          {/* Customer Bookings Table */}
                          <div style={{ marginBottom: '24px' }}>
                            <h5 style={{ fontSize: '0.9rem', color: '#fff', fontWeight: 800, marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <UserCheck size={16} color="#34d399" /> Customer Ticket Bookings ({ev.customer_bookings?.length || 0}):
                            </h5>

                            {!ev.customer_bookings || ev.customer_bookings.length === 0 ? (
                              <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', italic: 'true' }}>No confirmed customer bookings for this event yet.</p>
                            ) : (
                              <div style={{ overflowX: 'auto', background: 'rgba(18, 24, 38, 0.9)', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)' }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.8rem' }}>
                                  <thead>
                                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', color: 'var(--text-muted)' }}>
                                      <th style={{ padding: '10px 12px' }}>Customer Name</th>
                                      <th style={{ padding: '10px 12px' }}>Email (Gmail)</th>
                                      <th style={{ padding: '10px 12px' }}>Assigned Seats</th>
                                      <th style={{ padding: '10px 12px' }}>Ref #</th>
                                      <th style={{ padding: '10px 12px', textAlign: 'right' }}>Amount Paid</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {ev.customer_bookings.map(b => (
                                      <tr key={b.booking_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                                        <td style={{ padding: '10px 12px', fontWeight: 700, color: '#fff' }}>
                                          {b.customer_name}
                                        </td>
                                        <td style={{ padding: '10px 12px', color: '#93c5fd', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                          <Mail size={12} color="#93c5fd" /> {b.customer_email}
                                        </td>
                                        <td style={{ padding: '10px 12px' }}>
                                          {b.seats?.map(s => (
                                            <span key={s} className="badge" style={{ background: 'rgba(99,102,241,0.2)', color: '#93c5fd', marginRight: '4px', fontSize: '0.7rem' }}>
                                              {s}
                                            </span>
                                          ))}
                                        </td>
                                        <td style={{ padding: '10px 12px', fontFamily: 'monospace', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                                          {b.booking_reference}
                                        </td>
                                        <td style={{ padding: '10px 12px', textAlign: 'right', fontWeight: 800, color: 'var(--accent-amber)' }}>
                                          ₹{b.total_amount.toFixed(2)}
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            )}
                          </div>

                          {/* Seat Category Breakdown Table */}
                          <div style={{ marginBottom: '20px' }}>
                            <h5 style={{ fontSize: '0.85rem', color: '#fff', fontWeight: 700, marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <CheckCircle2 size={14} color="var(--primary)" /> Seat Category Sales Breakdown:
                            </h5>

                            {ev.category_breakdown.length === 0 ? (
                              <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>No seat categories generated for this event yet.</p>
                            ) : (
                              <div style={{ overflowX: 'auto' }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.8rem' }}>
                                  <thead>
                                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', color: 'var(--text-muted)' }}>
                                      <th style={{ padding: '8px' }}>Category Name</th>
                                      <th style={{ padding: '8px' }}>Booked Seats</th>
                                      <th style={{ padding: '8px' }}>Held Seats</th>
                                      <th style={{ padding: '8px' }}>Available Seats</th>
                                      <th style={{ padding: '8px' }}>Total Seats</th>
                                      <th style={{ padding: '8px', textAlign: 'right' }}>Category Earnings</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {ev.category_breakdown.map(cat => (
                                      <tr key={cat.category_name} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                                        <td style={{ padding: '8px', fontWeight: 700, color: cat.category_name === 'VIP' ? '#fbbf24' : cat.category_name === 'PREMIUM' ? '#93c5fd' : '#fff' }}>
                                          {cat.category_name}
                                        </td>
                                        <td style={{ padding: '8px', color: '#34d399', fontWeight: 700 }}>{cat.booked_seats}</td>
                                        <td style={{ padding: '8px', color: 'var(--accent-amber)' }}>{cat.held_seats}</td>
                                        <td style={{ padding: '8px', color: 'var(--text-muted)' }}>{cat.available_seats}</td>
                                        <td style={{ padding: '8px', fontWeight: 600 }}>{cat.total_seats}</td>
                                        <td style={{ padding: '8px', textAlign: 'right', fontWeight: 800, color: 'var(--accent-amber)' }}>
                                          ₹{cat.revenue.toFixed(2)}
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            )}
                          </div>

                          {/* Showtimes & Occupancy */}
                          {ev.shows.length > 0 && (
                            <div>
                              <h5 style={{ fontSize: '0.85rem', color: '#fff', fontWeight: 700, marginBottom: '10px' }}>
                                Scheduled Showtime Occupancy:
                              </h5>
                              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '10px' }}>
                                {ev.shows.map(sh => {
                                  const occPct = sh.total_seats > 0 ? Math.round((sh.booked_seats / sh.total_seats) * 100) : 0;
                                  return (
                                    <div key={sh.show_id} style={{ background: 'rgba(18, 24, 38, 0.8)', padding: '12px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)' }}>
                                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', fontWeight: 700, marginBottom: '4px' }}>
                                        <span>{sh.venue_name}</span>
                                        <span style={{ color: 'var(--accent-cyan)' }}>{occPct}% Occupied</span>
                                      </div>
                                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
                                        {new Date(sh.start_time).toLocaleString()}
                                      </div>
                                      {/* Occupancy progress bar */}
                                      <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                                        <div style={{ width: `${occPct}%`, height: '100%', background: 'linear-gradient(90deg, #10b981, #ec4899)', borderRadius: '3px' }} />
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          )}

                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

        </div>
      )}

    </div>
  );
}
