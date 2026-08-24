import React, { useState } from 'react';
import { Ticket, Calendar, Bookmark, LayoutDashboard, User, LogOut, ShieldCheck } from 'lucide-react';

export default function Navbar({ currentUser, activeTab, setActiveTab, onLogout, onQuickRoleSwitch, onOpenAuth }) {
  return (
    <nav className="glass-panel" style={{ borderRadius: '0 0 16px 16px', margin: '0 0 24px 0', padding: '14px 28px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', maxWidth: '1200px', margin: '0 auto' }}>
        
        {/* Brand Logo */}
        <div 
          onClick={() => setActiveTab('events')} 
          style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}
        >
          <div style={{ 
            background: 'linear-gradient(135deg, #6366f1, #ec4899)', 
            padding: '8px', 
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 15px rgba(99, 102, 241, 0.5)'
          }}>
            <Ticket size={24} color="#fff" />
          </div>
          <div>
            <h2 className="brand-font" style={{ fontSize: '1.4rem', fontWeight: 800, background: 'linear-gradient(90deg, #fff, #93c5fd)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              TICKETSMITH
            </h2>
            <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', letterSpacing: '1px', textTransform: 'uppercase' }}>
              Live Entertainment & Movies
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {currentUser?.role === 'CUSTOMER' || !currentUser ? (
            <>
              <button 
                className={`btn-secondary ${activeTab === 'events' ? 'active' : ''}`}
                onClick={() => setActiveTab('events')}
                style={{ 
                  background: activeTab === 'events' ? 'rgba(99, 102, 241, 0.2)' : 'transparent',
                  borderColor: activeTab === 'events' ? 'var(--primary)' : 'transparent',
                  color: activeTab === 'events' ? '#fff' : 'var(--text-muted)'
                }}
              >
                <Calendar size={16} /> Browse Events
              </button>

              {currentUser && (
                <>
                  <button 
                    className={`btn-secondary ${activeTab === 'bookings' ? 'active' : ''}`}
                    onClick={() => setActiveTab('bookings')}
                    style={{ 
                      background: activeTab === 'bookings' ? 'rgba(99, 102, 241, 0.2)' : 'transparent',
                      borderColor: activeTab === 'bookings' ? 'var(--primary)' : 'transparent',
                      color: activeTab === 'bookings' ? '#fff' : 'var(--text-muted)'
                    }}
                  >
                    <Ticket size={16} /> My Bookings
                  </button>

                  <button 
                    className={`btn-secondary ${activeTab === 'waitlists' ? 'active' : ''}`}
                    onClick={() => setActiveTab('waitlists')}
                    style={{ 
                      background: activeTab === 'waitlists' ? 'rgba(99, 102, 241, 0.2)' : 'transparent',
                      borderColor: activeTab === 'waitlists' ? 'var(--primary)' : 'transparent',
                      color: activeTab === 'waitlists' ? '#fff' : 'var(--text-muted)'
                    }}
                  >
                    <Bookmark size={16} /> Waitlists
                  </button>
                </>
              )}
            </>
          ) : (
            <button 
              className={`btn-secondary ${activeTab === 'dashboard' ? 'active' : ''}`}
              onClick={() => setActiveTab('dashboard')}
              style={{ 
                background: 'rgba(236, 72, 153, 0.2)',
                borderColor: 'var(--accent-pink)',
                color: '#fff'
              }}
            >
              <LayoutDashboard size={16} /> {currentUser.role === 'ADMIN' ? 'Admin Console' : 'Organiser Portal'}
            </button>
          )}
        </div>

        {/* User Profile & Authentication Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>

          {currentUser ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{currentUser.name}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--accent-cyan)' }}>{currentUser.email}</div>
              </div>
              <button 
                onClick={onLogout} 
                className="btn-secondary" 
                style={{ padding: '8px', borderRadius: '50%' }}
                title="Logout"
              >
                <LogOut size={16} color="#ef4444" />
              </button>
            </div>
          ) : (
            <button className="btn-primary" onClick={onOpenAuth}>
              <User size={16} /> Sign In
            </button>
          )}

        </div>

      </div>
    </nav>
  );
}
