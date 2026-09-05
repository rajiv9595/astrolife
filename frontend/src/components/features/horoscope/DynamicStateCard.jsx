/**
 * DynamicStateCard — Phase 11 (INTEGRATION, new file, existing VedicCard style).
 * Shows the explicit evaluation datetime plus backend-supplied dynamic facts
 * (current Dasha hierarchy, transit snapshot marker). All values come from
 * POST /dynamic/state; nothing is derived client-side. UNKNOWN/INVALID are
 * rendered with preserved semantics, never as negatives.
 */
import React from 'react';
import VedicCard from '../../ui/VedicCard';
import { describeStatus, normalizeStatus } from '../../../utils/statusSemantics';
import { formatIsoDisplay } from '../../../utils/canonicalFormat';

function Row({ label, value, sub }) {
  return (
    <div className="flex items-start justify-between gap-4 py-2 border-b border-stone-100 last:border-0">
      <span className="text-xs font-bold uppercase tracking-wider text-stone-400">{label}</span>
      <span className="text-sm font-semibold text-vedic-blue text-right">
        {value}
        {sub ? <span className="block text-xs font-normal text-stone-500">{sub}</span> : null}
      </span>
    </div>
  );
}

const DynamicStateCard = ({ evaluationIso, dynamicState, loading, error }) => {
  const shown = formatIsoDisplay(evaluationIso || '');
  const dasha = dynamicState?.dasha?.current || dynamicState?.dasha || null;
  const hierarchy = Array.isArray(dasha?.hierarchy) ? dasha.hierarchy.join(' \u2192 ') : null;
  const transitNote = dynamicState?.transits ? 'Snapshot supplied by backend' : 'Unavailable';

  return (
    <VedicCard className="p-6">
      <h3 className="font-bold text-vedic-blue mb-1">Dynamic State</h3>
      <p className="text-xs text-stone-500 mb-4">
        Evaluation moment is explicit. Natal chart is never recalculated here.
      </p>
      {loading ? (
        <div className="flex items-center gap-3 py-4" role="status" aria-label="Loading dynamic state">
          <div className="w-6 h-6 border-2 border-vedic-orange border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-stone-500">Loading dynamic state…</span>
        </div>
      ) : error ? (
        <div role="alert" className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
          {error.kind}: {error.message}
        </div>
      ) : (
        <div>
          <Row label="Evaluation" value={shown.text} sub={evaluationIso || undefined} />
          <Row label="Dasha" value={hierarchy || 'Unknown'} sub={hierarchy ? undefined : describeStatus('UNKNOWN')} />
          <Row label="Transits" value={transitNote} />
          {dynamicState?.note ? <Row label="Note" value={String(dynamicState.note)} /> : null}
          <p className="sr-only">Dasha status: {normalizeStatus(hierarchy ? 'ACTIVE' : 'UNKNOWN')}</p>
        </div>
      )}
    </VedicCard>
  );
};

export default DynamicStateCard;
