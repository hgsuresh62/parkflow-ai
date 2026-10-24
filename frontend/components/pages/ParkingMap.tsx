'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import type { ParkingSlot, Floor, SlotStatus } from '@/types';
import type { PageId } from '@/app/page';

interface Props {
  slotUpdates: Record<string, SlotStatus>;
  addToast: (title: string, message: string, type?: 'success' | 'info' | 'warning' | 'error') => void;
  selectedSlot: string | null;
  setSelectedSlot: (slot: string | null) => void;
  activeRoute: string | null;
  setActiveRoute: (route: string | null) => void;
  setCurrentPage: (page: PageId) => void;
}

const STATUS_COLORS: Record<string, string> = {
  available: '#10b981',
  occupied: '#ef4444',
  reserved: '#3b82f6',
  pending: '#f59e0b',
  maintenance: '#94a3b8',
};

export default function ParkingMap({ slotUpdates, addToast, selectedSlot, setSelectedSlot, setCurrentPage }: Props) {
  const [floors, setFloors] = useState<Floor[]>([]);
  const [activeFloor, setActiveFloor] = useState(1);
  const [slots, setSlots] = useState<ParkingSlot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredSlot, setHoveredSlot] = useState<string | null>(null);

  const fetchFloors = useCallback(async () => {
    try {
      const res = await api.floors.list();
      setFloors(res.floors);
      setError(null);
    } catch {
      setError('Failed to load floor data');
    }
  }, []);

  const fetchSlots = useCallback(async () => {
    try {
      const res = await api.slots.list({ floor_number: activeFloor });
      setSlots(res.slots);
    } catch {
      setError('Failed to load slots');
    } finally {
      setLoading(false);
    }
  }, [activeFloor]);

  useEffect(() => {
    fetchFloors();
  }, [fetchFloors]);

  useEffect(() => {
    setLoading(true);
    fetchSlots();
    const timer = setInterval(fetchSlots, 8000);
    return () => clearInterval(timer);
  }, [fetchSlots]);

  // Merge live WebSocket updates into local slot state
  const mergedSlots = slots.map((slot) => ({
    ...slot,
    status: (slotUpdates[slot.slot_code] ?? slot.status) as SlotStatus,
  }));

  const floorSlots = mergedSlots;

  // Group by row
  const rows = floorSlots.reduce<Record<string, ParkingSlot[]>>((acc, slot) => {
    const row = slot.row_label || 'A';
    if (!acc[row]) acc[row] = [];
    acc[row].push(slot);
    return acc;
  }, {});

  const currentFloor = floors.find((f) => f.floor_number === activeFloor);
  const available = floorSlots.filter((s) => s.status === 'available').length;
  const occupied = floorSlots.filter((s) => s.status === 'occupied').length;
  const reserved = floorSlots.filter((s) => s.status === 'reserved').length;

  const handleSlotClick = (slot: ParkingSlot) => {
    if (slot.status === 'occupied') {
      addToast('Slot Occupied', `${slot.slot_code} is currently occupied.`, 'warning');
      return;
    }
    if (selectedSlot === slot.slot_code) {
      setSelectedSlot(null);
    } else {
      setSelectedSlot(slot.slot_code);
      addToast('Slot Selected', `${slot.slot_code} selected. Navigate or reserve it.`, 'info');
    }
  };

  const handleNavigate = () => {
    if (selectedSlot) {
      setCurrentPage('navigation');
    }
  };

  const handleReserve = async () => {
    if (!selectedSlot) return;
    try {
      const res = await api.reservations.create(selectedSlot);
      addToast('Reserved!', `${res.reservation_code} — ${selectedSlot} reserved for 30 min`, 'success');
      fetchSlots();
      setSelectedSlot(null);
    } catch (e: any) {
      addToast('Reservation Failed', e.message || 'Could not reserve slot', 'error');
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 400 }}>
        <div style={{ color: 'var(--color-text-muted)' }}>Loading parking map...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: 40 }}>
        <div style={{ color: '#ef4444', marginBottom: 12 }}>{error}</div>
        <button className="btn btn-primary" onClick={() => { fetchFloors(); fetchSlots(); }}>Retry</button>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 1200 }}>
      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 22, fontWeight: 800, marginBottom: 4 }}>Live Parking Map</h1>
        <p style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>
          Interactive map — click an available slot to select it
        </p>
      </div>

      {/* Floor selector */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        {[1, 2, 3].map((f) => {
          const fd = floors.find((fl) => fl.floor_number === f);
          return (
            <button
              key={f}
              className={`floor-tab ${activeFloor === f ? 'active' : ''}`}
              onClick={() => setActiveFloor(f)}
            >
              Floor {f}
              {fd && (
                <span style={{ marginLeft: 6, fontSize: 11, opacity: 0.8 }}>
                  ({fd.available_slots ?? available} free)
                </span>
              )}
            </button>
          );
        })}
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 12, alignItems: 'center' }}>
          <Legend color="#10b981" label="Available" />
          <Legend color="#ef4444" label="Occupied" />
          <Legend color="#3b82f6" label="Reserved" />
          <Legend color="#1d4ed8" label="Selected" />
        </div>
      </div>

      {/* Stats bar */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
        <Stat label="Available" value={available} color="#10b981" />
        <Stat label="Occupied" value={occupied} color="#ef4444" />
        <Stat label="Reserved" value={reserved} color="#3b82f6" />
        <Stat label="Total" value={floorSlots.length} color="var(--color-text-primary)" />
      </div>

      {/* Map Grid */}
      <div className="card" style={{ padding: 24, marginBottom: 16 }}>
        <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 16, color: 'var(--color-text-secondary)' }}>
          {currentFloor?.name || `Floor ${activeFloor}`}
          {currentFloor?.description && (
            <span style={{ fontWeight: 400, marginLeft: 8, fontSize: 12 }}> — {currentFloor.description}</span>
          )}
        </div>

        {/* Entrance / Ramp indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20, padding: '8px 16px', background: '#f8fafc', borderRadius: 8 }}>
          {activeFloor === 1 && <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>🚪 ENTRANCE ←</span>}
          {activeFloor > 1 && <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>↑ RAMP FROM FLOOR {activeFloor - 1}</span>}
          <div style={{ flex: 1, height: 2, background: '#e2e8f0', borderRadius: 99 }} />
          {activeFloor < 3 && <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>RAMP TO FLOOR {activeFloor + 1} →</span>}
          {activeFloor === 1 && <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>🚪 EXIT →</span>}
        </div>

        {/* Slot rows */}
        {Object.entries(rows).sort().map(([rowLabel, rowSlots]) => (
          <div key={rowLabel} style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--color-text-muted)', marginBottom: 8, letterSpacing: '0.08em' }}>
              ROW {rowLabel}
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {rowSlots.sort((a, b) => a.slot_code.localeCompare(b.slot_code)).map((slot) => {
                const isSelected = selectedSlot === slot.slot_code;
                const isHovered = hoveredSlot === slot.slot_code;
                const bgColor = isSelected ? '#1d4ed8' : STATUS_COLORS[slot.status] || '#94a3b8';
                return (
                  <button
                    key={slot.slot_code}
                    title={`${slot.slot_code} — ${slot.status} — ${slot.slot_type}`}
                    onClick={() => handleSlotClick(slot)}
                    onMouseEnter={() => setHoveredSlot(slot.slot_code)}
                    onMouseLeave={() => setHoveredSlot(null)}
                    style={{
                      width: 52,
                      height: 36,
                      borderRadius: 6,
                      background: bgColor,
                      border: isSelected ? '2px solid #1e40af' : '1px solid rgba(0,0,0,0.1)',
                      color: 'white',
                      fontSize: 9,
                      fontWeight: 700,
                      cursor: slot.status === 'occupied' ? 'not-allowed' : 'pointer',
                      opacity: isHovered && !isSelected ? 0.85 : 1,
                      transform: isSelected ? 'scale(1.08)' : 'scale(1)',
                      transition: 'all 0.15s',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: 2,
                      lineHeight: 1.1,
                    }}
                  >
                    <span>{slot.slot_code.split('-')[1]}</span>
                    {slot.slot_type === 'accessible' && <span style={{ fontSize: 8 }}>♿</span>}
                    {slot.slot_type === 'ev_charging' && <span style={{ fontSize: 8 }}>⚡</span>}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Action panel for selected slot */}
      {selectedSlot && (
        <div className="card" style={{
          padding: 20,
          border: '2px solid #2563eb',
          display: 'flex',
          alignItems: 'center',
          gap: 16,
        }}>
          <div style={{ fontSize: 28 }}>🎯</div>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 700, fontSize: 15 }}>Selected: {selectedSlot}</div>
            <div style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>
              {floorSlots.find((s) => s.slot_code === selectedSlot)?.slot_type} slot on Floor {activeFloor}
            </div>
          </div>
          <button className="btn btn-primary" onClick={handleNavigate}>
            🧭 Navigate Here
          </button>
          <button className="btn btn-success" onClick={handleReserve}>
            📋 Reserve Slot
          </button>
          <button className="btn btn-outline" onClick={() => setSelectedSlot(null)}>
            ✕ Clear
          </button>
        </div>
      )}
    </div>
  );
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
      <div style={{ width: 12, height: 12, borderRadius: 3, background: color }} />
      <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>{label}</span>
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 8,
      padding: '8px 16px',
      display: 'flex',
      alignItems: 'center',
      gap: 8,
    }}>
      <span style={{ fontWeight: 800, fontSize: 18, color }}>{value}</span>
      <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>{label}</span>
    </div>
  );
}
