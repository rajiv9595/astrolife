import api from './api';

export const aiService = {
    // Analyze Chart
    // opts (all optional, additive): { birthParams, evaluationIso, includeTransitEvents, eventWindowDays }
    // Backend computes canonical transits server-side; frontend never calculates astrology.
    analyze: async (query, chartContext, opts = {}) => {
        const response = await api.post('/ai/analyze', {
            query,
            context_data: chartContext,
            ...(opts.birthParams || {}),
            ...((opts.evaluationIso ?? opts.evaluation_iso) ? { evaluation_iso: opts.evaluationIso ?? opts.evaluation_iso } : {}),
            ...(opts.includeTransitEvents ? { include_transit_events: true } : {}),
            ...(opts.eventWindowDays ? { event_window_days: opts.eventWindowDays } : {}),
        });
        return response.data; // { response: "text..." }
    }
};
