import api from './api';

export const astroService = {
    // Compute Full Chart
    computeChart: async (params) => {
        // params: { year, month, day, hour, minute, lat, lon, tz }
        const response = await api.post('/compute', params);
        return response.data;
    },

    // Geocode Search
    searchLocation: async (query) => {
        // Note: The backend endpoint is defined as direct params on geocode router usually
        // But let's assume /geocode/search?query=...
        // Adjust port if needed. Geocode service might be on 8001 widely, but here simple assumption on main API
        // Wait, previous file view showed geocode router included in main app.
        const response = await api.get(`/geocode/search?query=${encodeURIComponent(query)}`);
        return response.data;
    },

    // Get location suggestions for dropdown
    getLocationSuggestions: async (query) => {
        const response = await api.get(`/geocode/suggestions?query=${encodeURIComponent(query)}`);
        return response.data.results || [];
    },

    // Match Making
    matchCharts: async (boyParams, girlParams) => {
        const response = await api.post('/match', {
            boy: boyParams,
            girl: girlParams
        });
        return response.data;
    }
};
