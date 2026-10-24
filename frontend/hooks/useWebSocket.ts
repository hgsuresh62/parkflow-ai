// ParkFlow AI — WebSocket Hook with Reconnection

import { useEffect, useRef, useState, useCallback } from 'react';
import type { WSEvent, WSEventType } from '@/types';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

type WSStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

interface UseWebSocketOptions {
  onMessage?: (event: WSEvent) => void;
  onSlotUpdated?: (data: WSEvent['data']) => void;
  onReservationCreated?: (data: WSEvent['data']) => void;
  onSimulatorEvent?: (data: WSEvent['data']) => void;
  autoReconnect?: boolean;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectCountRef = useRef(0);
  const isMountedRef = useRef(true);

  const [status, setStatus] = useState<WSStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<WSEvent | null>(null);
  const [connectionCount, setConnectionCount] = useState(0);

  const {
    onMessage,
    onSlotUpdated,
    onReservationCreated,
    onSimulatorEvent,
    autoReconnect = true,
  } = options;

  const connect = useCallback(() => {
    if (!isMountedRef.current) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setStatus('connecting');

    try {
      const ws = new WebSocket(`${WS_URL}/ws`);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!isMountedRef.current) return;
        setStatus('connected');
        setConnectionCount((c) => c + 1);
        reconnectCountRef.current = 0;
        // Start heartbeat
        const ping = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          } else {
            clearInterval(ping);
          }
        }, 30000);
      };

      ws.onmessage = (event) => {
        if (!isMountedRef.current) return;
        try {
          const msg: WSEvent = JSON.parse(event.data);
          setLastMessage(msg);
          onMessage?.(msg);

          switch (msg.type) {
            case 'slot.updated':
              onSlotUpdated?.(msg.data);
              break;
            case 'reservation.created':
              onReservationCreated?.(msg.data);
              break;
            case 'simulator.event':
              onSimulatorEvent?.(msg.data);
              break;
          }
        } catch {}
      };

      ws.onerror = () => {
        if (!isMountedRef.current) return;
        setStatus('error');
      };

      ws.onclose = () => {
        if (!isMountedRef.current) return;
        setStatus('disconnected');
        wsRef.current = null;

        // Exponential backoff reconnection
        if (autoReconnect && isMountedRef.current) {
          const delay = Math.min(1000 * Math.pow(2, reconnectCountRef.current), 30000);
          reconnectCountRef.current++;
          reconnectTimerRef.current = setTimeout(() => {
            if (isMountedRef.current) connect();
          }, delay);
        }
      };
    } catch {
      setStatus('error');
    }
  }, [onMessage, onSlotUpdated, onReservationCreated, onSimulatorEvent, autoReconnect]);

  const disconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
    }
    wsRef.current?.close();
    wsRef.current = null;
    setStatus('disconnected');
  }, []);

  useEffect(() => {
    isMountedRef.current = true;
    connect();

    return () => {
      isMountedRef.current = false;
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { status, lastMessage, connectionCount, connect, disconnect };
}
