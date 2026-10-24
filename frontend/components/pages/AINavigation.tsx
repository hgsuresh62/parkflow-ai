'use client';

import { useState, useCallback, useEffect } from 'react';
import { api } from '@/lib/api';
import type { RouteResult, AlternativeSlot, NavigationInstruction, SlotStatus } from '@/types';
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

const SOURCE_NODES = [
  { value: 'ENTRANCE', label: '🚪 Main Entrance' },
  { value: 'F1_ENTRY', label: '1F Entry' },
  { value: 'F2_RAMP_DOWN', label: '2F Ramp Entry' },
  { value: 'F3_RAMP_DOWN', label: '3F Ramp Entry' },
];

const DEMO_DESTINATIONS = [
  'F1-A05', 'F1-B10', 'F2-B05', 'F2-C08', 'F3-C03', 'F3-D12',
];

const EDGE_ICONS: Record<string, string> = {
  straight: '⬆',
  turn_left: '↰',
  turn_right: '↱',
  ramp: '🏔',
  park: '🅿',
};

export default function AINavigation({
  addToast,
  selectedSlot,
  setSelectedSlot,
  setActiveRoute,
}: Props) {
  const [source, setSource] = useState('ENTRANCE');
  const [destination, setDestination] = useState('');
  const [route, setRoute] = useState<RouteResult | null>(null);
  const [alternatives, setAlternatives] = useState<AlternativeSlot[]>([]);
  const [loading, setLoading] = useState(false);
  const [availableSlots, setAvailableSlots] = useState<string[]>([]);
  const [step, setStep] = useState(0);
  const [animating, setAnimating] = useState(false);

  useEffect(() => {
    // Preload some available slots for quick selection
    api.slots.availability().then((avail) => {
      api.routes.alternatives('', source).then((data) => {
        setAvailableSlots(data.alternatives.map((a) => a.slot_code));
      }).catch(() => {
        setAvailableSlots(DEMO_DESTINATIONS);
      });
    }).catch(() => {
      setAvailableSlots(DEMO_DESTINATIONS);
    });
  }, [source]);

  useEffect(() => {
    if (selectedSlot) {
      setDestination(selectedSlot);
    }
  }, [selectedSlot]);

  const handleCalculate = async () => {
    if (!destination) {
      addToast('Select Destination', 'Please enter or select a destination slot', 'warning');
      return;
    }

    setLoading(true);
    setRoute(null);
    setAlternatives([]);
    setStep(0);

    try {
      const result = await api.routes.calculate(source, destination);
      setRoute(result);
      setActiveRoute(result.route_id);
      addToast('Route Calculated', `${result.estimated_time_seconds}s to ${destination}`, 'success');
    } catch (e: any) {
      // Handle 409 conflict (slot occupied) — show alternatives
      if (e.message?.includes('409')) {
        addToast('Slot Occupied', 'Finding alternatives...', 'warning');
        try {
          const altData = await api.routes.alternatives('', source);
          setAlternatives(altData.alternatives);
        } catch {
          addToast('Error', 'Failed to find alternatives', 'error');
        }
      } else {
        addToast('Routing Failed', e.message || 'Could not calculate route', 'error');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRecalculate = async () => {
    if (!route) return;
    setLoading(true);
    try {
      const result = await api.routes.recalculate(route.route_id, source);
      setRoute(result);
      setActiveRoute(result.route_id);
      addToast('Rerouted', `New destination: ${result.destination_slot}`, 'info');
    } catch (e: any) {
      addToast('Rerouting Failed', e.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleAlternativeSelect = (slot: string) => {
    setDestination(slot);
    setAlternatives([]);
  };

  const handleNavigationStep = () => {
    if (!route) return;
    if (step < route.instructions.length - 1) {
      setStep((s) => s + 1);
    }
  };

  const startAnimation = () => {
    if (!route || animating) return;
    setAnimating(true);
    setStep(0);
    let i = 0;
    const interval = setInterval(() => {
      i++;
      setStep(i);
      if (i >= route.instructions.length - 1) {
        clearInterval(interval);
        setAnimating(false);
        addToast('Arrived!', `You have arrived at ${route.destination_slot}`, 'success');
      }
    }, 1500);
  };

  const currentInstruction = route?.instructions[step];

  return (
    <div style={{ maxWidth: 1000 }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 800, marginBottom: 4 }}>AI Navigation</h1>
        <p style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>
          Dijkstra's shortest-path algorithm routes you to your parking slot
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: 20 }}>
        {/* Input Panel */}
        <div>
          <div className="card" style={{ padding: 24, marginBottom: 16 }}>
            <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 16 }}>Route Planner</div>

            <div style={{ marginBottom: 14 }}>
              <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', display: 'block', marginBottom: 6 }}>
                FROM (Source Node)
              </label>
              <select
                value={source}
                onChange={(e) => setSource(e.target.value)}
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  border: '1px solid var(--color-border)',
                  borderRadius: 8,
                  fontSize: 13,
                  color: 'var(--color-text-primary)',
                  background: 'var(--color-surface)',
                }}
              >
                {SOURCE_NODES.map((n) => (
                  <option key={n.value} value={n.value}>{n.label}</option>
                ))}
              </select>
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', display: 'block', marginBottom: 6 }}>
                TO (Destination Slot)
              </label>
              <input
                type="text"
                value={destination}
                onChange={(e) => setDestination(e.target.value.toUpperCase())}
                placeholder="e.g. F2-B05"
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  border: '1px solid var(--color-border)',
                  borderRadius: 8,
                  fontSize: 13,
                  color: 'var(--color-text-primary)',
                  outline: 'none',
                }}
              />
              <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {availableSlots.slice(0, 6).map((slot) => (
                  <button
                    key={slot}
                    onClick={() => setDestination(slot)}
                    style={{
                      padding: '3px 8px',
                      fontSize: 11,
                      border: '1px solid var(--color-border)',
                      borderRadius: 6,
                      cursor: 'pointer',
                      background: destination === slot ? '#eff6ff' : 'var(--color-surface)',
                      color: destination === slot ? '#2563eb' : 'var(--color-text-muted)',
                      fontWeight: 600,
                    }}
                  >
                    {slot}
                  </button>
                ))}
              </div>
            </div>

            <button
              className="btn btn-primary"
              style={{ width: '100%', justifyContent: 'center' }}
              onClick={handleCalculate}
              disabled={loading || !destination}
            >
              {loading ? '⟳ Calculating...' : '🧭 Calculate Route'}
            </button>

            {route && (
              <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                <button
                  className="btn btn-outline"
                  style={{ flex: 1, justifyContent: 'center', fontSize: 12 }}
                  onClick={handleRecalculate}
                  disabled={loading}
                >
                  ♻ Recalculate
                </button>
                <button
                  className="btn btn-success"
                  style={{ flex: 1, justifyContent: 'center', fontSize: 12 }}
                  onClick={startAnimation}
                  disabled={animating}
                >
                  ▶ Simulate Drive
                </button>
              </div>
            )}
          </div>

          {/* Route Summary */}
          {route && (
            <div className="card" style={{ padding: 20 }}>
              <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 14, color: 'var(--color-text-primary)' }}>
                Route Summary
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <SummaryItem icon="🎯" label="Destination" value={route.destination_slot} />
                <SummaryItem icon="📏" label="Distance" value={`${route.distance_m}m`} />
                <SummaryItem
                  icon="⏱"
                  label="Est. Time"
                  value={`${route.estimated_time_seconds}s (~${Math.ceil(route.estimated_time_seconds / 60)} min)`}
                />
                <SummaryItem icon="📍" label="Steps" value={`${route.instructions.length} steps`} />
                {route.floor_changes.length > 0 && (
                  <SummaryItem
                    icon="🏔"
                    label="Floor Changes"
                    value={route.floor_changes.map((fc) => `F${fc.from_floor}→F${fc.to_floor}`).join(', ')}
                  />
                )}
              </div>
            </div>
          )}

          {/* Alternatives */}
          {alternatives.length > 0 && (
            <div className="card" style={{ padding: 20, marginTop: 16 }}>
              <div style={{ fontWeight: 700, marginBottom: 12 }}>Available Alternatives</div>
              {alternatives.map((alt) => (
                <button
                  key={alt.slot_code}
                  onClick={() => handleAlternativeSelect(alt.slot_code)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    width: '100%',
                    padding: '10px 12px',
                    marginBottom: 8,
                    border: '1px solid var(--color-border)',
                    borderRadius: 8,
                    background: 'var(--color-surface-subtle)',
                    cursor: 'pointer',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 13 }}>{alt.slot_code}</div>
                    <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>Floor {alt.floor} • {alt.distance_m}m</div>
                  </div>
                  <span style={{ fontSize: 12, color: '#10b981', fontWeight: 700 }}>~{alt.estimated_time_seconds}s</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Instructions Panel */}
        <div>
          {route ? (
            <div className="card" style={{ padding: 24 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                <div style={{ fontWeight: 700, fontSize: 15 }}>Turn-by-Turn Instructions</div>
                <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
                  Step {step + 1} / {route.instructions.length}
                </span>
              </div>

              {/* Current step highlight */}
              {currentInstruction && (
                <div style={{
                  background: 'linear-gradient(135deg, #eff6ff, #dbeafe)',
                  border: '2px solid #2563eb',
                  borderRadius: 12,
                  padding: 20,
                  marginBottom: 16,
                  textAlign: 'center',
                }}>
                  <div style={{ fontSize: 36, marginBottom: 8 }}>
                    {EDGE_ICONS[currentInstruction.edge_type] || '⬆'}
                  </div>
                  <div style={{ fontWeight: 700, fontSize: 16, color: '#1d4ed8', marginBottom: 4 }}>
                    {currentInstruction.instruction}
                  </div>
                  <div style={{ fontSize: 12, color: '#3b82f6' }}>
                    Floor {currentInstruction.floor}
                    {currentInstruction.floor_change && ` → Floor ${currentInstruction.to_floor}`}
                  </div>
                </div>
              )}

              <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                <button
                  className="btn btn-outline"
                  style={{ flex: 1, justifyContent: 'center' }}
                  onClick={() => setStep((s) => Math.max(0, s - 1))}
                  disabled={step === 0 || animating}
                >
                  ← Prev
                </button>
                <button
                  className="btn btn-primary"
                  style={{ flex: 1, justifyContent: 'center' }}
                  onClick={handleNavigationStep}
                  disabled={step >= route.instructions.length - 1 || animating}
                >
                  Next →
                </button>
              </div>

              {/* All steps list */}
              <div style={{ maxHeight: 350, overflowY: 'auto' }}>
                {route.instructions.map((instr: NavigationInstruction, i: number) => (
                  <div
                    key={i}
                    onClick={() => !animating && setStep(i)}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: 12,
                      padding: '10px 12px',
                      borderRadius: 8,
                      marginBottom: 6,
                      cursor: animating ? 'default' : 'pointer',
                      background: i === step ? '#eff6ff' : 'transparent',
                      border: i === step ? '1px solid #bfdbfe' : '1px solid transparent',
                      transition: 'all 0.15s',
                    }}
                  >
                    <div style={{
                      width: 28,
                      height: 28,
                      borderRadius: '50%',
                      background: i === step ? '#2563eb' : i < step ? '#10b981' : '#e2e8f0',
                      color: i <= step ? 'white' : 'var(--color-text-muted)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: 11,
                      fontWeight: 700,
                      flexShrink: 0,
                    }}>
                      {i < step ? '✓' : String(instr.step)}
                    </div>
                    <div style={{ flex: 1, paddingTop: 2 }}>
                      <div style={{
                        fontSize: 13,
                        color: i === step ? '#1d4ed8' : 'var(--color-text-primary)',
                        fontWeight: i === step ? 600 : 400,
                        lineHeight: 1.4,
                      }}>
                        {instr.instruction}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 2 }}>
                        Floor {instr.floor} • {EDGE_ICONS[instr.edge_type]} {instr.edge_type}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="card" style={{ padding: 40, textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ fontSize: 64, marginBottom: 16 }}>🧭</div>
              <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 8 }}>AI Navigation Ready</div>
              <div style={{ color: 'var(--color-text-muted)', fontSize: 14, maxWidth: 280, lineHeight: 1.6 }}>
                Select a starting point and destination slot, then click Calculate Route to get Dijkstra-powered turn-by-turn directions.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SummaryItem({ icon, label, value }: { icon: string; label: string; value: string }) {
  return (
    <div style={{
      padding: '10px 12px',
      background: 'var(--color-surface-subtle)',
      borderRadius: 8,
    }}>
      <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 4 }}>{icon} {label}</div>
      <div style={{ fontWeight: 700, fontSize: 13 }}>{value}</div>
    </div>
  );
}
