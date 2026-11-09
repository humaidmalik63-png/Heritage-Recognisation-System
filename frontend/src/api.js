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

export async function verifyMonumentImage(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/verify-monument`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error (${response.status})`);
  }

  return response.json();
}

export async function fetchExceptions() {
  const response = await fetch(`${API_BASE_URL}/api/exceptions`);
  if (!response.ok) {
    throw new Error(`Failed to load exceptions: ${response.status}`);
  }
  return response.json();
}

export async function resolveException(id, status, curatorNotes) {
  const response = await fetch(`${API_BASE_URL}/api/exceptions/${id}/resolve`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
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

export async function fetchGeminiTelemetry() {
  const response = await fetch(`${API_BASE_URL}/api/telemetry/gemini`);
  if (!response.ok) {
    throw new Error(`Failed to load Gemini telemetry: ${response.status}`);
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
