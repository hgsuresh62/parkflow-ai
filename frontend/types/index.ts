// ParkFlow AI — TypeScript Types

export type SlotStatus = 'available' | 'occupied' | 'reserved' | 'pending' | 'maintenance';
export type SlotType = 'standard' | 'accessible' | 'ev_charging' | 'compact' | 'oversized';
export type SensorStatus = 'online' | 'offline' | 'error' | 'unknown';
export type EventSource = 'simulator' | 'thingspeak' | 'mqtt' | 'manual' | 'hardware';

export interface ParkingSlot {
  id: number;
  slot_code: string;
  floor_id: number;
  floor_number: number;
  slot_type: SlotType;
  status: SlotStatus;
  row_label: string;
  position_x: number;
  position_y: number;
  graph_node: string;
  is_accessible: boolean;
  last_sensor_update: string | null;
  created_at: string;
}

export interface Floor {
  id: number;
  floor_number: number;
  name: string;
  description: string;
  layout_config: {
    rows: string[];
    entrance?: string;
    ramp_up?: string;
    ramp_down?: string;
    svg_height: number;
    svg_width: number;
  };
  total_slots: number;
  available_slots: number;
  occupied_slots: number;
  reserved_slots: number;
  occupancy_percentage: number;
  slots?: ParkingSlot[];
}

export interface AvailabilitySummary {
  total_slots: number;
  available: number;
  occupied: number;
  reserved: number;
  occupancy_percentage: number;
  floors: FloorAvailability[];
}

export interface FloorAvailability {
  floor_number: number;
  available: number;
  occupied: number;
  reserved: number;
  total: number;
  occupancy_percentage: number;
}

export interface NavigationInstruction {
  step: number;
  instruction: string;
  floor: number;
  floor_change?: boolean;
  to_floor?: number;
  node_from: string;
  node_to: string;
  edge_type: string;
}

export interface RouteResult {
  route_id: string;
  destination_slot: string;
  source_node: string;
  path: string[];
  instructions: NavigationInstruction[];
  distance_m: number;
  estimated_time_seconds: number;
  route_cost: number;
  floor_changes: FloorChange[];
  is_valid: boolean;
}

export interface FloorChange {
  step_index: number;
  from_node: string;
  to_node: string;
  from_floor: number;
  to_floor: number;
  direction: 'up' | 'down';
}

export interface AlternativeSlot {
  slot_code: string;
  floor: number;
  distance_m: number;
  estimated_time_seconds: number;
  route_cost: number;
}

export interface Reservation {
  id: number;
  reservation_code: string;
  parking_slot_id: number;
  slot_code: string;
  user_session_id: string;
  status: 'active' | 'expired' | 'cancelled' | 'fulfilled';
  starts_at: string;
  expires_at: string;
  created_at: string;
}

export interface Sensor {
  id: number;
  sensor_uid: string;
  sensor_type: string;
  slot_code: string;
  provider: EventSource;
  status: SensorStatus;
  last_distance_cm: number | null;
  last_seen_at: string | null;
  meta_data: Record<string, unknown>;
}

export interface SensorEvent {
  id: number;
  slot_code: string;
  floor_number: number;
  occupancy_state: SlotStatus;
  source: EventSource;
  event_timestamp: string;
}

export interface SimulatorStatus {
  running: boolean;
  mode: 'idle' | 'random' | 'demo' | 'stress';
  interval_s: number;
  total_sensors: number;
  online_sensors: number;
  occupied_count: number;
  available_count: number;
  demo_target_slot: string | null;
  total_events: number;
  started_at: string | null;
  last_event_at: string | null;
}

export interface AnalyticsOverview {
  total_slots: number;
  available: number;
  occupied: number;
  reserved: number;
  occupancy_percentage: number;
  recent_events_1h: number;
  timestamp: string;
}

// WebSocket event types
export type WSEventType =
  | 'connection.established'
  | 'slot.updated'
  | 'reservation.created'
  | 'reservation.cancelled'
  | 'route.invalidated'
  | 'sensor.status_changed'
  | 'simulator.event'
  | 'pong';

export interface WSEvent {
  type: WSEventType;
  timestamp: string;
  data: Record<string, unknown>;
}

export interface SlotUpdatedEvent {
  slot_code: string;
  status: SlotStatus;
  floor: number;
  source: EventSource;
  distance_cm?: number;
  previous_status?: SlotStatus;
}
