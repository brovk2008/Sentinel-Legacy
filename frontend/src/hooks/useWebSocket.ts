import { useEffect, useRef, useState, useCallback } from "react";
import { SentinelEvent } from "../types";
import { WS_BASE_URL } from "../config/api";

export function useWebSocket(role: string = "governance_admin") {
  const [events, setEvents] = useState<SentinelEvent[]>([]);
  const [latestEvent, setLatestEvent] = useState<SentinelEvent | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const lastTsRef = useRef<number>(0);
  const reconnectDelayRef = useRef(1000);

  const connect = useCallback(() => {
    const fullUrl = `${WS_BASE_URL}/ws/dashboard?role=${role}&last_seq_ts=${lastTsRef.current}`;

    try {
      const ws = new WebSocket(fullUrl);

      ws.onopen = () => {
        setConnected(true);
        reconnectDelayRef.current = 1000;
      };

      ws.onmessage = (e) => {
        try {
          const event: SentinelEvent = JSON.parse(e.data);
          if (event.type === "ping") {
            ws.send(JSON.stringify({ type: "pong" }));
            return;
          }
          lastTsRef.current = event.ts;
          setLatestEvent(event);
          setEvents((prev) => [event, ...prev].slice(0, 150));
        } catch {
          // ignore parsing error
        }
      };

      ws.onclose = () => {
        setConnected(false);
        setTimeout(connect, Math.min(reconnectDelayRef.current, 15000));
        reconnectDelayRef.current = Math.min(reconnectDelayRef.current * 1.5, 15000);
      };

      ws.onerror = () => {
        ws.close();
      };

      wsRef.current = ws;
    } catch {
      setTimeout(connect, 3000);
    }
  }, [role]);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  return { events, latestEvent, connected };
}
