'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import type { Sensor, SimulatorStatus, SlotStatus } from '@/types';

interface Props {
  slotUpdates: Record<string, SlotStatus>;
  addToast: (title: string, message: string, type?: 'success' | 'info' | 'warning' | 'error') => void;
  selectedSlot: string | null;
  setSelectedSlot: (slot: string | null) => void;
  activeRoute: string | null;
  setActiveRoute: (route: string | null) => void;
  setCurrentPage: (page: any) => void;
}

export default function IoTSensorsPage({ addToast }: Props) {
  const [sensors, setSensors] = useState<(Sensor & { slot_code: string })[]>([]);
  const [simStatus, setSimStatus] = useState<SimulatorStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [interval, setIntervalS] = useState(5);
  const [triggerSlot, setTriggerSlot] = useState('');
  const [triggerType, setTriggerType] = useState<'arrive' | 'depart'>('arrive');
  const [searchFilter, setSearchFilter] = useState('');
  const [demoTarget, setDemoTarget] = useState('');

  const fetchData = useCallback(async () => {
    try {
      const [sensorData, sim] = await Promise.all([
        api.iot.sensors(),
        api.iot.simulator.status(),
      ]);
      setSensors(sensorData.sensors as (Sensor & { slot_code: string })[]);
      setSimStatus(sim);
    } catch {
      // Backend may not be running
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const timer = setInterval(fetchData, 6000);
    return () => clearInterval(timer);
  }, [fetchData]);

  const handleStart = async () => {
    try {
      await api.iot.simulator.start(interval);
      addToast('Simulator Started', `Running at ${interval}s interval`, 'success');
      fetchData();
    } catch (e: any) {
      addToast('Error', e.message, 'error');
    }
  };

  const handleStop = async () => {
    try {
      await api.iot.simulator.stop();
      addToast('Simulator Stopped', 'IoT simulation halted', 'info');
      fetchData();
    } catch (e: any) {
      addToast('Error', e.message, 'error');
    }
  };

  const handleDemo = async () => {
    try {
      const result = await api.iot.simulator.startDemo(demoTarget || undefined);
      addToast('Demo Mode', `Demo started — target: ${(result as any).target_slot}`, 'success');
      fetchData();
    } catch (e: any) {
      addToast('Error', e.message, 'error');
    }
  };

  const handleStress = async (enabled: boolean) => {
    try {
      await api.iot.simulator.stress(enabled);
      addToast(enabled ? 'Stress Mode ON' : 'Stress Mode OFF', enabled ? 'Rapid random changes active' : 'Normal mode restored', 'warning');
      fetchData();
    } catch (e: any) {
      addToast('Error', e.message, 'error');
    }
  };

  const handleTrigger = async () => {
    if (!triggerSlot.trim()) {
      addToast('Missing Slot', 'Enter a slot code to trigger', 'warning');
      return;
    }
    try {
      await api.iot.simulator.trigger(triggerSlot.toUpperCase(), triggerType);
      addToast('Event Triggered', `${triggerSlot} — ${triggerType}`, 'info');
      setTriggerSlot('');
      fetchData();
    } catch (e: any) {
      addToast('Trigger Failed', e.message, 'error');
    }
  };

  const filteredSensors = sensors.filter((s) =>
    !searchFilter || s.slot_code?.toLowerCase().includes(searchFilter.toLowerCase())
  );

  const online = sensors.filter((s) => s.status === 'online').length;

  return (
    <div style={{ maxWidth: 1100 }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 800, marginBottom: 4 }}>IoT Sensors</h1>
        <p style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>
          Virtual HC-SR04 ultrasonic sensor management and IoT simulator controls
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 20 }}>
        {/* Control Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Simulator Status */}
          <div className="card" style={{ padding: 20 }}>
            <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>Simulator Status</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <span className={`connection-dot ${simStatus?.running ? 'connected' : 'disconnected'}`} />
              <span style={{ fontWeight: 600, fontSize: 13 }}>
                {simStatus?.running ? `${simStatus.mode.toUpperCase()}` : 'IDLE'}
              </span>
            </div>
            {simStatus && (
              <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 12 }}>
                <div>📡 {simStatus.total_sensors} sensors</div>
                <div>✅ {simStatus.online_sensors} online</div>
                <div>🚗 {simStatus.occupied_count} occupied</div>
                <div>🔄 {simStatus.total_events} events</div>
              </div>
            )}

            <div style={{ marginBottom: 10 }}>
              <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)', display: 'block', marginBottom: 4 }}>
                INTERVAL (seconds)
              </label>
              <input
                type="number"
                min={1}
                max={60}
                value={interval}
                onChange={(e) => setIntervalS(Number(e.target.value))}
                style={{ width: '100%', padding: '6px 10px', border: '1px solid var(--color-border)', borderRadius: 6, fontSize: 13 }}
              />
            </div>

            {simStatus?.running ? (
              <button className="btn btn-danger" style={{ width: '100%', justifyContent: 'center', marginBottom: 6 }} onClick={handleStop}>
                ⏹ Stop Simulator
              </button>
            ) : (
              <button className="btn btn-success" style={{ width: '100%', justifyContent: 'center', marginBottom: 6 }} onClick={handleStart}>
                ▶ Start Simulator
              </button>
            )}

            <button
              className="btn btn-outline"
              style={{ width: '100%', justifyContent: 'center', marginBottom: 6, fontSize: 12 }}
              onClick={() => handleStress(simStatus?.mode !== 'stress')}
            >
              {simStatus?.mode === 'stress' ? '⚡ Stop Stress' : '⚡ Stress Mode'}
            </button>
          </div>

          {/* Demo Mode */}
          <div className="card" style={{ padding: 20 }}>
            <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>Demo Mode</div>
            <div style={{ marginBottom: 10 }}>
              <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)', display: 'block', marginBottom: 4 }}>
                TARGET SLOT (optional)
              </label>
              <input
                type="text"
                value={demoTarget}
                onChange={(e) => setDemoTarget(e.target.value.toUpperCase())}
                placeholder="e.g. F2-B05"
                style={{ width: '100%', padding: '6px 10px', border: '1px solid var(--color-border)', borderRadius: 6, fontSize: 13 }}
              />
            </div>
            <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }} onClick={handleDemo}>
              🎬 Start Demo Sequence
            </button>
          </div>

          {/* Manual Trigger */}
          <div className="card" style={{ padding: 20 }}>
            <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>Manual Trigger</div>
            <div style={{ marginBottom: 8 }}>
              <input
                type="text"
                value={triggerSlot}
                onChange={(e) => setTriggerSlot(e.target.value.toUpperCase())}
                placeholder="Slot code (e.g. F1-A05)"
                style={{ width: '100%', padding: '6px 10px', border: '1px solid var(--color-border)', borderRadius: 6, fontSize: 13 }}
              />
            </div>
            <div style={{ display: 'flex', gap: 6, marginBottom: 10 }}>
              {(['arrive', 'depart'] as const).map((type) => (
                <button
                  key={type}
                  onClick={() => setTriggerType(type)}
                  style={{
                    flex: 1,
                    padding: '6px',
                    borderRadius: 6,
                    border: '1px solid var(--color-border)',
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: 'pointer',
                    background: triggerType === type ? '#2563eb' : 'var(--color-surface)',
                    color: triggerType === type ? 'white' : 'var(--color-text-muted)',
                  }}
                >
                  {type === 'arrive' ? '🚗 Arrive' : '🚪 Depart'}
                </button>
              ))}
            </div>
            <button
              className="btn btn-primary"
              style={{ width: '100%', justifyContent: 'center', fontSize: 12 }}
              onClick={handleTrigger}
            >
              Trigger Event
            </button>
          </div>
        </div>

        {/* Sensor Grid */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
            <input
              type="text"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              placeholder="🔍 Filter sensors by slot..."
              style={{
                flex: 1,
                padding: '8px 14px',
                border: '1px solid var(--color-border)',
                borderRadius: 8,
                fontSize: 13,
              }}
            />
            <div style={{ fontSize: 13, color: 'var(--color-text-muted)', whiteSpace: 'nowrap' }}>
              {online} / {sensors.length} online
            </div>
            <button className="btn btn-outline" style={{ fontSize: 12, padding: '6px 12px' }} onClick={fetchData}>↻</button>
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: 40, color: 'var(--color-text-muted)' }}>Loading sensors...</div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 10, maxHeight: '70vh', overflowY: 'auto' }}>
              {filteredSensors.map((sensor) => (
                <div
                  key={sensor.id}
                  className="card"
                  style={{
                    padding: 14,
                    borderLeft: `3px solid ${sensor.status === 'online' ? '#10b981' : '#ef4444'}`,
                  }}
                >
                  <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 4, fontFamily: 'monospace' }}>
                    {sensor.slot_code}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginBottom: 6 }}>
                    {sensor.sensor_uid}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <span className={`badge badge-${sensor.status}`}>{sensor.status}</span>
                    {sensor.last_distance_cm !== null && (
                      <span style={{
                        fontSize: 11,
                        color: (sensor.last_distance_cm || 0) < 50 ? '#ef4444' : '#10b981',
                        fontWeight: 700,
                      }}>
                        {sensor.last_distance_cm?.toFixed(0)}cm
                      </span>
                    )}
                  </div>
                  {sensor.last_seen_at && (
                    <div style={{ fontSize: 10, color: 'var(--color-text-muted)' }}>
                      {new Date(sensor.last_seen_at).toLocaleTimeString()}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
