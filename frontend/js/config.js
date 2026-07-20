/**
 * config.js — Environment configuration for ProM frontend
 *
 * Detects backend API URL from environment or falls back to localhost.
 * To override the backend port, set BACKEND_PORT in localStorage:
 *   localStorage.setItem('BACKEND_PORT', '8003')
 *
 * To override via query string:
 *   ?backend_port=8003
 */

function getBackendUrl() {
  // Check query string first
  const params = new URLSearchParams(window.location.search);
  const queryPort = params.get('backend_port');
  if (queryPort) {
    localStorage.setItem('BACKEND_PORT', queryPort);
  }

  // Check localStorage for override
  const storedPort = localStorage.getItem('BACKEND_PORT');
  const port = storedPort || '8000';

  return `http://127.0.0.1:${port}/api`;
}

// Export the API base URL
const API = getBackendUrl();

// Log the config on load for debugging
console.log('[ProM Config] Backend API:', API);
