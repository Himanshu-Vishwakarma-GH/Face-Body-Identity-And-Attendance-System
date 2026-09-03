const API_URL = import.meta.env.VITE_API_URL || '';

function getAuthHeaders() {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  };
}

async function request(endpoint, options = {}) {
  const url = `${API_URL}${endpoint}`;
  const headers = options.headers ? { ...getAuthHeaders(), ...options.headers } : getAuthHeaders();
  
  const response = await fetch(url, {
    ...options,
    headers
  });

  if (response.status === 401) {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.hash = '#login';
    throw new Error('Session expired. Please log in again.');
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Request failed with status ${response.status}`);
  }

  return response.json();
}

export const api = {
  // Auth
  async login(username, password) {
    const res = await request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
    localStorage.setItem('token', res.access_token);
    localStorage.setItem('user', JSON.stringify({ username: res.username, role: res.role }));
    return res;
  },

  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },

  getUser() {
    try {
      return JSON.parse(localStorage.getItem('user'));
    } catch {
      return null;
    }
  },

  // Dashboard
  getDashboard() {
    return request('/api/admin/dashboard');
  },

  // Employees
  getEmployees(department = '', activeOnly = false) {
    const params = new URLSearchParams();
    if (department) params.append('department', department);
    if (activeOnly) params.append('active_only', 'true');
    return request(`/api/admin/employees?${params.toString()}`);
  },

  registerEmployee(data) {
    return request('/api/admin/register', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  deactivateEmployee(id) {
    return request(`/api/admin/employee/${id}`, {
      method: 'DELETE'
    });
  },

  // Cameras
  getCameras(linkedOnly = false) {
    return request(`/api/admin/cameras?linked_only=${linkedOnly}`);
  },

  scanCameras() {
    return request('/api/admin/cameras/scan', { method: 'POST' });
  },

  linkCamera(id, zone = '') {
    const query = zone ? `?zone=${encodeURIComponent(zone)}` : '';
    return request(`/api/admin/cameras/${id}/link${query}`, { method: 'POST' });
  },

  unlinkCamera(id) {
    return request(`/api/admin/cameras/${id}/unlink`, { method: 'POST' });
  },

  addCamera(data) {
    return request('/api/admin/cameras', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  testCameraSource(source) {
    return request('/api/admin/cameras/test-source', {
      method: 'POST',
      body: JSON.stringify({ source })
    });
  },

  detectUsbCameras() {
    return request('/api/admin/cameras/detect-usb');
  },

  getNetworkInfo() {
    return request('/api/admin/system/network-info');
  },

  scanWifiPhoneCameras() {
    return request('/api/admin/cameras/scan-phones');
  },

  getCameraStreamUrl(cameraId) {
    return `${API_URL}/api/camera/${cameraId}/stream`;
  },

  getCameraSnapshotUrl(cameraId) {
    return `${API_URL}/api/camera/${cameraId}/snapshot`;
  },

  // Camera Health & Maintenance Tickets
  getCameraHealth() {
    return request('/api/admin/cameras/health');
  },

  getTickets(status = '') {
    const q = status ? `?status=${status}` : '';
    return request(`/api/admin/cameras/tickets${q}`);
  },

  resolveTicket(id) {
    return request(`/api/admin/cameras/tickets/${id}/resolve`, { method: 'POST' });
  },

  // Cross-Camera & Movement Tracking
  getTimeline(employeeId = '') {
    const q = employeeId ? `?employee_id=${encodeURIComponent(employeeId)}` : '';
    return request(`/api/admin/timeline${q}`);
  },

  getEmployeeMovementPath(employeeId) {
    return request(`/api/admin/timeline/path/${encodeURIComponent(employeeId)}`);
  },

  // Logs & Alerts
  getAccessLogs(limit = 50, decision = '') {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (decision) params.append('decision', decision);
    return request(`/api/admin/logs?${params.toString()}`);
  },

  getTailgateAlerts() {
    return request('/api/admin/tailgate/alerts');
  },

  // Zones
  getZones() {
    return request('/api/admin/zones');
  },

  createZone(name, description = '') {
    return request(`/api/admin/zones?name=${encodeURIComponent(name)}&description=${encodeURIComponent(description)}`, {
      method: 'POST'
    });
  }
};
