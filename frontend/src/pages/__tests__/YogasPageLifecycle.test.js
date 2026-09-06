import { describe, it } from 'node:test';
import assert from 'node:assert/strict';

/**
 * HOTFIX 1 — YogasPage stale-response tests.
 *
 * Mirrors the guarded continuations in frontend/src/pages/YogasPage.jsx:
 * component-scope `requestGenerationRef`, per-fetch captured generation,
 * `isCurrentGeneration()` gating setYogas / setLoading / toast /
 * localStorage, AbortController cleanup, CanceledError/AbortError silence.
 * See PlanetsPageLifecycle.test.js header for the §10 realism note, which
 * applies identically here (one fetch per effect run; overlapping fetches
 * model an older continuation surviving abort or a same-mount refetch).
 */

const delay = (ms) => new Promise((r) => setTimeout(r, ms));

const createComponent = () => ({ requestGenerationRef: { current: 0 } });

const createEffectRun = (component) => {
    const controller = new AbortController();
    return {
        component,
        signal: controller.signal,
        mounted: true,
        cleanup() {
            this.mounted = false;
            controller.abort();
        },
    };
};

const createStore = () => ({
    yogas: [],
    loading: true,
    toastErrors: [],
    ls: new Map(),
});

const runYogasFetch = async (
    effectRun,
    store,
    { id, latency, shouldFail = false, networkYogas }
) => {
    const ref = effectRun.component.requestGenerationRef;
    const generation = ++ref.current;
    const isCurrentGeneration = () =>
        effectRun.mounted && generation === ref.current;

    try {
        await delay(latency);
        if (effectRun.signal.aborted) {
            const e = new Error('canceled');
            e.name = 'CanceledError';
            throw e;
        }
        if (!isCurrentGeneration()) return `${id}:stale-suppressed`;
        if (shouldFail) throw Object.assign(new Error(`boom-${id}`), { name: 'Error' });

        const data = { yogas: networkYogas !== undefined ? networkYogas : [{ id }] };
        if (!isCurrentGeneration()) return `${id}:stale-suppressed`;

        store.yogas = data.yogas;
        store.ls.set('chartData', JSON.stringify({ ...data, _gen: generation }));
        store.loading = false;
        return `${id}:wrote`;
    } catch (err) {
        if (!isCurrentGeneration() || err.name === 'CanceledError' || err.name === 'AbortError') {
            return `${id}:error-suppressed`;
        }
        store.toastErrors.push(`${id}:failed-yogas`);
        store.loading = false;
        return `${id}:toast`;
    }
};

describe('HOTFIX 1 — same-mounted stale-response protection (YogasPage)', () => {
    it('stale success: A starts, B starts, B succeeds, A succeeds => B authoritative', async () => {
        const component = createComponent();
        const effectRun = createEffectRun(component);
        const store = createStore();

        const pA = runYogasFetch(effectRun, store, { id: 'A', latency: 50 });
        await delay(5); // A in-flight before B starts
        const pB = runYogasFetch(effectRun, store, {
            id: 'B',
            latency: 10,
            networkYogas: [{ id: 'B-yoga' }],
        });
        const [rA, rB] = await Promise.all([pA, pB]);

        assert.equal(rB, 'B:wrote');
        assert.equal(rA, 'A:stale-suppressed');
        assert.deepEqual(store.yogas, [{ id: 'B-yoga' }]);
        assert.equal(JSON.parse(store.ls.get('chartData')).yogas[0].id, 'B-yoga');
        assert.equal(store.toastErrors.length, 0);
    });

    it('stale failure: A starts, B starts, B succeeds, A fails => no toast from A', async () => {
        const component = createComponent();
        const effectRun = createEffectRun(component);
        const store = createStore();

        const pA = runYogasFetch(effectRun, store, { id: 'A', latency: 50, shouldFail: true });
        await delay(5);
        const pB = runYogasFetch(effectRun, store, {
            id: 'B',
            latency: 10,
            networkYogas: [{ id: 'B-yoga' }],
        });
        const [rA, rB] = await Promise.all([pA, pB]);

        assert.equal(rB, 'B:wrote');
        // Either silent suppression path is acceptable (see Planets TEST 2).
        assert.ok(rA === 'A:stale-suppressed' || rA === 'A:error-suppressed', `A suppressed, got ${rA}`);
        assert.deepEqual(store.yogas, [{ id: 'B-yoga' }], 'B remains displayed');
        assert.equal(store.toastErrors.length, 0, 'A produces no error toast');
    });

    it('unmount: A starts, unmounts, A resolves => no write', async () => {
        const component = createComponent();
        const effectRun = createEffectRun(component);
        const store = createStore();

        const p = runYogasFetch(effectRun, store, { id: 'A', latency: 20 });
        effectRun.cleanup();
        const r = await p;

        assert.equal(r, 'A:error-suppressed');
        assert.deepEqual(store.yogas, []);
        assert.equal(store.toastErrors.length, 0);
        assert.equal(store.ls.has('chartData'), false);
    });

    it('unmount failure: A starts, unmounts, A fails => no toast', async () => {
        const component = createComponent();
        const effectRun = createEffectRun(component);
        const store = createStore();

        const p = runYogasFetch(effectRun, store, { id: 'A', latency: 20, shouldFail: true });
        effectRun.cleanup();
        const r = await p;

        assert.equal(r, 'A:error-suppressed');
        assert.equal(store.toastErrors.length, 0);
    });
});
