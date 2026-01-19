import api from './api';

export const aiService = {
    // Analyze Chart
    analyze: async (query, chartContext) => {
        const response = await api.post('/ai/analyze', {
            query,
            context_data: chartContext
        });
        return response.data; // { response: "text..." }
    }
};
