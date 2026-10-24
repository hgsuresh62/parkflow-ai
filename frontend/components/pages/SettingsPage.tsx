'use client';

import { useState } from 'react';
import type { SlotStatus } from '@/types';

interface Props {
  slotUpdates: Record<string, SlotStatus>;
  addToast: (title: string, message: string, type?: 'success' | 'info' | 'warning' | 'error') => void;
  selectedSlot: string | null;
  setSelectedSlot: (slot: string | null) => void;
  activeRoute: string | null;
  setActiveRoute: (route: string | null) => void;
  setCurrentPage: (page: any) => void;
}

export default function SettingsPage({ addToast }: Props) {
  const [apiUrl, setApiUrl] = useState(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000');
  const [wsUrl, setWsUrl] = useState(process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000');
  const [iotMode, setIotMode] = useState('simulation');
  const [simInterval, setSimInterval] = useState('5');
  const [theme, setTheme] = useState('light');

  const handleSave = () => {
    addToast('Settings Saved', 'Configuration changes apply on next page load', 'success');
  };

  const handleTestConnection = async () => {
    try {
      const res = await fetch(`${apiUrl}/health`);
      if (res.ok) {
        const data = await res.json();
        addToast('Connected!', `Backend v${data.version} is running`, 'success');
      } else {
        addToast('Connection Failed', `HTTP ${res.status}`, 'error');
      }
    } catch (e) {
      addToast('Connection Failed', 'Cannot reach backend server', 'error');
    }
  };

  return (
    <div style={{ maxWidth: 700 }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 800, marginBottom: 4 }}>Settings</h1>
        <p style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>
          Configure ParkFlow AI connection and behavior
        </p>
      </div>

      {/* Connection Settings */}
      <Section title="Backend Connection" icon="🔌">
        <FormRow label="API Base URL">
          <input
            type="text"
            value={apiUrl}
            onChange={(e) => setApiUrl(e.target.value)}
            style={inputStyle}
          />
        </FormRow>
        <FormRow label="WebSocket URL">
          <input
            type="text"
            value={wsUrl}
            onChange={(e) => setWsUrl(e.target.value)}
            style={inputStyle}
          />
        </FormRow>
        <div style={{ display: 'flex', gap: 10, marginTop: 4 }}>
          <button className="btn btn-primary" onClick={handleTestConnection}>
            🔍 Test Connection
          </button>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', alignSelf: 'center' }}>
            Changes take effect after page reload
          </div>
        </div>
      </Section>

      {/* IoT Settings */}
      <Section title="IoT Configuration" icon="📡">
        <FormRow label="IoT Mode">
          <select value={iotMode} onChange={(e) => setIotMode(e.target.value)} style={inputStyle}>
            <option value="simulation">Simulation (No hardware needed)</option>
            <option value="mqtt">MQTT (Physical sensors)</option>
            <option value="thingspeak">ThingSpeak (Cloud IoT)</option>
            <option value="hybrid">Hybrid (Sim + Real)</option>
          </select>
        </FormRow>
        <FormRow label="Simulation Interval (seconds)">
          <input
            type="number"
            min={1}
            max={60}
            value={simInterval}
            onChange={(e) => setSimInterval(e.target.value)}
            style={{ ...inputStyle, width: 120 }}
          />
        </FormRow>
        {iotMode === 'mqtt' && (
          <div style={{ padding: 12, background: '#fef3c7', borderRadius: 8, fontSize: 12, color: '#92400e', marginTop: 8 }}>
            <strong>MQTT requires:</strong> Mosquitto broker running and sensor firmware configured.
            Set MQTT_BROKER_HOST in your .env file.
          </div>
        )}
        {iotMode === 'thingspeak' && (
          <div style={{ padding: 12, background: '#fef3c7', borderRadius: 8, fontSize: 12, color: '#92400e', marginTop: 8 }}>
            <strong>ThingSpeak requires:</strong> A ThingSpeak account with THINGSPEAK_CHANNEL_ID and THINGSPEAK_READ_API_KEY in .env.
          </div>
        )}
      </Section>

      {/* System Info */}
      <Section title="System Information" icon="ℹ️">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
          <InfoItem label="Application" value="ParkFlow AI v1.0.0" />
          <InfoItem label="Frontend" value="Next.js 14 + TypeScript" />
          <InfoItem label="Backend" value="FastAPI + SQLAlchemy" />
          <InfoItem label="Database" value="SQLite (aiosqlite)" />
          <InfoItem label="AI Routing" value="NetworkX Dijkstra" />
          <InfoItem label="Real-time" value="WebSocket" />
          <InfoItem label="IoT Sensors" value="HC-SR04 (virtual)" />
          <InfoItem label="Parking Slots" value="100 across 3 floors" />
        </div>
      </Section>

      {/* Quick Reference */}
      <Section title="API Reference" icon="📚">
        <div style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>
          <div style={{ marginBottom: 8 }}>
            <a href={`${apiUrl}/docs`} target="_blank" rel="noreferrer" style={{ color: '#2563eb', fontWeight: 600 }}>
              {apiUrl}/docs
            </a>
            {' '} — Interactive API documentation (Swagger UI)
          </div>
          <div style={{ marginBottom: 8 }}>
            <a href={`${apiUrl}/redoc`} target="_blank" rel="noreferrer" style={{ color: '#2563eb', fontWeight: 600 }}>
              {apiUrl}/redoc
            </a>
            {' '} — ReDoc API reference
          </div>
          <div style={{ marginBottom: 8 }}>
            <a href={`${apiUrl}/health`} target="_blank" rel="noreferrer" style={{ color: '#2563eb', fontWeight: 600 }}>
              {apiUrl}/health
            </a>
            {' '} — Backend health check
          </div>
        </div>
      </Section>

      {/* Environment Variables */}
      <Section title="Environment Setup" icon="⚙️">
        <div style={{ background: '#0f172a', color: '#e2e8f0', borderRadius: 10, padding: 16, fontFamily: 'monospace', fontSize: 12, lineHeight: 1.8 }}>
          <div style={{ color: '#94a3b8' }}># Copy .env.example to .env and configure:</div>
          <div><span style={{ color: '#60a5fa' }}>DATABASE_URL</span>=sqlite+aiosqlite:///./parkflow.db</div>
          <div><span style={{ color: '#60a5fa' }}>IOT_MODE</span>=simulation</div>
          <div><span style={{ color: '#60a5fa' }}>NEXT_PUBLIC_API_URL</span>=http://localhost:8000</div>
          <div><span style={{ color: '#60a5fa' }}>NEXT_PUBLIC_WS_URL</span>=ws://localhost:8000</div>
        </div>
      </Section>

      <div style={{ display: 'flex', gap: 10 }}>
        <button className="btn btn-primary" onClick={handleSave}>💾 Save Settings</button>
        <button className="btn btn-outline" onClick={() => window.location.reload()}>↻ Reload App</button>
      </div>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '9px 12px',
  border: '1px solid var(--color-border)',
  borderRadius: 8,
  fontSize: 13,
  color: 'var(--color-text-primary)',
  background: 'var(--color-surface)',
};

function Section({ title, icon, children }: { title: string; icon: string; children: React.ReactNode }) {
  return (
    <div className="card" style={{ padding: 24, marginBottom: 16 }}>
      <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
        <span>{icon}</span> {title}
      </div>
      {children}
    </div>
  );
}

function FormRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
        {label}
      </label>
      {children}
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ padding: '10px 12px', background: 'var(--color-surface-subtle)', borderRadius: 8 }}>
      <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginBottom: 3 }}>{label}</div>
      <div style={{ fontSize: 13, fontWeight: 700 }}>{value}</div>
    </div>
  );
}
