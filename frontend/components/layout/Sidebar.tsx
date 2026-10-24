'use client';

import type { PageId } from '@/app/page';

interface SidebarProps {
  currentPage: PageId;
  onNavigate: (page: PageId) => void;
  wsStatus: string;
}

const navItems: { id: PageId; label: string; icon: string }[] = [
  { id: 'overview', label: 'Overview', icon: '◈' },
  { id: 'map', label: 'Live Parking Map', icon: '🗺' },
  { id: 'navigation', label: 'AI Navigation', icon: '🧭' },
  { id: 'reservations', label: 'Reservations', icon: '📋' },
  { id: 'analytics', label: 'Analytics', icon: '📊' },
  { id: 'iot', label: 'IoT Sensors', icon: '📡' },
  { id: 'settings', label: 'Settings', icon: '⚙️' },
];

export default function Sidebar({ currentPage, onNavigate, wsStatus }: SidebarProps) {
  return (
    <aside className="app-sidebar" style={{ display: 'flex', flexDirection: 'column' }}>
      {/* Logo */}
      <div style={{
        padding: '20px 16px 16px',
        borderBottom: '1px solid var(--color-border)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 36,
            height: 36,
            borderRadius: 10,
            background: 'linear-gradient(135deg, #2563eb, #1d4ed8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: 18,
            fontWeight: 800,
            flexShrink: 0,
          }}>P</div>
          <div>
            <div style={{ fontWeight: 800, fontSize: 15, color: 'var(--color-text-primary)', letterSpacing: '-0.02em' }}>
              ParkFlow AI
            </div>
            <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 1 }}>
              Smart Parking System
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, padding: '12px 0', overflowY: 'auto' }}>
        {navItems.map((item) => (
          <button
            key={item.id}
            className={`nav-item ${currentPage === item.id ? 'active' : ''}`}
            onClick={() => onNavigate(item.id)}
            style={{ width: '100%', textAlign: 'left', background: 'none', border: 'none' }}
          >
            <span style={{ fontSize: 15, width: 20, textAlign: 'center' }}>{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      {/* Connection Status */}
      <div style={{
        padding: '12px 16px',
        borderTop: '1px solid var(--color-border)',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
      }}>
        <span className={`connection-dot ${wsStatus}`} />
        <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
          {wsStatus === 'connected' ? 'Live Connected' :
           wsStatus === 'connecting' ? 'Connecting...' : 'Disconnected'}
        </span>
      </div>

      {/* Version */}
      <div style={{
        padding: '8px 16px 16px',
        fontSize: 11,
        color: 'var(--color-text-muted)',
      }}>
        v1.0.0 — Demo Mode
      </div>
    </aside>
  );
}
