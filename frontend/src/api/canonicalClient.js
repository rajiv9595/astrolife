/**
 * Canonical backend client — Phase 11.
 * Centralizes backend communication over the existing axios instance:
 * base URL handling, JSON, abort support, error normalization, response
 * pass-through (backend status semantics preserved verbatim).
 * No astrology logic lives here.
 */
import api from '../services/api';
import { ENDPOINTS } from './endpoints';
import { normalizeErrorKind } from '../utils/statusSemantics';

function toAbort(signal) {
  return signal ? { signal } : {};
}

export function normalizeApiError(err) {
  const httpStatus = err?.response?.status;
  const data = err?.response?.data;
  const detail = data?.detail ?? data?.message ?? err?.message ?? 'Unknown error';
  let kind = 'UNKNOWN';
  if (err?.code === 'ERR_CANCELED' || err?.code === 'ECONNABORTED') kind = 'UNAVAILABLE';
  else if (httpStatus === 404) kind = 'NOT_FOUND';
  else if (httpStatus === 422) kind = 'VALIDATION_ERROR';
  else if (httpStatus === 409) kind = 'CONFLICT';
  else if (typeof httpStatus === 'number' && httpStatus >= 500) kind = 'INTERNAL_ERROR';
  else if (typeof httpStatus === 'number' && httpStatus >= 400) kind = 'INVALID_INPUT';
  else if (!err?.response) kind = 'UNAVAILABLE';
  return {
    kind: normalizeErrorKind(kind),
    message: typeof detail === 'string' ? detail : JSON.stringify(detail),
    httpStatus,
    detail,
  };
}

export const canonicalClient = {
  computeChart: async (params, { signal } = {}) => {
    const res = await api.post(ENDPOINTS.COMPUTE, params, toAbort(signal));
    return res.data;
  },

  dynamicState: async (birthParams, { evaluationIso, signal } = {}) => {
    const res = await api.post(
      ENDPOINTS.DYNAMIC_STATE,
      { ...birthParams, evaluation_datetime: evaluationIso ?? null },
      toAbort(signal)
    );
    return res.data;
  },

  panchanga: async ({ evaluationIso, lat, lon, tz }, { signal } = {}) => {
    const res = await api.post(
      ENDPOINTS.DYNAMIC_PANCHANGA,
      { evaluation_datetime: evaluationIso, lat, lon, tz },
      toAbort(signal)
    );
    return res.data;
  },

  transitSnapshot: async ({ evaluationIso, lat, lon, tz }, { signal } = {}) => {
    const res = await api.post(
      ENDPOINTS.DYNAMIC_TRANSIT_SNAPSHOT,
      { evaluation_datetime: evaluationIso, lat, lon, tz },
      toAbort(signal)
    );
    return res.data;
  },

  expertReport: async (chartData, { signal } = {}) => {
    const res = await api.post(ENDPOINTS.AI_EXPERT_REPORT, { context_data: chartData }, toAbort(signal));
    return res.data;
  },
};
