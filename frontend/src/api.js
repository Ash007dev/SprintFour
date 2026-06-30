const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');

export async function pseudonymizeDocument(text) {
  const response = await fetch(`${API_BASE}/pseudonymize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: { message: 'Unknown error' } }));
    const message = error?.detail?.message || error?.detail || `Server error (${response.status})`;
    throw new Error(message);
  }

  return response.json();
}

export async function pseudonymizeFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/pseudonymize/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: { message: 'Unknown error' } }));
    const message = error?.detail?.message || error?.detail || `Server error (${response.status})`;
    throw new Error(message);
  }

  return response.json();
}

export async function verifyDocument(pseudonymizedText, entityCount, baselineTrustScore) {
  const response = await fetch(`${API_BASE}/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      pseudonymized_text: pseudonymizedText,
      entity_count: entityCount,
      baseline_trust_score: baselineTrustScore,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: { message: 'Unknown error' } }));
    const message = error?.detail?.message || error?.detail || `Server error (${response.status})`;
    throw new Error(message);
  }

  return response.json();
}

export async function getDemoDocuments() {
  const response = await fetch(`${API_BASE}/demo-documents`);
  if (!response.ok) throw new Error('Failed to load demo documents');
  const data = await response.json();
  return data.documents;
}

export async function healthCheck() {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) throw new Error('Backend not reachable');
  return response.json();
}
