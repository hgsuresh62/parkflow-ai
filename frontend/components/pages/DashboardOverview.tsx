'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import type { AvailabilitySummary, AnalyticsOverview, SensorEvent, SimulatorStatus, SlotStatus } from '@/types';
import type { PageId } from '@/app/page';

interface Props {
  slotUpdates: Record<string, SlotStatus>;
  addToast: (title: string, message: string, type?: 'success' | 'info' | 'warning' | 'error') => void;
  setCurrentPage: (page: PageId) => void;
  selectedSlot: string | null;
  setSelectedSlot: (slot: string | null) => void;
  activeRoute: string | null;
  setActiveRoute: (route: string | null) => void;
}

export default function DashboardOverview({ addToast, setCurrentPage }: Props) {
  const [availability, setAvailability] = useState<AvailabilitySummary | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [recentEvents, setRecentEvents] = useState<SensorEvent[]>([]);
  const [simStatus, setSimStatus] = useState<SimulatorStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [avail, analyt, events, sim] = await Promise.all([
        api.slots.availability(),
        api.analytics.overview(),
        api.analytics.activity(1, 10),
        api.iot.simulator.status(),
      ]);
      setAvailability(avail);
      setAnalytics(analyt);
      setRecentEvents(events.activity);
      setSimStatus(sim);
      setError(null);
    } catch (e) {
      setError('Cannot connect to backend. Is the server running?');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const timer = setInterval(fetchData, 10000);
    return () => clearInterval(timer);
  }, [fetchData]);

  const handleStartDemo = async () => {
    try {
      await api.iot.simulator.startDemo();
      addToast('Demo Started', 'Live demo sequence is now running!', 'success');
      fetchData();
    } catch {
      addToast('Error', 'Failed to start demo', 'error');
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 400 }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>⟳</div>
          <div style={{ color: 'var(--color-text-muted)' }}>Loading ParkFlow AI...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 400 }}>
        <div className="card" style={{ padding: 32, textAlign: 'center', maxWidth: 400 }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>⚠️</div>
          <div style={{ fontWeight: 700, marginBottom: 8, color: 'var(--color-text-primary)' }}>Backend Not Reachable</div>
          <div style={{ color: 'var(--color-text-muted)', marginBottom: 20, fontSize: 13 }}>{error}</div>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', background: '#f8fafc', padding: '10px 14px', borderRadius: 8, fontFamily: 'monospace', textAlign: 'left' }}>
            cd backend<br />
            pip install -r requirements.txt<br />
            python -m app.main
          </div>
          <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={fetchData}>Retry</button>
        </div>
      </div>
    );
  }

  const avail = availability;
  const occupancyColor = avail && avail.occupancy_percentage > 80 ? '#ef4444'
    : avail && avail.occupancy_percentage > 50 ? '#f59e0b' : '#10b981';

  return (
    <div style={{ maxWidth: 1200 }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 800, color: 'var(--color-text-primary)', marginBottom: 4 }}>
          Dashboard Overview
        </h1>
        <p style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>
          Real-time parking status across all 3 floors • {new Date().toLocaleString()}
        </p>
      </div>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        <KpiCard
          label="Total Slots"
          value={String(avail?.total_slots ?? '—')}
          icon="🅿️"
          color="#2563eb"
          sub="3 floors"
        />
        <KpiCard
          label="Available"
          value={String(avail?.available ?? '—')}
          icon="✅"
          color="#10b981"
          sub={`${avail ? (100 - avail.occupancy_percentage).toFixed(1) : 0}% free`}
        />
        <KpiCard
          label="Occupied"
          value={String(avail?.occupied ?? '—')}
          icon="🚗"
          color="#ef4444"
          sub={`${avail?.occupancy_percentage ?? 0}% full`}
        />
        <KpiCard
          label="Reserved"
          value={String(avail?.reserved ?? '—')}
          icon="📋"
          color="#3b82f6"
          sub="Active reservations"
        />
      </div>

      {/* Occupancy Bar + Demo */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16, marginBottom: 24 }}>
        {/* Occupancy Overview */}
        <div className="card" style={{ padding: 24 }}>
          <div style={{ fontWeight: 700, marginBottom: 16, fontSize: 15 }}>Floor Occupancy</div>
          {avail?.floors.map((floor) => (
            <div key={floor.floor_number} style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span style={{ fontWeight: 600, fontSize: 13 }}>Floor {floor.floor_number}</span>
                <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
                  {floor.available} available / {floor.total} total
                </span>
              </div>
              <div style={{ height: 10, background: '#f1f5f9', borderRadius: 99, overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  width: `${floor.occupancy_percentage}%`,
                  background: floor.occupancy_percentage > 80 ? '#ef4444'
                    : floor.occupancy_percentage > 50 ? '#f59e0b' : '#10b981',
                  borderRadius: 99,
                  transition: 'width 0.5s ease',
                }} />
              </div>
              <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 4 }}>
                {floor.occupancy_percentage}% occupied
              </div>
            </div>
          ))}
          <button
            className="btn btn-primary"
            style={{ marginTop: 8, width: '100%' }}
            onClick={() => setCurrentPage('map')}
          >
            🗺 View Live Map
          </button>
        </div>

        {/* Simulator Panel */}
        <div className="card" style={{ padding: 24 }}>
          <div style={{ fontWeight: 700, marginBottom: 12, fontSize: 15 }}>IoT Simulator</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <span className={`connection-dot ${simStatus?.running ? 'connected' : 'disconnected'}`} />
            <span style={{ fontSize: 13, fontWeight: 600 }}>
              {simStatus?.running ? `Running — ${simStatus.mode}` : 'Idle'}
            </span>
          </div>
          {simStatus && (
            <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 16 }}>
              <div>🎯 {simStatus.total_sensors} virtual sensors</div>
              <div>📡 {simStatus.online_sensors} online</div>
              <div>🔄 {simStatus.total_events} events fired</div>
              {simStatus.last_event_at && (
                <div>🕒 Last: {new Date(simStatus.last_event_at).toLocaleTimeString()}</div>
              )}
            </div>
          )}
          <button className="btn btn-success" style={{ width: '100%', marginBottom: 8 }} onClick={handleStartDemo}>
            ▶ Start Demo
          </button>
          <button
            className="btn btn-outline"
            style={{ width: '100%', fontSize: 12 }}
            onClick={() => setCurrentPage('iot')}
          >
            Manage Sensors →
          </button>
        </div>
      </div>

      {/* Quick Actions + Recent Events */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {/* Quick Actions */}
        <div className="card" style={{ padding: 24 }}>
          <div style={{ fontWeight: 700, marginBottom: 16, fontSize: 15 }}>Quick Actions</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <QuickAction
              icon="🗺"
              label="Browse Parking Map"
              desc="View all slots across 3 floors"
              onClick={() => setCurrentPage('map')}
            />
            <QuickAction
              icon="🧭"
              label="Get AI Navigation"
              desc="Route to nearest available slot"
              onClick={() => setCurrentPage('navigation')}
            />
            <QuickAction
              icon="📋"
              label="Make a Reservation"
              desc="Reserve a slot for up to 2 hours"
              onClick={() => setCurrentPage('reservations')}
            />
            <QuickAction
              icon="📊"
              label="View Analytics"
              desc="Occupancy trends and statistics"
              onClick={() => setCurrentPage('analytics')}
            />
          </div>
        </div>

        {/* Recent Events */}
        <div className="card" style={{ padding: 24 }}>
          <div style={{ fontWeight: 700, marginBottom: 16, fontSize: 15 }}>Recent Activity (1h)</div>
          {recentEvents.length === 0 ? (
            <div style={{ color: 'var(--color-text-muted)', fontSize: 13, textAlign: 'center', padding: '20px 0' }}>
              No events yet. Start the IoT simulator to see live updates.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {recentEvents.map((event, i) => (
                <div key={i} style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '8px 12px',
                  background: event.occupancy_state === 'occupied' ? '#fff1f2' : '#f0fdf4',
                  borderRadius: 8,
                }}>
                  <span style={{ fontSize: 16 }}>
                    {event.occupancy_state === 'occupied' ? '🚗' : '✅'}
                  </span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 600 }}>{(event as any).slot_code || 'Unknown'}</div>
                    <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                      Floor {(event as any).floor_number} • {event.source}
                    </div>
                  </div>
                  <span className={`badge badge-${event.occupancy_state}`}>
                    {event.occupancy_state}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function KpiCard({ label, value, icon, color, sub }: {
  label: string; value: string; icon: string; color: string; sub: string;
}) {
  return (
    <div className="kpi-card" style={{ borderTop: `3px solid ${color}` }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
        <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          {label}
        </span>
        <span style={{ fontSize: 20 }}>{icon}</span>
      </div>
      <div style={{ fontSize: 32, fontWeight: 800, color: 'var(--color-text-primary)', lineHeight: 1 }}>{value}</div>
      <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 6 }}>{sub}</div>
    </div>
  );
}

function QuickAction({ icon, label, desc, onClick }: {
  icon: string; label: string; desc: string; onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="card-hover"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '12px 14px',
        border: '1px solid var(--color-border)',
        borderRadius: 10,
        background: 'var(--color-surface-subtle)',
        cursor: 'pointer',
        textAlign: 'left',
        width: '100%',
      }}
    >
      <span style={{ fontSize: 22 }}>{icon}</span>
      <div>
        <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--color-text-primary)' }}>{label}</div>
        <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>{desc}</div>
      </div>
      <span style={{ marginLeft: 'auto', color: 'var(--color-text-muted)' }}>→</span>
    </button>
  );
}
