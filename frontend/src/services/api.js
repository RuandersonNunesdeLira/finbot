const API_BASE = '';  // Vite proxy handles /api -> backend

async function apiFetch(endpoint, options = {}) {
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    return await res.json();
  } catch (err) {
    console.error(`API Error [${endpoint}]:`, err);
    throw err;
  }
}

export async function checkHealth() {
  return apiFetch('/health');
}

export async function sendMessage(message, sessionId = 'web') {
  return apiFetch('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message, session_id: sessionId }),
  });
}

export async function getPromptStatus() {
  return apiFetch('/api/prompt');
}

export async function submitFeedback({ rating, comment = '', suggestion = '' }) {
  return apiFetch('/api/feedback', {
    method: 'POST',
    body: JSON.stringify({ rating, comment, suggestion }),
  });
}

export async function getFeedbacks() {
  return apiFetch('/api/feedbacks');
}

export async function processOptimize() {
  return apiFetch('/api/feedback/process', { method: 'POST' });
}
