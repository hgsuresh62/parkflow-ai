'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import type { FloorAvailability, SensorEvent, SlotStatus } from '@/types';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, Legend,
} from 'recharts';

interface Props {
  slotUpdates: Record<string, SlotStatus>;
  addToast: (title: string, message: string, type?: 'success' | 'info' | 'warning' | 'error') => void;
  selectedSlot: string | null;
  setSelectedSlot: (slot: string | null) => void;
  activeRoute: string | null;
  setActiveRoute: (route: string | null) => void;
  setCurrentPage: (page: any) => void;
}

const PIE_COLORS = ['#10b981', '#ef4444', '#3b82f6', '#f59e0b'];

export default function AnalyticsPage({ addToast }: Props) {
  const [floorData, setFloorData] = useState<FloorAvailability[]>([]);
  const [activity, setActivity] = useState<SensorEvent[]>([]);
  const [hourly, setHourly] = useState<Array<{ hour: string; occupied: number; available: number; total: number }>>([]);
  const [overview, setOverview] = useState<{
    total_slots: number; available: number; occupied: number; reserved: number;
    occupancy_percentage: number; recent_events_1h: number;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [hours, setHours] = useState(12);

  const fetchData = useCallback(async () => {
    try {
      const [floors, act, hrly, ovr] = await Promise.all([
        api.analytics.floors(),
        api.analytics.activity(hours, 50),
        api.analytics.hourly(hours),
        api.analytics.overview(),
      ]);
      setFloorData(floors.floors);
      setActivity(act.activity);
      setHourly(hrly.hourly);
      setOverview(ovr);
    } catch {
      addToast('Error', 'Failed to load analytics data', 'error');
    } finally {
      setLoading(false);
    }
  }, [hours, addToast]);

  useEffect(() => {
    fetchData();
    const timer = setInterval(fetchData, 15000);
    return () => clearInterval(timer);
  }, [fetchData]);

  const floorChartData = floorData.map((f) => ({
    name: `Floor ${f.floor_number}`,
    Available: f.available,
    Occupied: f.occupied,
    Reserved: f.reserved,
  }));

  const pieData = overview ? [
    { name: 'Available', value: overview.available },
    { name: 'Occupied', value: overview.occupied },
    { name: 'Reserved', value: overview.reserved },
  ].filter((d) => d.value > 0) : [];

  const hourlyChartData = hourly.map((h) => ({
    ...h,
    hour: new Date(h.hour).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  }));

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 60, color: 'var(--color-text-muted)' }}>Loading analytics...</div>;
  }

  return (
    <div style={{ maxWidth: 1100 }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 800, marginBottom: 4 }}>Analytics</h1>
        <p style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>
          Real-time parking occupancy trends and event statistics
        </p>
      </div>

      {/* Overview KPIs */}
      {overview && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 14, marginBottom: 24 }}>
          {[
            { label: 'Total Slots', value: overview.total_slots, color: '#2563eb' },
            { label: 'Available', value: overview.available, color: '#10b981' },
            { label: 'Occupied', value: overview.occupied, color: '#ef4444' },
            { label: 'Reserved', value: overview.reserved, color: '#3b82f6' },
            { label: 'Events (1h)', value: overview.recent_events_1h, color: '#f59e0b' },
          ].map((kpi) => (
            <div key={kpi.label} className="kpi-card" style={{ borderTop: `3px solid ${kpi.color}` }}>
              <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>
                {kpi.label}
              </div>
              <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--color-text-primary)' }}>{kpi.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Chart row 1 */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16, marginBottom: 16 }}>
        {/* Floor Bar Chart */}
        <div className="card" style={{ padding: 24 }}>
          <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 16 }}>Floor Occupancy Breakdown</div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={floorChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="Available" fill="#10b981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Occupied" fill="#ef4444" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Reserved" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Pie Chart */}
        <div className="card" style={{ padding: 24 }}>
          <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 16 }}>Overall Distribution</div>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {pieData.map((_, index) => (
                    <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ textAlign: 'center', padding: 40, color: 'var(--color-text-muted)' }}>No data</div>
          )}
        </div>
      </div>

      {/* Hourly Timeline */}
      <div className="card" style={{ padding: 24, marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <div style={{ fontWeight: 700, fontSize: 15 }}>Event Timeline</div>
          <div style={{ display: 'flex', gap: 6 }}>
            {[6, 12, 24].map((h) => (
              <button
                key={h}
                onClick={() => setHours(h)}
                style={{
                  padding: '4px 12px',
                  borderRadius: 6,
                  border: '1px solid var(--color-border)',
                  fontSize: 12,
                  cursor: 'pointer',
                  background: hours === h ? '#2563eb' : 'var(--color-surface)',
                  color: hours === h ? 'white' : 'var(--color-text-secondary)',
                }}
              >
                {h}h
              </button>
            ))}
            <button className="btn btn-outline" style={{ fontSize: 11, padding: '4px 10px' }} onClick={fetchData}>↻</button>
          </div>
        </div>
        {hourlyChartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={hourlyChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="hour" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line type="monotone" dataKey="occupied" stroke="#ef4444" dot={false} strokeWidth={2} />
              <Line type="monotone" dataKey="available" stroke="#10b981" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div style={{ textAlign: 'center', padding: 40, color: 'var(--color-text-muted)' }}>
            No event data yet. Start the IoT simulator to generate activity.
          </div>
        )}
      </div>

      {/* Recent Activity Table */}
      <div className="card" style={{ padding: 24 }}>
        <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 16 }}>Recent Sensor Events</div>
        {activity.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 20, color: 'var(--color-text-muted)' }}>
            No events recorded yet.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--color-border)' }}>
                  {['Slot', 'Floor', 'State', 'Source', 'Time'].map((h) => (
                    <th key={h} style={{ padding: '8px 12px', textAlign: 'left', fontSize: 11, fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {activity.slice(0, 20).map((ev, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--color-border)', transition: 'background 0.1s' }}>
                    <td style={{ padding: '8px 12px', fontWeight: 700, fontFamily: 'monospace' }}>{(ev as any).slot_code}</td>
                    <td style={{ padding: '8px 12px', color: 'var(--color-text-muted)' }}>F{(ev as any).floor_number}</td>
                    <td style={{ padding: '8px 12px' }}>
                      <span style={{
                        background: ev.occupancy_state === 'occupied' ? '#fee2e2' : '#d1fae5',
                        color: ev.occupancy_state === 'occupied' ? '#991b1b' : '#065f46',
                        padding: '2px 8px',
                        borderRadius: 99,
                        fontSize: 11,
                        fontWeight: 700,
                      }}>
                        {ev.occupancy_state}
                      </span>
                    </td>
                    <td style={{ padding: '8px 12px', color: 'var(--color-text-muted)', fontSize: 12 }}>{ev.source}</td>
                    <td style={{ padding: '8px 12px', color: 'var(--color-text-muted)', fontSize: 12 }}>
                      {new Date(ev.event_timestamp).toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
