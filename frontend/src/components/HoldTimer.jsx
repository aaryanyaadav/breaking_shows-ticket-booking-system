import React, { useState, useEffect } from 'react';
import { Clock, AlertTriangle } from 'lucide-react';

export default function HoldTimer({ expiresAt, onExpired }) {
  const [timeLeft, setTimeLeft] = useState(0);

  useEffect(() => {
    if (!expiresAt) return;

    let dateStr = expiresAt;
    if (typeof dateStr === 'string' && !dateStr.endsWith('Z') && !dateStr.includes('+')) {
      dateStr = dateStr + 'Z';
    }

    const targetTime = new Date(dateStr).getTime();

    const updateTimer = () => {
      const now = new Date().getTime();
      const difference = Math.max(0, Math.floor((targetTime - now) / 1000));
      setTimeLeft(difference);

      if (difference <= 0 && onExpired) {
        onExpired();
      }
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [expiresAt]);


  const minutes = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;
  const isUrgent = timeLeft < 60;

  return (
    <div style={{
      position: 'fixed',
      bottom: '24px',
      right: '24px',
      zIndex: 90,
      background: isUrgent ? 'rgba(239, 68, 68, 0.9)' : 'rgba(18, 24, 38, 0.9)',
      backdropFilter: 'blur(12px)',
      border: `1px solid ${isUrgent ? '#ef4444' : 'var(--primary)'}`,
      padding: '12px 20px',
      borderRadius: '30px',
      boxShadow: '0 8px 30px rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      color: '#fff',
      animation: isUrgent ? 'pulse-red 1s infinite' : 'none'
    }}>
      {isUrgent ? <AlertTriangle size={20} color="#fff" /> : <Clock size={20} color="var(--accent-amber)" />}
      <div>
        <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '1px', opacity: 0.8 }}>
          Seats Held TTL
        </div>
        <div style={{ fontSize: '1.2rem', fontWeight: 800, fontFamily: 'monospace' }}>
          {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
        </div>
      </div>
    </div>
  );
}
