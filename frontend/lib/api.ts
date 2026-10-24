// ParkFlow AI — API Client

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_V1 = `${API_BASE}/api/v1`;

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_V1}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const body = await response.json();
      errorDetail = body.detail?.error || body.detail || errorDetail;
    } catch {}
    throw new Error(`API Error ${response.status}: ${errorDetail}`);
  }

  return response.json();
}

// ─── Health ──────────────────────────────────────────────────
export const api = {
  health: {
    check: () => apiFetch<{ status: string; version: string }>('/health'),
    config: () => apiFetch<Record<string, unknown>>('/health/config'),
  },

  // ─── Floors ────────────────────────────────────────────────
  floors: {
    list: () => apiFetch<{ floors: import('@/types').Floor[]; total: number }>('/floors'),
    get: (floorNumber: number) => apiFetch<import('@/types').Floor>(`/floors/${floorNumber}`),
  },

  // ─── Slots ────────────────────────────────────────────────
  slots: {
    list: (params?: { floor_number?: number; status?: string; slot_type?: string }) => {
      const qs = params ? '?' + new URLSearchParams(
        Object.entries(params).filter(([, v]) => v !== undefined).map(([k, v]) => [k, String(v)])
      ).toString() : '';
      return apiFetch<{ slots: import('@/types').ParkingSlot[]; total: number }>(`/slots${qs}`);
    },
    get: (slotId: string) => apiFetch<import('@/types').ParkingSlot>(`/slots/${slotId}`),
    availability: () => apiFetch<import('@/types').AvailabilitySummary>('/slots/availability'),
    updateStatus: (slotId: string, status: string, source = 'manual') =>
      apiFetch(`/slots/${slotId}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status, source }),
      }),
  },

  // ─── Routes ───────────────────────────────────────────────
  routes: {
    calculate: (sourceNode: string, destinationSlot: string) =>
      apiFetch<import('@/types').RouteResult>('/routes', {
        method: 'POST',
        body: JSON.stringify({ source_node: sourceNode, destination_slot: destinationSlot }),
      }),
    get: (routeId: string) => apiFetch<import('@/types').RouteResult>(`/routes/${routeId}`),
    recalculate: (routeId: string, sourceNode: string, newDestination?: string) =>
      apiFetch<import('@/types').RouteResult>('/routes/recalculate', {
        method: 'POST',
        body: JSON.stringify({
          route_id: routeId,
          source_node: sourceNode,
          new_destination_slot: newDestination,
        }),
      }),
    alternatives: (routeId: string, sourceNode = 'ENTRANCE') =>
      apiFetch<{ alternatives: import('@/types').AlternativeSlot[] }>(
        `/routes/${routeId}/alternatives?source_node=${sourceNode}`
      ),
  },

  // ─── Reservations ─────────────────────────────────────────
  reservations: {
    create: (slotCode: string, userSessionId = 'guest-user') =>
      apiFetch<import('@/types').Reservation>('/reservations', {
        method: 'POST',
        body: JSON.stringify({ slot_code: slotCode, user_session_id: userSessionId }),
      }),
    list: (status?: string) =>
      apiFetch<{ reservations: import('@/types').Reservation[] }>(
        `/reservations${status ? `?status=${status}` : ''}`
      ),
    get: (id: string) => apiFetch<import('@/types').Reservation>(`/reservations/${id}`),
    cancel: (id: string) =>
      apiFetch(`/reservations/${id}`, { method: 'DELETE' }),
  },

  // ─── Sessions ─────────────────────────────────────────────
  sessions: {
    create: (destinationSlot: string) =>
      apiFetch<{ session_id: string; destination_slot: string }>('/sessions', {
        method: 'POST',
        body: JSON.stringify({ destination_slot: destinationSlot }),
      }),
    get: (id: string) => apiFetch<Record<string, unknown>>(`/sessions/${id}`),
    arrive: (id: string) =>
      apiFetch(`/sessions/${id}/arrive`, { method: 'POST' }),
    cancel: (id: string) =>
      apiFetch(`/sessions/${id}/cancel`, { method: 'POST' }),
  },

  // ─── IoT ──────────────────────────────────────────────────
  iot: {
    sensors: () => apiFetch<{ sensors: import('@/types').Sensor[]; online: number }>('/iot/sensors'),
    events: (limit = 50) =>
      apiFetch<{ events: import('@/types').SensorEvent[] }>(`/iot/events?limit=${limit}`),
    ingestEvent: (slotCode: string, state: string, distanceCm?: number) =>
      apiFetch('/iot/events', {
        method: 'POST',
        body: JSON.stringify({
          slot_code: slotCode,
          occupancy_state: state,
          distance_cm: distanceCm,
          source: 'manual',
        }),
      }),
    simulator: {
      start: (intervalS = 5) =>
        apiFetch(`/iot/simulation/start?interval_s=${intervalS}`, { method: 'POST' }),
      stop: () => apiFetch('/iot/simulation/stop', { method: 'POST' }),
      status: () => apiFetch<import('@/types').SimulatorStatus>('/iot/simulation/status'),
      trigger: (slotCode: string, eventType: 'arrive' | 'depart') =>
        apiFetch('/iot/simulation/trigger', {
          method: 'POST',
          body: JSON.stringify({ slot_code: slotCode, event_type: eventType }),
        }),
      startDemo: (targetSlot?: string) =>
        apiFetch(`/iot/simulation/demo${targetSlot ? `?target_slot=${targetSlot}` : ''}`, {
          method: 'POST',
        }),
      stress: (enabled: boolean) =>
        apiFetch(`/iot/simulation/stress?enabled=${enabled}`, { method: 'POST' }),
    },
  },

  // ─── Analytics ────────────────────────────────────────────
  analytics: {
    overview: () => apiFetch<import('@/types').AnalyticsOverview>('/analytics/overview'),
    floors: () => apiFetch<{ floors: import('@/types').FloorAvailability[] }>('/analytics/floors'),
    activity: (hours = 24, limit = 100) =>
      apiFetch<{ activity: import('@/types').SensorEvent[] }>(
        `/analytics/activity?hours=${hours}&limit=${limit}`
      ),
    hourly: (hours = 12) =>
      apiFetch<{ hourly: Array<{ hour: string; occupied: number; available: number; total: number }> }>(
        `/analytics/hourly?hours=${hours}`
      ),
  },
};

export default api;
