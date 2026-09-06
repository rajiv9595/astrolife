import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

/**
 * Phase 13 TEST 11 — PlanetsPage consumes the canonical backend strength result.
 *
 * Source-contract test: the Planetary Strength table must render canonical
 * Phase 4 semantics (Rupas score unit, canonical labels incl. Moderate /
 * Not Evaluated, null-score safe, reasons guard) instead of assuming the
 * legacy 0-100 evaluator shape.
 */
const here = path.dirname(fileURLToPath(import.meta.url));
const src = readFileSync(path.join(here, '..', 'PlanetsPage.jsx'), 'utf8');

describe('Phase 13 TEST 11 — PlanetsPage canonical strength contract', () => {
    it('renders canonical Rupas score unit', () => {
        assert.ok(src.includes("score_unit === 'rupas'"), 'score_unit branch present');
        assert.ok(src.includes('Rupas'), 'Rupas suffix rendered');
    });

    it('keeps legacy /100 rendering for pre-canonical cached rows', () => {
        assert.ok(src.includes('/100'), 'legacy score fallback preserved');
    });

    it('handles non-evaluated (Rahu/Ketu) rows without crashing', () => {
        // Backend sends label "Not Evaluated" + score null; the table renders
        // str.label data-driven and guards null scores, so no crash path exists.
        assert.ok(src.includes('>{str.label}<'), 'label rendered data-driven');
        assert.ok(src.includes('str.score === null'), 'null score guarded');
    });

    it('supports canonical Moderate status label', () => {
        assert.ok(src.includes("'Moderate'") || src.includes('"Moderate"'),
            'Moderate label branch present');
    });

    it('supports canonical Moolatrikona dignity badge', () => {
        assert.ok(src.includes('Moolatrikona'), 'Moolatrikona nature branch present');
    });

    it('reasons list is null-safe', () => {
        assert.ok(src.includes('(str.reasons || [])'), 'reasons guard present');
    });

    it('table still consumes backend-provided chartData.strengths (no frontend calc)', () => {
        assert.ok(src.includes('chartData.strengths.map'), 'renders backend strengths array');
        assert.ok(!src.includes('calculate_shadbala') && !src.includes('calculateAllShadbala'),
            'no frontend Shadbala calculation');
    });
});
