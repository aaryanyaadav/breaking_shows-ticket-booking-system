import React from 'react';
import { X, QrCode, CheckCircle2, Download, Ticket as TicketIcon } from 'lucide-react';

export default function TicketModal({ ticket, onClose }) {
  if (!ticket) return null;

  return (
    <div className="modal-backdrop">
      <div className="glass-panel" style={{ maxWidth: '420px', width: '100%', padding: '28px', position: 'relative' }}>
        
        <button 
          onClick={onClose} 
          style={{ position: 'absolute', top: '16px', right: '16px', background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
        >
          <X size={20} />
        </button>

        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          <CheckCircle2 size={40} color="#10b981" style={{ margin: '0 auto 8px auto' }} />
          <h3 style={{ fontSize: '1.4rem' }}>Booking Confirmed!</h3>
          <span style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)' }}>Ticket Reference: {ticket.ticket_reference}</span>
        </div>

        {/* QR Code Card */}
        <div style={{
          background: '#fff',
          padding: '20px',
          borderRadius: '16px',
          textAlign: 'center',
          margin: '0 auto 20px auto',
          boxShadow: '0 10px 30px rgba(0,0,0,0.5)'
        }}>
          {ticket.qr_code_url ? (
            <img 
              src={ticket.qr_code_url} 
              alt="Ticket QR Code" 
              style={{ width: '180px', height: '180px', margin: '0 auto' }} 
            />
          ) : (
            <QrCode size={160} color="#000" style={{ margin: '0 auto' }} />
          )}
          <div style={{ color: '#000', fontSize: '0.7rem', fontWeight: 700, marginTop: '8px', letterSpacing: '1px' }}>
            SCAN AT VENUE GATE
          </div>
        </div>

        <div style={{ background: 'rgba(255,255,255,0.04)', padding: '14px', borderRadius: '12px', marginBottom: '20px', fontSize: '0.85rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Seats Assigned:</span>
            <span style={{ fontWeight: 700, color: 'var(--accent-amber)' }}>{ticket.seats ? ticket.seats.join(', ') : 'Assigned Seats'}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Status:</span>
            <span style={{ fontWeight: 700, color: '#10b981' }}>{ticket.status}</span>
          </div>
        </div>

        <button 
          className="btn-primary" 
          style={{ width: '100%', justifyContent: 'center' }}
          onClick={() => window.print()}
        >
          <Download size={16} /> Download PDF Ticket
        </button>

      </div>
    </div>
  );
}
