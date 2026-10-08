/**
 * Sentinel Legacy v2.0 — Centralized API & WebSocket Configuration
 * 
 * Automatically resolves the backend API and WebSocket endpoints:
 * 1. Checks VITE_API_URL / VITE_WS_URL environment variables (for Vercel / Cloudflare).
 * 2. In non-localhost production environments, falls back to the current window host.
 * 3. Defaults to http://localhost:8000 and ws://localhost:8000 in local development.
 */

const getApiBaseUrl = (): string => {
  const envUrl = (import.meta as any).env?.VITE_API_URL;
  if (envUrl && typeof envUrl === 'string' && envUrl.trim()) {
    return envUrl.replace(/\/+$/, '');
  }
  if (typeof window !== 'undefined') {
    const host = window.location.hostname;
    if (host !== 'localhost' && host !== '127.0.0.1') {
      return window.location.origin;
    }
  }
  return 'http://localhost:8000';
};

const getWsBaseUrl = (): string => {
  const envWsUrl = (import.meta as any).env?.VITE_WS_URL;
  if (envWsUrl && typeof envWsUrl === 'string' && envWsUrl.trim()) {
    return envWsUrl.replace(/\/+$/, '');
  }
  if (typeof window !== 'undefined') {
    const host = window.location.hostname;
    if (host !== 'localhost' && host !== '127.0.0.1') {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      return `${protocol}//${window.location.host}`;
    }
  }
  return 'ws://localhost:8000';
};

export const API_BASE_URL = getApiBaseUrl();
export const WS_BASE_URL = getWsBaseUrl();
