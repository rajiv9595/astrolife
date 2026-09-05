/**
 * ResearchLab — Phase 11 (NEW_REQUIRED_FEATURE, minimum new UI).
 * Read-only view over GET /research/golden + /research/gates.
 * Experimental rules are badged EXPERIMENTAL and can never appear as
 * production truth: no promotion action exists in this UI on purpose.
 * Promotion requires all 12 gates plus explicit backend approval.
 */
import React, { useEffect, useState } from 'react';
import VedicCard from '../ui/VedicCard';
import api from '../../services/api';
import { ENDPOINTS } from '../../api/endpoints';
import { badgeTone, normalizeStatus } from '../../utils/statusSemantics';

const RESEARCH_BADGE = 'bg-purple-100 text-purple-800 border-purple-300';

const ResearchLab = () => {
  const [pkg, setPkg] = useState(null);
  const [gates, setGates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [g, gt] = await Promise.all([
          api.get(ENDPOINTS.RESEARCH_GOLDEN),
          api.get(ENDPOINTS.RESEARCH_GATES),
        ]);
        if (!cancelled) {
          setPkg(g.data);
          setGates(gt.data.gates || []);
        }
      } catch (err) {
        if (!cancelled) setError(err?.response?.data?.detail || err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center gap-3 p-8" role="status" aria-label="Loading research lab">
        <div className="w-8 h-8 border-2 border-vedic-orange border-t-transparent rounded-full animate-spin" />
        <span className="text-stone-500">Loading research package…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div role="alert" className="p-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl">
        UNAVAILABLE: {String(error)}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 flex-wrap">
        <h2 className="text-xl font-serif font-bold text-vedic-blue">Research Lab</h2>
        <span className={`text-[10px] font-extrabold px-2 py-1 rounded-full border ${RESEARCH_BADGE}`}>
          RESEARCH / EXPERIMENTAL — NOT PRODUCTION TRUTH
        </span>
      </div>
      <p className="text-sm text-stone-500">
        Package <span className="font-mono font-bold">{pkg?.package_id}</span> · v{pkg?.package_version} ·
        fingerprint <span className="font-mono">{pkg?.fingerprint?.slice(0, 12)}…</span>
      </p>

      <VedicCard className="p-6">
        <h3 className="font-bold text-vedic-blue mb-4">Experimental rules ({pkg?.rules?.length || 0})</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-stone-50 text-stone-500 font-bold uppercase text-xs border-b border-stone-200">
              <tr>
                <th scope="col" className="p-3">Rule</th>
                <th scope="col" className="p-3">Version</th>
                <th scope="col" className="p-3">Tradition</th>
                <th scope="col" className="p-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-100">
              {(pkg?.rules || []).map((r) => (
                <tr key={`${r.rule_id}@${r.rule_version}`}>
                  <td className="p-3 font-semibold text-vedic-blue">
                    {r.rule_name || r.rule_id}
                    <span className="block font-mono text-[11px] font-normal text-stone-500">{r.rule_id}</span>
                  </td>
                  <td className="p-3 font-mono text-xs">{r.rule_version}</td>
                  <td className="p-3 text-stone-600">{r.tradition}</td>
                  <td className="p-3">
                    <span className={`text-[10px] font-extrabold px-2 py-1 rounded-full border ${badgeTone(normalizeStatus(r.lifecycle_status))}`}>
                      {normalizeStatus(r.lifecycle_status)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </VedicCard>

      <VedicCard className="p-6">
        <h3 className="font-bold text-vedic-blue mb-2">Promotion gates (12)</h3>
        <p className="text-xs text-stone-500 mb-4">
          Promotion requires every gate plus an explicit APPROVE review. This UI exposes no
          promotion action: TESTED ≠ PROMOTED.
        </p>
        <ul className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {gates.map((g) => (
            <li key={g} className="font-mono text-xs bg-stone-50 border border-stone-200 rounded-lg px-3 py-2">
              {g}
            </li>
          ))}
        </ul>
      </VedicCard>

      <VedicCard className="p-6">
        <h3 className="font-bold text-vedic-blue mb-2">Evidence states</h3>
        <ul className="space-y-2 text-sm">
          {(pkg?.claims || []).map((c) => (
            <li key={c.claim_id} className="flex items-start justify-between gap-4 border-b border-stone-100 pb-2 last:border-0">
              <span className="text-stone-600">{c.statement}</span>
              <span className={`shrink-0 text-[10px] font-extrabold px-2 py-1 rounded-full border ${badgeTone(normalizeStatus(c.verification_status))}`}>
                {normalizeStatus(c.verification_status)}
              </span>
            </li>
          ))}
        </ul>
      </VedicCard>
    </div>
  );
};

export default ResearchLab;
