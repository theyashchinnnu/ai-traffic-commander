/**
 * API Client for AI City Traffic Commander
 * Handles all HTTP requests with automatic auth injection
 */
class TrafficAPI {
    constructor() {
        this.baseURL = window.location.origin;
        this.token = localStorage.getItem('tc_token');
        this.apiKey = localStorage.getItem('tc_api_key');
    }

    getHeaders() {
        const headers = { 'Content-Type': 'application/json' };
        if (this.apiKey) {
            headers['X-API-Key'] = this.apiKey;
        } else if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        return headers;
    }

    async request(method, endpoint, body = null) {
        const options = {
            method,
            headers: this.getHeaders(),
        };
        if (body) {
            options.body = JSON.stringify(body);
        }
        
        const response = await fetch(`${this.baseURL}${endpoint}`, options);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || `Request failed with status ${response.status}`);
        }
        return data;
    }

    // Auth
    async register(username, email, password) {
        return this.request('POST', '/api/auth/register', { username, email, password });
    }

    async login(username, password) {
        const data = await this.request('POST', '/api/auth/login', { username, password });
        this.token = data.access_token;
        this.apiKey = data.api_key;
        localStorage.setItem('tc_token', data.access_token);
        localStorage.setItem('tc_api_key', data.api_key);
        localStorage.setItem('tc_user', JSON.stringify(data.user));
        return data;
    }

    async getMe() {
        return this.request('GET', '/api/auth/me');
    }

    async getApiKeys() {
        return this.request('GET', '/api/auth/api-keys');
    }

    async createApiKey(name) {
        return this.request('POST', '/api/auth/api-keys', { name });
    }

    async revokeApiKey(keyId) {
        return this.request('DELETE', `/api/auth/api-keys/${keyId}`);
    }

    // Incidents
    async analyzeIncident(description, location = null, incidentType = null) {
        const body = { description };
        if (location) body.location = location;
        if (incidentType) body.incident_type = incidentType;
        return this.request('POST', '/api/incidents/analyze', body);
    }

    async getHistory() {
        return this.request('GET', '/api/incidents/history');
    }

    async getIncident(id) {
        return this.request('GET', `/api/incidents/${id}`);
    }

    async healthCheck() {
        return this.request('GET', '/api/health');
    }

    // Session
    isLoggedIn() {
        return !!(this.token || this.apiKey);
    }

    logout() {
        this.token = null;
        this.apiKey = null;
        localStorage.removeItem('tc_token');
        localStorage.removeItem('tc_api_key');
        localStorage.removeItem('tc_user');
    }

    getUser() {
        const user = localStorage.getItem('tc_user');
        return user ? JSON.parse(user) : null;
    }
}

// Global instance
const api = new TrafficAPI();
