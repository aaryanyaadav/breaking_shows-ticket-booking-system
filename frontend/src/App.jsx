import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import ShowBooking from './pages/ShowBooking';
import MyBookings from './pages/MyBookings';
import Waitlists from './pages/Waitlists';
import Dashboard from './pages/Dashboard';
import { X, UserCheck, ShieldAlert } from 'lucide-react';
import { API_BASE } from './config';

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [activeTab, setActiveTab] = useState('events');
  const [selectedEvent, setSelectedEvent] = useState(null);

  // Auth modal state
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [isLogin, setIsLogin] = useState(true);
  const [authForm, setAuthForm] = useState({ name: '', email: '', password: '', role: 'CUSTOMER' });

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      fetchMe(token);
    }
  }, []);

  const fetchMe = async (token) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCurrentUser(data);
        if (data.role === 'ORGANISER' || data.role === 'ADMIN') {
          setActiveTab('dashboard');
        }
      } else {
        localStorage.removeItem('token');
        setCurrentUser(null);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleQuickDemoLogin = async (role) => {
    let email = 'aryan@gmail.com';
    let password = 'cust123';
    let name = 'Aryan Sharma';

    if (role === 'ORGANISER') {
      email = 'org@bookmyshow.com';
      password = 'org123';
      name = 'BookMyShow Organiser';
    } else if (role === 'ADMIN') {
      email = 'admin@ticketmaster.com';
      password = 'admin123';
      name = 'Admin User';
    }

    try {
      let res = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      if (!res.ok) {
        // Fallback: register demo user if not yet seeded in backend DB
        res = await fetch(`${API_BASE}/api/v1/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, email, password, role })
        });
      }

      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('token', data.access_token);
        setCurrentUser(data.user);
      } else {
        // Instant mock state fallback if auth API is offline/unreachable
        const mockUser = { id: `demo-${role.toLowerCase()}`, name, email, role };
        setCurrentUser(mockUser);
      }
    } catch (e) {
      console.error(e);
      const mockUser = { id: `demo-${role.toLowerCase()}`, name, email, role };
      setCurrentUser(mockUser);
    }

    setSelectedEvent(null);
    if (role === 'ORGANISER' || role === 'ADMIN') {
      setActiveTab('dashboard');
    } else {
      setActiveTab('events');
    }
  };

  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    const endpoint = isLogin ? `${API_BASE}/api/v1/auth/login` : `${API_BASE}/api/v1/auth/register`;
    const body = isLogin 
      ? { email: authForm.email, password: authForm.password }
      : authForm;

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const data = await res.json();
      if (!res.ok) {
        alert(data.detail || "Auth failed");
        return;
      }
      localStorage.setItem('token', data.access_token);
      setCurrentUser(data.user);
      setShowAuthModal(false);
      if (data.user?.role === 'ORGANISER' || data.user?.role === 'ADMIN') {
        setActiveTab('dashboard');
      }
    } catch (err) {
      console.error(err);
      alert(`Authentication Error: ${err.message || "Failed to connect to backend server."}`);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setCurrentUser(null);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      
      {/* Top Navbar */}
      <Navbar 
        currentUser={currentUser}
        activeTab={activeTab}
        setActiveTab={(tab) => {
          setActiveTab(tab);
          setSelectedEvent(null);
        }}
        onLogout={handleLogout}
        onQuickRoleSwitch={handleQuickDemoLogin}
        onOpenAuth={() => setShowAuthModal(true)}
      />

      {/* Main Content Router */}
      <main style={{ flex: 1 }}>
        {currentUser?.role === 'ORGANISER' || currentUser?.role === 'ADMIN' ? (
          <Dashboard currentUser={currentUser} />
        ) : selectedEvent ? (
          <ShowBooking 
            event={selectedEvent} 
            currentUser={currentUser}
            onBack={() => setSelectedEvent(null)}
            onOpenAuth={() => setShowAuthModal(true)}
          />
        ) : activeTab === 'events' ? (
          <Home 
            onSelectEvent={(evt) => {
              if (currentUser?.role === 'ORGANISER' || currentUser?.role === 'ADMIN') {
                setActiveTab('dashboard');
              } else {
                setSelectedEvent(evt);
              }
            }} 
          />
        ) : activeTab === 'bookings' ? (
          <MyBookings currentUser={currentUser} />
        ) : activeTab === 'waitlists' ? (
          <Waitlists currentUser={currentUser} />
        ) : (
          <Dashboard currentUser={currentUser} />
        )}
      </main>

      {/* Footer */}
      <footer style={{ borderTop: '1px solid rgba(255,255,255,0.08)', padding: '24px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          Ticketsmith • Online Ticket Allocation Platform • Real-Time Seating & Digital Passes
        </div>
      </footer>

      {/* Auth Modal */}
      {showAuthModal && (
        <div className="modal-backdrop">
          <div className="glass-panel" style={{ maxWidth: '420px', width: '100%', padding: '28px', position: 'relative' }}>
            <button 
              onClick={() => setShowAuthModal(false)}
              style={{ position: 'absolute', top: '16px', right: '16px', background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
            >
              <X size={20} />
            </button>

            <h3 style={{ fontSize: '1.4rem', marginBottom: '4px', fontWeight: 800 }}>
              {isLogin ? 'Sign In' : 'Create Account'}
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '16px' }}>
              Access live seat reservations, show scheduling, or venue admin tools.
            </p>

            {/* Role Selection Tabs for Sign In & Registration */}
            <div style={{ marginBottom: '16px' }}>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Account Type:</label>
              <div style={{ display: 'grid', gridTemplateColumns: isLogin ? '1fr 1fr 1fr' : '1fr 1fr', gap: '6px' }}>
                {[
                  { id: 'CUSTOMER', label: 'Customer', email: 'aryan@gmail.com', pass: 'cust123' },
                  { id: 'ORGANISER', label: 'Organiser', email: 'org@bookmyshow.com', pass: 'org123' },
                  { id: 'ADMIN', label: 'Admin', email: 'admin@ticketmaster.com', pass: 'admin123' }
                ].filter(r => isLogin || r.id !== 'ADMIN').map(r => (
                  <button
                    key={r.id}
                    type="button"
                    onClick={() => {
                      setAuthForm({ 
                        ...authForm, 
                        role: r.id,
                        email: isLogin ? r.email : authForm.email,
                        password: isLogin ? r.pass : authForm.password
                      });
                    }}
                    style={{
                      padding: '8px 4px',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      borderRadius: '8px',
                      border: authForm.role === r.id ? '1px solid var(--primary)' : '1px solid rgba(255,255,255,0.1)',
                      background: authForm.role === r.id ? 'rgba(99,102,241,0.2)' : 'rgba(255,255,255,0.03)',
                      color: authForm.role === r.id ? '#fff' : 'var(--text-muted)',
                      cursor: 'pointer'
                    }}
                  >
                    {r.label}
                  </button>
                ))}
              </div>
            </div>

            <form onSubmit={handleAuthSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {!isLogin && (
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Full Name</label>
                  <input 
                    type="text" 
                    required
                    placeholder="e.g. Alex Morgan"
                    value={authForm.name}
                    onChange={e => setAuthForm({ ...authForm, name: e.target.value })}
                    style={{ width: '100%', padding: '10px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff' }}
                  />
                </div>
              )}

              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Email Address</label>
                <input 
                  type="email" 
                  required
                  placeholder="e.g. name@example.com"
                  value={authForm.email}
                  onChange={e => setAuthForm({ ...authForm, email: e.target.value })}
                  style={{ width: '100%', padding: '10px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Password</label>
                <input 
                  type="password" 
                  required
                  value={authForm.password}
                  onChange={e => setAuthForm({ ...authForm, password: e.target.value })}
                  style={{ width: '100%', padding: '10px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff' }}
                />
              </div>

              <button className="btn-primary" type="submit" style={{ justifyContent: 'center', marginTop: '8px' }}>
                {isLogin ? `Sign In as ${authForm.role}` : `Register as ${authForm.role}`}
              </button>
            </form>

            <div style={{ textAlign: 'center', marginTop: '16px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {isLogin ? "Don't have an account? " : "Already have an account? "}
              <button 
                onClick={() => {
                  const nextIsLogin = !isLogin;
                  setIsLogin(nextIsLogin);
                  if (!nextIsLogin && authForm.role === 'ADMIN') {
                    setAuthForm(f => ({ ...f, role: 'CUSTOMER' }));
                  }
                }} 
                style={{ background: 'transparent', border: 'none', color: 'var(--accent-pink)', cursor: 'pointer', fontWeight: 700 }}
              >
                {isLogin ? 'Register' : 'Login'}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
