/**
 * Heritage Monument Recognition API Client
 * Project No. 30: Visual Heritage Recognition and Grounded Cultural Discovery Platform
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:8001';

/**
 * Admin token for the backend's admin-only endpoints (/api/exceptions,
 * /api/exceptions/{id}/resolve, /api/telemetry/gemini). The backend verifies
 * it against the ADMIN_TOKEN environment variable.
 *
 * The token lives ONLY in this module's memory: it is never written to
 * localStorage, sessionStorage, or a cookie, and it is cleared when the
 * page reloads. The user enters it in the Exceptions drawer unlock prompt
 * (see ExceptionsDrawer.jsx). Do not persist it.
 */
let adminToken = null;

export function setAdminToken(token) {
  adminToken = token ? String(token) : null;
}

export function clearAdminToken() {
  adminToken = null;
}

export function hasAdminToken() {
  return Boolean(adminToken);
}

function adminHeaders(extra = {}) {
  return adminToken ? { Authorization: `Bearer ${adminToken}`, ...extra } : { ...extra };
}

function httpError(message, status) {
  const error = new Error(message);
  error.status = status;
  return error;
}

export async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }
  return response.json();
}

export async function fetchMonumentsCatalog() {
  const response = await fetch(`${API_BASE_URL}/api/monuments`);
  if (!response.ok) {
    throw new Error(`Failed to load monuments catalog: ${response.status}`);
  }
  return response.json();
}

export async function verifyMonumentImage(file, signal) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/verify-monument`, {
    method: 'POST',
    body: formData,
    signal,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error (${response.status})`);
  }

  return response.json();
}

export async function fetchExceptions() {
  const response = await fetch(`${API_BASE_URL}/api/exceptions`, {
    headers: adminHeaders(),
  });
  if (!response.ok) {
    if (response.status === 401) {
      throw httpError('Admin token required to view exceptions.', 401);
    }
    throw httpError(`Failed to load exceptions: ${response.status}`, response.status);
  }
  return response.json();
}

export async function resolveException(id, status, curatorNotes) {
  const response = await fetch(`${API_BASE_URL}/api/exceptions/${id}/resolve`, {
    method: 'POST',
    headers: adminHeaders({
      'Content-Type': 'application/json',
    }),
    body: JSON.stringify({
      status,
      curator_notes: curatorNotes,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    if (response.status === 401) {
      throw httpError('Admin token required to resolve exceptions.', 401);
    }
    throw httpError(
      errorData.detail || `Server error (${response.status})`,
      response.status
    );
  }

  return response.json();
}

export async function fetchGeminiTelemetry() {
  const response = await fetch(`${API_BASE_URL}/api/telemetry/gemini`, {
    headers: adminHeaders(),
  });
  if (!response.ok) {
    if (response.status === 401) {
      throw httpError('Admin token required to view telemetry.', 401);
    }
    throw httpError(`Failed to load Gemini telemetry: ${response.status}`, response.status);
  }
  return response.json();
}

export async function explainMonumentArchitecture(monumentId, file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/monuments/${monumentId}/explain-architecture`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Architecture explanation failed (${response.status})`);
  }

  return response.json();
}

export async function analyzeLocalFeatures(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/recognition/local-features`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Local feature analysis failed (${response.status})`);
  }

  return response.json();
}
