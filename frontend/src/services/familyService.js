import api from './api';

export const familyService = {
    // Get all family members
    getAll: async () => {
        const response = await api.get('/family/');
        return response.data;
    },

    // Add new member
    add: async (memberData) => {
        const response = await api.post('/family/', memberData);
        return response.data;
    },

    // Delete member
    delete: async (id) => {
        const response = await api.delete(`/family/${id}`);
        return response.data;
    },

    // Update member
    update: async (id, memberData) => {
        const response = await api.put(`/family/${id}`, memberData);
        return response.data;
    }
};
