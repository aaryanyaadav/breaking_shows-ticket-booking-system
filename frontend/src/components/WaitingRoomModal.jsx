import React, { useState, useEffect } from 'react';
import { Users, ShieldAlert, Sparkles } from 'lucide-react';

export default function WaitingRoomModal({ queueData, onEligible }) {
  useEffect(() => {
    if (queueData?.status === 'ELIGIBLE') {
      const timer = setTimeout(() => {
        onEligible();
      }, 1200);
      return () => clearTimeout(timer);
    }
  }, [queueData]);

  if (!queueData) return null;

  return (
    <div className="modal-backdrop">
      <div className="glass-panel" style={{ maxWidth: '480px', width: '100%', padding: '32px', textAlign: 'center' }}>
        
        <div style={{
          width: '72px',
          height: '72px',
          borderRadius: '50%',
          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(236, 72, 153, 0.3))',
          border: '2px solid var(--primary)',
          margin: '0 auto 20px auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 30px rgba(99, 102, 241, 0.4)'
        }}>
          <Users size={32} color="var(--accent-cyan)" />
        </div>

        <h2 style={{ fontSize: '1.5rem', marginBottom: '8px' }}>
          Virtual Waiting Room
        </h2>

        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '24px', lineHeight: 1.5 }}>
          High demand event! You are in a controlled queue. We are metering customers into seat selection to ensure smooth checkout.
        </p>

        {queueData.status === 'ELIGIBLE' ? (
          <div style={{ padding: '16px', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10b981', borderRadius: '12px' }}>
            <Sparkles size={24} color="#10b981" style={{ margin: '0 auto 8px auto' }} />
            <h4 style={{ color: '#34d399', margin: 0 }}>You are next! Entering seat selection...</h4>
          </div>
        ) : (
          <div style={{ background: 'rgba(255, 255, 255, 0.04)', padding: '20px', borderRadius: '14px', border: '1px solid rgba(255,255,255,0.08)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>
              Your Queue Position
            </div>
            <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--accent-amber)', margin: '8px 0' }}>
              #{queueData.queue_position}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Total Waiting: {queueData.total_in_queue} customers
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)', marginTop: '8px' }}>
              Estimated Wait: ~{queueData.estimated_wait_seconds} seconds
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
