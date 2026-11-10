/**
 * Heritage Monument Recognition API Client
 * Project No. 30: Visual Heritage Recognition and Grounded Cultural Discovery Platform
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:8001';

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

export async function verifyMonumentImage(file, timeoutMs = 25000, externalSignal = null) {
  const formData = new FormData();
  formData.append('file', file);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => {
    controller.abort();
  }, timeoutMs);

  if (externalSignal) {
    if (externalSignal.aborted) {
      controller.abort();
    } else {
      externalSignal.addEventListener('abort', () => controller.abort(), { once: true });
    }
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/verify-monument`, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Server error (${response.status})`);
    }

    return await response.json();
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error(`Verification request timed out after ${Math.round(timeoutMs / 1000)} seconds. Please retry.`);
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function fetchExceptionsSummary() {
  const response = await fetch(`${API_BASE_URL}/api/exceptions/summary`);
  if (!response.ok) {
    throw new Error(`Failed to load exceptions summary: ${response.status}`);
  }
  return response.json();
}

export async function fetchExceptions(token = null) {
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const response = await fetch(`${API_BASE_URL}/api/exceptions`, {
    headers,
    credentials: 'include',
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to load exceptions (${response.status})`);
  }
  return response.json();
}

export async function resolveException(id, status, curatorNotes, token = null, csrfToken = null) {
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (csrfToken) headers['X-CSRF-Token'] = csrfToken;

  const response = await fetch(`${API_BASE_URL}/api/exceptions/${id}/resolve`, {
    method: 'POST',
    headers,
    credentials: 'include',
    body: JSON.stringify({
      status,
      curator_notes: curatorNotes,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error (${response.status})`);
  }

  return response.json();
}

export async function loginAdmin(username, password) {
  const response = await fetch(`${API_BASE_URL}/api/admin/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({
      username,
      password,
    }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Authentication failed. Please check credentials.');
  }

  return response.json();
}

export async function logoutAdmin() {
  const response = await fetch(`${API_BASE_URL}/api/admin/logout`, {
    method: 'POST',
    credentials: 'include',
  });
  return response.ok;
}

export async function fetchAdminMe(token = null) {
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const response = await fetch(`${API_BASE_URL}/api/admin/me`, {
    headers,
    credentials: 'include',
  });
  if (!response.ok) return null;
  return response.json();
}

export async function fetchGeminiTelemetry(token = null) {
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const response = await fetch(`${API_BASE_URL}/api/telemetry/gemini`, {
    headers,
    credentials: 'include',
  });
  if (!response.ok) {
    throw new Error(`Failed to load Gemini telemetry: ${response.status}`);
  }
  return response.json();
}

export async function fetchGeminiPublicStatus() {
  const response = await fetch(`${API_BASE_URL}/api/telemetry/status`);
  if (!response.ok) return { status: 'unknown' };
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
