'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import type { Reservation, SlotStatus } from '@/types';
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

export default function ReservationsPage({ addToast, selectedSlot, setSelectedSlot }: Props) {
  const [reservations, setReservations] = useState<(Reservation & { slot_code: string })[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [slotCode, setSlotCode] = useState('');
  const [duration, setDuration] = useState(30);
  const [userSession, setUserSession] = useState('guest-user');
  const [filter, setFilter] = useState<string>('');

  const fetchReservations = useCallback(async () => {
    try {
      const res = await api.reservations.list(filter || undefined);
      setReservations(res.reservations as (Reservation & { slot_code: string })[]);
    } catch {
      addToast('Error', 'Failed to load reservations', 'error');
    } finally {
      setLoading(false);
    }
  }, [filter, addToast]);

  useEffect(() => {
    if (selectedSlot) setSlotCode(selectedSlot);
  }, [selectedSlot]);

  useEffect(() => {
    fetchReservations();
    const timer = setInterval(fetchReservations, 15000);
    return () => clearInterval(timer);
  }, [fetchReservations]);

  const handleCreate = async () => {
    if (!slotCode.trim()) {
      addToast('Missing Slot', 'Please enter a slot code', 'warning');
      return;
    }
    setCreating(true);
    try {
      const res = await api.reservations.create(slotCode.toUpperCase(), userSession);
      addToast('Reserved!', `${res.reservation_code} — valid for ${duration} minutes`, 'success');
      setSlotCode('');
      setSelectedSlot(null);
      fetchReservations();
    } catch (e: any) {
      addToast('Reservation Failed', e.message || 'Could not create reservation', 'error');
    } finally {
      setCreating(false);
    }
  };

  const handleCancel = async (id: string, code: string) => {
    try {
      await api.reservations.cancel(id);
      addToast('Cancelled', `Reservation ${code} has been cancelled`, 'info');
      fetchReservations();
    } catch (e: any) {
      addToast('Error', e.message || 'Failed to cancel reservation', 'error');
    }
  };

  const getTimeRemaining = (expiresAt: string) => {
    const diff = new Date(expiresAt).getTime() - Date.now();
    if (diff <= 0) return 'Expired';
    const mins = Math.floor(diff / 60000);
    const secs = Math.floor((diff % 60000) / 1000);
    return `${mins}m ${secs}s`;
  };

  const statusBadge = (status: string) => {
    const colors: Record<string, string> = {
      active: '#10b981',
      expired: '#94a3b8',
      cancelled: '#ef4444',
      fulfilled: '#2563eb',
    };
    return (
      <span style={{
        background: colors[status] + '20',
        color: colors[status],
        padding: '3px 10px',
        borderRadius: 99,
        fontSize: 11,
        fontWeight: 700,
      }}>
        {status.toUpperCase()}
      </span>
    );
  };

  return (
    <div style={{ maxWidth: 900 }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 800, marginBottom: 4 }}>Reservations</h1>
        <p style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>
          Reserve a parking slot for up to 2 hours
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 20 }}>
        {/* Create Form */}
        <div className="card" style={{ padding: 24, alignSelf: 'start' }}>
          <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 16 }}>New Reservation</div>

          <div style={{ marginBottom: 14 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', display: 'block', marginBottom: 6 }}>
              SLOT CODE
            </label>
            <input
              type="text"
              value={slotCode}
              onChange={(e) => setSlotCode(e.target.value.toUpperCase())}
              placeholder="e.g. F1-A05"
              style={{
                width: '100%',
                padding: '9px 12px',
                border: '1px solid var(--color-border)',
                borderRadius: 8,
                fontSize: 13,
              }}
            />
            {selectedSlot && (
              <div style={{ marginTop: 6, fontSize: 12, color: '#2563eb' }}>
                ← From map selection: {selectedSlot}
              </div>
            )}
          </div>

          <div style={{ marginBottom: 14 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', display: 'block', marginBottom: 6 }}>
              DURATION (minutes)
            </label>
            <select
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              style={{
                width: '100%',
                padding: '9px 12px',
                border: '1px solid var(--color-border)',
                borderRadius: 8,
                fontSize: 13,
                background: 'var(--color-surface)',
              }}
            >
              <option value={15}>15 minutes</option>
              <option value={30}>30 minutes</option>
              <option value={60}>1 hour</option>
              <option value={120}>2 hours</option>
            </select>
          </div>

          <div style={{ marginBottom: 20 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', display: 'block', marginBottom: 6 }}>
              USER / SESSION ID
            </label>
            <input
              type="text"
              value={userSession}
              onChange={(e) => setUserSession(e.target.value)}
              style={{
                width: '100%',
                padding: '9px 12px',
                border: '1px solid var(--color-border)',
                borderRadius: 8,
                fontSize: 13,
              }}
            />
          </div>

          <button
            className="btn btn-success"
            style={{ width: '100%', justifyContent: 'center' }}
            onClick={handleCreate}
            disabled={creating || !slotCode}
          >
            {creating ? '⟳ Creating...' : '📋 Reserve Slot'}
          </button>

          <div style={{ marginTop: 16, padding: 12, background: '#f0fdf4', borderRadius: 8, fontSize: 12, color: '#065f46' }}>
            <strong>Tips:</strong>
            <ul style={{ marginTop: 6, paddingLeft: 16 }}>
              <li>Select a slot from the Live Map first</li>
              <li>Reservation holds slot for selected duration</li>
              <li>System will auto-expire old reservations</li>
            </ul>
          </div>
        </div>

        {/* Reservations List */}
        <div>
          <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
            {['', 'active', 'expired', 'cancelled'].map((s) => (
              <button
                key={s}
                onClick={() => setFilter(s)}
                style={{
                  padding: '6px 14px',
                  borderRadius: 8,
                  border: '1px solid var(--color-border)',
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                  background: filter === s ? '#2563eb' : 'var(--color-surface)',
                  color: filter === s ? 'white' : 'var(--color-text-secondary)',
                }}
              >
                {s || 'All'}
              </button>
            ))}
            <button
              className="btn btn-outline"
              style={{ marginLeft: 'auto', fontSize: 12 }}
              onClick={fetchReservations}
            >
              ↻ Refresh
            </button>
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: 40, color: 'var(--color-text-muted)' }}>Loading...</div>
          ) : reservations.length === 0 ? (
            <div className="card" style={{ padding: 40, textAlign: 'center' }}>
              <div style={{ fontSize: 48, marginBottom: 12 }}>📋</div>
              <div style={{ fontWeight: 600, marginBottom: 8 }}>No Reservations</div>
              <div style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>
                Create your first reservation using the form on the left.
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {reservations.map((res) => (
                <div key={res.id} className="card" style={{
                  padding: 16,
                  borderLeft: `4px solid ${res.status === 'active' ? '#10b981' : res.status === 'cancelled' ? '#ef4444' : '#94a3b8'}`,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                    <div>
                      <span style={{ fontWeight: 800, fontSize: 15, fontFamily: 'monospace' }}>
                        {res.reservation_code}
                      </span>
                      <span style={{ marginLeft: 10 }}>{statusBadge(res.status)}</span>
                    </div>
                    {res.status === 'active' && (
                      <button
                        className="btn btn-danger"
                        style={{ fontSize: 11, padding: '4px 10px' }}
                        onClick={() => handleCancel(String(res.id), res.reservation_code)}
                      >
                        Cancel
                      </button>
                    )}
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, fontSize: 12 }}>
                    <div>
                      <span style={{ color: 'var(--color-text-muted)' }}>Slot:</span>{' '}
                      <strong>{res.slot_code}</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--color-text-muted)' }}>User:</span>{' '}
                      <strong>{res.user_session_id}</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--color-text-muted)' }}>Expires:</span>{' '}
                      <strong style={{ color: res.status === 'active' ? '#10b981' : 'inherit' }}>
                        {res.status === 'active' ? getTimeRemaining(res.expires_at) : new Date(res.expires_at).toLocaleTimeString()}
                      </strong>
                    </div>
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 8 }}>
                    Created: {new Date(res.created_at).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
