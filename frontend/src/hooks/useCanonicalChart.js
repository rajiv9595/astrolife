/**
 * useCanonicalChart — Phase 11.
 * Separates STATIC chart state (birth params + ChartFacts) from DYNAMIC
 * astrology state (evaluation datetime + dasha/transit snapshot).
 * Changing the evaluation date never recalculates the natal chart:
 * static results are cache-keyed and dynamic fetches are keyed on
 * chart identity + evaluation ISO + profile. Stale dynamic data is
 * cleared whenever the chart identity changes (no cross-chart leaks).
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { canonicalClient, normalizeApiError } from '../api/canonicalClient';
import { buildComputeParams, chartCacheKey, dynamicCacheKey } from '../utils/chartParams';

const staticCache = new Map();
const dynamicCache = new Map();

export function useCanonicalChart(birthInput, { evaluationIso = null, profile = 'default' } = {}) {
  const [staticChart, setStaticChart] = useState(null);
  const [dynamicState, setDynamicState] = useState(null);
  const [loadingStatic, setLoadingStatic] = useState(false);
  const [loadingDynamic, setLoadingDynamic] = useState(false);
  const [error, setError] = useState(null);
  const abortRef = useRef(null);

  const built = useMemo(() => buildComputeParams(birthInput || {}), [birthInput]);
  const params = built.params || null;
  const paramErrors = built.errors || null;
  const chartKey = params ? chartCacheKey(params) : null;
  const dynKey = params ? dynamicCacheKey(params, evaluationIso, profile) : null;

  const loadStatic = useCallback(async () => {
    if (!params) return;
    if (staticCache.has(chartKey)) {
      setStaticChart(staticCache.get(chartKey));
      return staticCache.get(chartKey);
    }
    setLoadingStatic(true);
    setError(null);
    try {
      const data = await canonicalClient.computeChart(params);
      staticCache.set(chartKey, data);
      setStaticChart(data);
      return data;
    } catch (err) {
      setError(normalizeApiError(err));
      setStaticChart(null);
      return null;
    } finally {
      setLoadingStatic(false);
    }
  }, [params, chartKey]);

  const loadDynamic = useCallback(async () => {
    if (!params) return;
    if (dynamicCache.has(dynKey)) {
      setDynamicState(dynamicCache.get(dynKey));
      return dynamicCache.get(dynKey);
    }
    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setLoadingDynamic(true);
    try {
      const data = await canonicalClient.dynamicState(params, {
        evaluationIso,
        signal: controller.signal,
      });
      dynamicCache.set(dynKey, data);
      setDynamicState(data);
      return data;
    } catch (err) {
      if (err?.code === 'ERR_CANCELED') return null;
      setError(normalizeApiError(err));
      setDynamicState(null);
      return null;
    } finally {
      setLoadingDynamic(false);
    }
  }, [params, dynKey, evaluationIso]);

  // New chart identity clears dynamic state first (stale-guard).
  useEffect(() => {
    setDynamicState(null);
    setError(null);
    loadStatic();
    return () => {
      if (abortRef.current) abortRef.current.abort();
    };
  }, [chartKey]); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    params,
    paramErrors,
    chartKey,
    staticChart,
    dynamicState,
    loadingStatic,
    loadingDynamic,
    error,
    loadStatic,
    loadDynamic,
  };
}

export function __clearCachesForTests() {
  staticCache.clear();
  dynamicCache.clear();
}
