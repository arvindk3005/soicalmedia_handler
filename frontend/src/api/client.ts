const base = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
let token = localStorage.getItem('pulsepilot_token') || '';

export function setToken(value: string) {
  token = value;
  localStorage.setItem('pulsepilot_token', value);
}

export function clearToken() {
  token = '';
  localStorage.removeItem('pulsepilot_token');
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const isFormData = options.body instanceof FormData;
  const headers: Record<string, string> = {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...((options.headers as Record<string, string>) || {}),
  };

  // Only set Content-Type to application/json if it's not a FormData payload
  // Browsers automatically supply the correct multipart boundary for FormData
  if (!isFormData && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(base + path, {
    ...options,
    headers,
  });

  const data = await response.json().catch(() => ({ detail: 'Network response was not valid JSON' }));
  if (!response.ok) {
    throw new Error(data.detail || 'Request failed');
  }
  return data as T;
}
