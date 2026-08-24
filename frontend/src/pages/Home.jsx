import React, { useState, useEffect } from 'react';
import { Search, Film, Music, Trophy, Sparkles, MapPin, Clock } from 'lucide-react';

export default function Home({ onSelectEvent }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchEvents();
  }, [selectedType]);

  const fetchEvents = async () => {
    setLoading(true);
    try {
      let url = '/api/v1/events';
      if (selectedType !== 'ALL') {
        url += `?event_type=${selectedType}`;
      }
      const res = await fetch(url);
      const data = await res.json();
      setEvents(data);
    } catch (err) {
      console.error("Failed to fetch events:", err);
    } finally {
      setLoading(false);
    }
  };

  const filteredEvents = events.filter(e => 
    e.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (e.description && e.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const getBadgeClass = (type) => {
    switch (type) {
      case 'MOVIE': return 'badge-movie';
      case 'CONCERT': return 'badge-concert';
      case 'SPORTS': return 'badge-sports';
      default: return 'badge-theatre';
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 20px 60px 20px' }}>
      
      {/* Hero Banner */}
      <div className="glass-panel" style={{
        padding: '48px 36px',
        marginBottom: '40px',
        background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(236, 72, 153, 0.15) 100%)',
        border: '1px solid rgba(99, 102, 241, 0.3)',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <div style={{ maxWidth: '650px', position: 'relative', zIndex: 2 }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: 'rgba(99, 102, 241, 0.2)', padding: '6px 14px', borderRadius: '20px', color: '#93c5fd', fontSize: '0.8rem', fontWeight: 700, marginBottom: '16px' }}>
            <Sparkles size={14} /> Live Entertainment & Movies
          </div>
          <h1 style={{ fontSize: '2.8rem', fontWeight: 800, lineHeight: 1.15, marginBottom: '16px' }}>
            Book Tickets for <span style={{ color: 'var(--accent-pink)' }}>Live Concerts</span> & Movies.
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '1rem', lineHeight: 1.6, marginBottom: '24px' }}>
            Interactive seat maps, instant seat reservations, category waitlists, and digital QR ticket passes.
          </p>

          {/* Search bar */}
          <div style={{ display: 'flex', gap: '12px', background: 'rgba(18, 24, 38, 0.9)', padding: '8px 16px', borderRadius: '14px', border: '1px solid rgba(255,255,255,0.15)' }}>
            <Search size={20} color="var(--text-muted)" style={{ marginTop: '8px' }} />
            <input 
              type="text" 
              placeholder="Search movies, concerts, stadium shows..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ background: 'transparent', border: 'none', outline: 'none', color: '#fff', width: '100%', fontSize: '0.95rem' }}
            />
          </div>
        </div>
      </div>

      {/* Category Filter Pills */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '32px', flexWrap: 'wrap' }}>
        {[
          { id: 'ALL', label: 'All Events', icon: Sparkles },
          { id: 'MOVIE', label: 'Movies', icon: Film },
          { id: 'CONCERT', label: 'Concerts', icon: Music },
          { id: 'SPORTS', label: 'Sports', icon: Trophy }
        ].map(cat => {
          const Icon = cat.icon;
          const isActive = selectedType === cat.id;
          return (
            <button
              key={cat.id}
              onClick={() => setSelectedType(cat.id)}
              className="btn-secondary"
              style={{
                background: isActive ? 'linear-gradient(135deg, var(--primary), var(--accent-pink))' : 'rgba(255,255,255,0.05)',
                borderColor: isActive ? 'transparent' : 'rgba(255,255,255,0.1)',
                color: '#fff',
                fontWeight: isActive ? 700 : 500
              }}
            >
              <Icon size={16} /> {cat.label}
            </button>
          );
        })}
      </div>

      {/* Event Cards Grid */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
          Loading events...
        </div>
      ) : filteredEvents.length === 0 ? (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
          No events found matching your criteria.
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '24px' }}>
          {filteredEvents.map(evt => (
            <div 
              key={evt.id}
              className="glass-panel glass-panel-interactive"
              onClick={() => onSelectEvent(evt)}
              style={{ cursor: 'pointer', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}
            >
              <div style={{ height: '220px', position: 'relative', overflow: 'hidden', background: '#121826' }}>
                <img 
                  src={evt.poster_url || 'https://images.unsplash.com/photo-1470225620780-dba8ba36b745?auto=format&fit=crop&w=800&q=80'} 
                  alt={evt.title}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
                />
                <div style={{ position: 'absolute', top: '12px', left: '12px' }}>
                  <span className={`badge ${getBadgeClass(evt.event_type)}`}>
                    {evt.event_type}
                  </span>
                </div>
              </div>

              <div style={{ padding: '20px', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <h3 style={{ fontSize: '1.25rem', marginBottom: '8px', lineHeight: 1.3 }}>{evt.title}</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '16px', lineClamp: 2, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {evt.description}
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '14px' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={14} /> {evt.duration_minutes} mins
                  </span>
                  <button className="btn-primary" style={{ padding: '6px 14px', fontSize: '0.8rem' }}>
                    Book Shows
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

    </div>
  );
}
