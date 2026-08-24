// API Base URL resolution for local development and cloud production deployments
const envBackendUrl = import.meta.env.VITE_BACKEND_URL;

export const API_BASE = envBackendUrl
  ? (envBackendUrl.startsWith('http') ? envBackendUrl : `https://${envBackendUrl}`)
  : (import.meta.env.MODE === 'production' ? 'https://ticket-backend-hkry.onrender.com' : '');

export const WS_BASE = API_BASE.replace(/^http/, 'ws');
