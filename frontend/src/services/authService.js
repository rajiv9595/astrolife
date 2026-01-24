import api from './api';

export const authService = {
    // Login
    login: async (email, password) => {
        const response = await api.post('/auth/login', { email, password });
        if (response.data.access_token) {
            localStorage.setItem('token', response.data.access_token);
            localStorage.setItem('user', JSON.stringify(response.data.user));
        }
        return response.data;
    },

    // Google Login
    googleLogin: async (token) => {
        const response = await api.post('/auth/google', { token });
        if (response.data.access_token) {
            localStorage.setItem('token', response.data.access_token);
            localStorage.setItem('user', JSON.stringify(response.data.user));
        }
        return response.data;
    },

    // Signup
    signup: async (userData) => {
        // userData matches schema: name, email, password, mobile_number, date_of_birth, time_of_birth, location, lat, lon, timezone
        const response = await api.post('/auth/signup', userData);
        if (response.data.access_token) {
            localStorage.setItem('token', response.data.access_token);
            localStorage.setItem('user', JSON.stringify(response.data.user));
        }
        return response.data;
    },

    // Logout
    logout: () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
    },

    // Get Current User
    getCurrentUser: async () => {
        const response = await api.get('/auth/me');
        return response.data;
    },

    // Get Chart Params
    getChartDataParams: async () => {
        const response = await api.get('/auth/chart-data');
        return response.data;
    },

    // Update Profile
    updateProfile: async (data) => {
        const response = await api.put('/auth/me', data);
        // Update local user data
        if (response.data) {
            localStorage.setItem('user', JSON.stringify(response.data));
        }
        return response.data;
    }
};
