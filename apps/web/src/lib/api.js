const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://morningai-mvp.onrender.com';

class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const token = localStorage.getItem('auth_token');
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    };

    if (config.body && typeof config.body === 'object') {
      config.body = JSON.stringify(config.body);
    }

    const response = await fetch(url, config);
    
    if (!response.ok) {
      const error = new Error(`HTTP error! status: ${response.status}`);
      error.status = response.status;
      
      try {
        const errorData = await response.json();
        error.message = errorData.message || error.message;
      } catch {
        // If response is not JSON, use default error message
      }
      
      throw error;
    }

    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return response.json();
    }
    
    return response.text();
  }

  // Auth endpoints
  async login(email, password, otp = null) {
    return this.request('/api/login', {
      method: 'POST',
      body: { email, password, otp },
    });
  }

  async register(username, email, password) {
    return this.request('/api/register', {
      method: 'POST',
      body: { username, email, password },
    });
  }

  async verifyToken() {
    return this.request('/api/verify');
  }

  async logout() {
    return this.request('/api/auth/logout', {
      method: 'POST',
    });
  }

  async logoutAll() {
    return this.request('/api/auth/logout-all', {
      method: 'POST',
    });
  }

  // Profile endpoints
  async getProfile() {
    return this.request('/api/profile');
  }

  async updateProfile(data) {
    return this.request('/api/profile', {
      method: 'PUT',
      body: data,
    });
  }

  // 2FA endpoints
  async setup2FA() {
    return this.request('/api/auth/2fa/setup', {
      method: 'POST',
    });
  }

  async enable2FA(otp) {
    return this.request('/api/auth/2fa/enable', {
      method: 'POST',
      body: { otp },
    });
  }

  async disable2FA(otp) {
    return this.request('/api/auth/2fa/disable', {
      method: 'POST',
      body: { otp },
    });
  }

  async get2FAStatus() {
    return this.request('/api/auth/2fa/status');
  }

  // Email verification endpoints
  async sendVerificationEmail() {
    return this.request('/api/auth/email/send-verification', {
      method: 'POST',
    });
  }

  // Admin endpoints
  async getAllUsers() {
    return this.request('/api/admin/users');
  }

  async getUserById(userId) {
    return this.request(`/api/admin/users/${userId}`);
  }

  async updateUserRole(userId, role) {
    return this.request(`/api/admin/users/${userId}/role`, {
      method: 'PUT',
      body: { role },
    });
  }

  async updateUserStatus(userId, is_active) {
    return this.request(`/api/admin/users/${userId}/status`, {
      method: 'PUT',
      body: { is_active },
    });
  }

  async getBlacklist() {
    return this.request('/api/admin/blacklist');
  }

  async cleanupBlacklist() {
    return this.request('/api/admin/blacklist/cleanup', {
      method: 'POST',
    });
  }

  // Health check
  async healthCheck() {
    return this.request('/health');
  }
}

export const apiClient = new ApiClient();
