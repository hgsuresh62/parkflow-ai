'use client';

import { useState, useEffect } from 'react';
import type { PageId } from '@/app/page';

interface TopNavProps {
  title: string;
  wsStatus: string;
  currentPage: PageId;
}

export default function TopNav({ title, wsStatus, currentPage }: TopNavProps) {
  const [time, setTime] = useState('');

  useEffect(() => {
    const update = () => {
      setTime(new Date().toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
        timeZone: 'Asia/Kolkata',
      }));
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  const breadcrumb = ['ParkFlow AI', title];

  return (
    <header className="app-topnav" style={{ gap: 16 }}>
      {/* Breadcrumb */}
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginBottom: 2 }}>
          {breadcrumb.join(' / ')}
        </div>
        <h1 style={{ fontSize: 18, fontWeight: 700, color: 'var(--color-text-primary)', letterSpacing: '-0.02em' }}>
          {title}
        </h1>
      </div>

      {/* Right side */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        {/* Demo badge */}
        <div style={{
          background: '#fef3c7',
          color: '#92400e',
          padding: '4px 10px',
          borderRadius: 999,
          fontSize: 11,
          fontWeight: 600,
          border: '1px solid #fde68a',
        }}>
          🎯 Simulated Demo
        </div>

        {/* WS Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span className={`connection-dot ${wsStatus}`} />
          <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
            {wsStatus === 'connected' ? 'Live' : wsStatus}
          </span>
        </div>

        {/* Time */}
        <div style={{
          background: 'var(--color-surface-muted)',
          padding: '6px 12px',
          borderRadius: 8,
          fontSize: 13,
          fontWeight: 600,
          color: 'var(--color-text-secondary)',
          minWidth: 72,
          textAlign: 'center',
        }}>
          {time}
        </div>

        {/* User avatar placeholder */}
        <div style={{
          width: 34,
          height: 34,
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontSize: 14,
          fontWeight: 700,
          cursor: 'pointer',
        }}>
          U
        </div>
      </div>
    </header>
  );
}
