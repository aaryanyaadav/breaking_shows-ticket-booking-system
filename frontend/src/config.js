// API Base URL resolution for local development and cloud production deployments
const envBackendUrl = import.meta.env.VITE_BACKEND_URL;

const isCloudProd = import.meta.env.PROD || (typeof window !== 'undefined' && window.location.hostname.includes('onrender.com'));

export const API_BASE = envBackendUrl
  ? (envBackendUrl.startsWith('http') ? envBackendUrl : `https://${envBackendUrl}`)
  : (isCloudProd ? 'https://ticket-backend-hkry.onrender.com' : '');

export const WS_BASE = API_BASE
  ? API_BASE.replace(/^http/, 'ws')
  : `${typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${typeof window !== 'undefined' ? window.location.host : ''}`;
