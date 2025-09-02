// Authentication utilities
class AuthManager {
    constructor() {
        this.baseURL = window.CONFIG?.FRONTEND_API_URL || 'http://localhost:5000/api';
    }

    // Check if user is authenticated
    isAuthenticated() {
        const user = this.getCurrentUser();
        return user !== null;
    }

    // Get current user from localStorage
    getCurrentUser() {
        try {
            const userStr = localStorage.getItem('user');
            return userStr ? JSON.parse(userStr) : null;
        } catch {
            return null;
        }
    }

    // Check if current user has specific role
    hasRole(role) {
        const user = this.getCurrentUser();
        return user && user.role === role;
    }

    // Logout user
    async logout() {
        try {
            await fetch(`${this.baseURL}/auth/logout`, {
                method: 'POST',
                credentials: 'include'
            });
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            localStorage.removeItem('user');
            window.location.href = 'login.html';
        }
    }

    // Refresh authentication token
    async refreshToken() {
        try {
            const response = await fetch(`${this.baseURL}/auth/refresh`, {
                method: 'POST',
                credentials: 'include'
            });

            if (response.ok) {
                const result = await response.json();
                localStorage.setItem('user', JSON.stringify(result.user));
                return true;
            } else {
                this.logout();
                return false;
            }
        } catch (error) {
            console.error('Token refresh error:', error);
            this.logout();
            return false;
        }
    }

    // Redirect to appropriate dashboard based on role
    redirectToDashboard() {
        const user = this.getCurrentUser();
        if (user) {
            if (user.role === 'student') {
                window.location.href = 'dashboard_student.html';
            } else {
                window.location.href = 'dashboard_teacher.html';
            }
        } else {
            window.location.href = 'login.html';
        }
    }

    // Check authentication and redirect if not authenticated
    requireAuth(requiredRole = null) {
        const user = this.getCurrentUser();
        
        if (!user) {
            window.location.href = 'login.html';
            return false;
        }

        if (requiredRole && user.role !== requiredRole) {
            this.redirectToDashboard();
            return false;
        }

        return true;
    }
}

// API utilities
class APIClient {
    constructor() {
        this.baseURL = window.CONFIG?.FRONTEND_API_URL || 'http://localhost:5000/api';
        this.authManager = new AuthManager();
    }

    // Make authenticated API request
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            let response = await fetch(url, config);

            // If unauthorized, try to refresh token
            if (response.status === 401) {
                const refreshed = await this.authManager.refreshToken();
                if (refreshed) {
                    // Retry the original request
                    response = await fetch(url, config);
                } else {
                    throw new Error('Authentication failed');
                }
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // GET request
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    // POST request
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // PUT request
    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    // DELETE request
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
}

// Utility functions
class Utils {
    // Format date
    static formatDate(dateString) {
        if (!dateString) return 'No date';
        
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    // Format datetime
    static formatDateTime(dateString) {
        if (!dateString) return 'No date';
        
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    // Show loading spinner
    static showLoading(element, show = true) {
        if (show) {
            element.innerHTML = `
                <div class="flex items-center justify-center p-4">
                    <svg class="animate-spin h-8 w-8 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                </div>
            `;
        }
    }

    // Show error message
    static showError(element, message) {
        element.innerHTML = `
            <div class="alert alert-error">
                <strong>Error:</strong> ${message}
            </div>
        `;
    }

    // Show empty state
    static showEmpty(element, message = 'No data available') {
        element.innerHTML = `
            <div class="text-center py-8">
                <p class="text-gray-500">${message}</p>
            </div>
        `;
    }

    // Debounce function
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Calculate grade color
    static getGradeColor(score, maxScore) {
        const percentage = (score / maxScore) * 100;
        if (percentage >= 90) return 'text-green-600';
        if (percentage >= 80) return 'text-blue-600';
        if (percentage >= 70) return 'text-yellow-600';
        if (percentage >= 60) return 'text-orange-600';
        return 'text-red-600';
    }

    // Get grade letter
    static getGradeLetter(score, maxScore) {
        const percentage = (score / maxScore) * 100;
        if (percentage >= 90) return 'A';
        if (percentage >= 80) return 'B';
        if (percentage >= 70) return 'C';
        if (percentage >= 60) return 'D';
        return 'F';
    }
}

// Global instances
window.authManager = new AuthManager();
window.apiClient = new APIClient();
window.utils = Utils;