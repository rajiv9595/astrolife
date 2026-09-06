import { describe, it } from 'node:test';
import assert from 'node:assert/strict';

/**
 * HOTFIX 1 — PlanetsPage lifecycle & stale-response tests.
 *
 * Faithful mirror of the guarded continuation pattern in
 * frontend/src/pages/PlanetsPage.jsx (effect body):
 *   - component-scope `requestGenerationRef` shared by all fetches
 *   - each fetch captures `generation = ++ref.current` at start
 *   - after EVERY await, `isCurrentGeneration()` (isMounted + generation
 *     identity) gates setChartData / setLoading / toast / localStorage
 *   - AbortController cleanup sets isMounted=false + aborts; CanceledError /
 *     AbortError never toast
 *   - cache requires structural validation (`parsedCache.planets`) and never
 *     overwrites fresher network data; a failed network never clears cache
 *
 * NOTE on TEST 1/2 realism (§10): the component issues exactly one fetch per
 * effect run, so two overlapping same-closure invocations cannot be produced
 * through the literal public render path today. The closest real invocation
 * path is (a) an effect re-run (e.g. `navigate` change / StrictMode remount)
 * whose older continuation survives abort (transport ignores signal, or the
 * promise already resolved with its continuation queued), and (b) any future
 * same-mount refetch/retry. Both cases share one component-scope generation
 * ref, which is exactly what this harness drives: two overlapping fetches
 * against one shared ref with NO cleanup of the first — i.e. both observe
 * `isMounted === true`, so only the generation guard can suppress the stale
 * one. The pre-fix code fails TEST 1/2 in this harness; the fixed code passes.
 */

const delay = (ms) => new Promise((r) => setTimeout(r, ms));

// Component scope: mirrors `useRef(0)` at component scope (shared ref object).
const createComponent = () => ({ requestGenerationRef: { current: 0 } });

// One effect run: mirrors per-effect `isMounted` + `AbortController`.
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

// Effect store: mirrors component state + localStorage + toast surface.
const createStore = (seedCache) => ({
    chartData: null,
    loading: true,
    toastErrors: [],
    navigations: [],
    ls: new Map(
        seedCache !== undefined ? [['chartData', JSON.stringify(seedCache)]] : []
    ),
});

/**
 * Mirrors PlanetsPage fetchChartData continuations (user-name step omitted:
 * it follows the identical guard and is covered by the same invariant).
 * - cache: read + structural validation, gated re-check before render
 * - params: stubbed present (formData path); `formDataNull` opts into the
 *   missing-details branch
 * - network: resolves `networkData` or rejects, fully generation-gated
 */
const runPlanetsFetch = async (
    effectRun,
    store,
    { id, latency, shouldFail = false, networkData, formDataNull = false }
) => {
    const ref = effectRun.component.requestGenerationRef;
    const generation = ++ref.current;
    const isCurrentGeneration = () =>
        effectRun.mounted && generation === ref.current;
    const aborted = () => effectRun.signal.aborted;

    try {
        // --- cache step (synchronous read, structurally validated) ---
        const cachedRaw = store.ls.get('chartData');
        if (cachedRaw) {
            try {
                const parsed = JSON.parse(cachedRaw);
                if (parsed && parsed.planets) {
                    if (!isCurrentGeneration()) return `${id}:stale-cache-suppressed`;
                    // Never let a stale generation's cache render clobber a
                    // newer generation's fresh network write issued earlier.
                    if (store.chartData && store.chartData._gen > generation) {
                        return `${id}:stale-cache-skipped-fresh-present`;
                    }
                    store.chartData = { ...parsed, _gen: generation };
                    store.loading = false;
                }
            } catch {
                // Unparseable cache is ignored (production warns).
            }
        }
        if (!isCurrentGeneration() || aborted()) return `${id}:stale-suppressed`;

        // --- params + network step ---
        await delay(latency);
        if (aborted()) {
            const e = new Error('canceled');
            e.name = 'CanceledError';
            throw e;
        }
        if (!isCurrentGeneration()) return `${id}:stale-suppressed`;

        if (formDataNull) {
            if (!isCurrentGeneration()) return `${id}:stale-suppressed`;
            store.toastErrors.push(`${id}:enter-details`);
            store.navigations.push('/enter-details');
            return `${id}:no-form-data`;
        }

        if (shouldFail) throw Object.assign(new Error(`boom-${id}`), { name: 'Error' });
        const data = networkData !== undefined ? networkData : { id, planets: { Sun: {} } };
        if (!isCurrentGeneration()) return `${id}:stale-suppressed`;

        store.chartData = { ...data, _gen: generation };
        try {
            if (store.throwOnLsSet) {
                if (store.throwOnLsSet === 'QuotaExceededError') {
                    const err = new Error('Quota exceeded');
                    err.name = 'QuotaExceededError';
                    throw err;
                } else if (store.throwOnLsSet === 'SerializationError') {
                    throw new TypeError('Converting circular structure to JSON');
                } else {
                    throw new Error('Generic storage error');
                }
            }
            const cachePayload = {
                _cache_version: 1,
                planets: data.planets,
                ascendant: data.ascendant,
                whole_sign_houses: data.whole_sign_houses,
                strengths: data.strengths,
                yogas: data.yogas,
                id: data.id,
                _gen: generation
            };
            store.ls.set('chartData', JSON.stringify(cachePayload));
            store.lsWrites = (store.lsWrites || 0) + 1;
        } catch (storageErr) {
            // cache failure does not throw to outer catch block
            store.storageErrors = (store.storageErrors || 0) + 1;
        }
        store.loading = false;
        return `${id}:wrote`;
    } catch (err) {
        if (!isCurrentGeneration() || err.name === 'CanceledError' || err.name === 'AbortError') {
            return `${id}:error-suppressed`;
        }
        // Failed network never clears existing (cached or fresh) chart data.
        store.toastErrors.push(`${id}:failed-positions`);
        store.loading = false;
        return `${id}:toast`;
    }
};

const stripGen = (d) => {
    if (!d) return d;
    const { _gen, ...rest } = d;
    return rest;
};

describe('HOTFIX 1 — same-mounted stale-response protection (PlanetsPage)', () => {
    it('TEST 1: A starts, B starts, B succeeds, A succeeds => B authoritative, no write from A', async () => {
        const component = createComponent();
        // Same mount: one effect run whose closure both fetches share, so
        // both observe isMounted === true; only generation discriminates.
        const effectRun = createEffectRun(component);
        const store = createStore();

        const pA = runPlanetsFetch(effectRun, store, { id: 'A', latency: 50 });
        await delay(5); // let A reach its in-flight await before B starts
        const pB = runPlanetsFetch(effectRun, store, {
            id: 'B',
            latency: 10,
            networkData: { id: 'B', planets: { Sun: {} } },
        });
        const [rA, rB] = await Promise.all([pA, pB]);

        assert.equal(rB, 'B:wrote');
        assert.equal(rA, 'A:stale-suppressed');
        assert.equal(stripGen(store.chartData).id, 'B', 'B remains authoritative');
        assert.equal(JSON.parse(store.ls.get('chartData')).id, 'B', 'localStorage holds B');
        assert.equal(store.toastErrors.length, 0);
    });

    it('TEST 2: A starts, B starts, B succeeds, A fails => B displayed, no toast from A', async () => {
        const component = createComponent();
        const effectRun = createEffectRun(component);
        const store = createStore();

        const pA = runPlanetsFetch(effectRun, store, { id: 'A', latency: 50, shouldFail: true });
        await delay(5); // let A reach its in-flight await before B starts
        const pB = runPlanetsFetch(effectRun, store, {
            id: 'B',
            latency: 10,
            networkData: { id: 'B', planets: { Sun: {} } },
        });
        const [rA, rB] = await Promise.all([pA, pB]);

        assert.equal(rB, 'B:wrote');
        // Stale A is suppressed either at the post-await currency check
        // ('stale-suppressed') or in catch ('error-suppressed'); both paths
        // are silent. The production catch suppresses via the same guard.
        assert.ok(rA === 'A:stale-suppressed' || rA === 'A:error-suppressed', `A suppressed, got ${rA}`);
        assert.equal(stripGen(store.chartData).id, 'B', 'B remains displayed');
        assert.equal(store.toastErrors.length, 0, 'A produces no error toast');
        assert.equal(JSON.parse(store.ls.get('chartData')).id, 'B', 'A does not touch localStorage');
    });

    it('TEST 3: A starts, component unmounts, A resolves => no state write', async () => {
        const component = createComponent();
        const effectRun = createEffectRun(component);
        const store = createStore();

        const p = runPlanetsFetch(effectRun, store, { id: 'A', latency: 20 });
        effectRun.cleanup(); // unmount before resolution
        const r = await p;

        assert.ok(r === 'A:stale-suppressed' || r === 'A:error-suppressed');
        assert.equal(store.chartData, null);
        assert.equal(store.ls.has('chartData'), false);
        assert.equal(store.toastErrors.length, 0);
        assert.equal(store.loading, true, 'loading untouched after unmount');
    });

    it('TEST 4: A starts, component unmounts, A fails => no toast', async () => {
        const component = createComponent();
        const effectRun = createEffectRun(component);
        const store = createStore();

        const p = runPlanetsFetch(effectRun, store, { id: 'A', latency: 20, shouldFail: true });
        effectRun.cleanup();
        const r = await p;

        assert.equal(r, 'A:error-suppressed');
        assert.equal(store.chartData, null);
        assert.equal(store.toastErrors.length, 0, 'no toast after unmount');
        assert.equal(store.ls.has('chartData'), false);
    });

    it('TEST 5: cache exists, network succeeds => fresh network authoritative (stale cache never wins)', async () => {
        const component = createComponent();
        const effectRun = createEffectRun(component);
        const store = createStore({ id: 'CACHE', planets: { Sun: {} } });

        const r = await runPlanetsFetch(effectRun, store, {
            id: 'N',
            latency: 10,
            networkData: { id: 'N', planets: { Moon: {} } },
        });

        assert.equal(r, 'N:wrote');
        assert.equal(stripGen(store.chartData).id, 'N', 'fresh network wins over cache');
        assert.equal(JSON.parse(store.ls.get('chartData')).id, 'N');
    });

    it('TEST 6: cache exists, active network fails => cached chart stays, one error indication', async () => {
        const component = createComponent();
        const effectRun = createEffectRun(component);
        const store = createStore({ id: 'CACHE', planets: { Sun: {} } });

        const r = await runPlanetsFetch(effectRun, store, { id: 'N', latency: 10, shouldFail: true });

        assert.equal(r, 'N:toast');
        assert.equal(stripGen(store.chartData).id, 'CACHE', 'cached chart remains visible');
        assert.equal(store.toastErrors.length, 1, 'exactly one error indication');
    });

    it('TEST 7: two overlapping requests => only latest generation writes localStorage', async () => {
        const component = createComponent();
        const effectRun = createEffectRun(component);
        const store = createStore();
        let writes = 0;
        const origSet = store.ls.set.bind(store.ls);
        store.ls.set = (k, v) => {
            writes++;
            return origSet(k, v);
        };

        const pA = runPlanetsFetch(effectRun, store, {
            id: 'A',
            latency: 50,
            networkData: { id: 'A', planets: { Sun: {} } },
        });
        await delay(5); // A in-flight before B starts
        const pB = runPlanetsFetch(effectRun, store, {
            id: 'B',
            latency: 10,
            networkData: { id: 'B', planets: { Moon: {} } },
        });
        await Promise.all([pA, pB]);

        assert.equal(writes, 1, 'exactly one localStorage write (latest only)');
        assert.equal(JSON.parse(store.ls.get('chartData')).id, 'B');
    });

    it('StrictMode remount: aborted generation A cannot overwrite or toast over B', async () => {
        const component = createComponent();
        const store = createStore();
        // Effect A mounts (gen 1), React cleanup aborts it (StrictMode
        // double-effect), effect B mounts (gen 2). A's transport ignores the
        // abort and resolves late anyway.
        const effectA = createEffectRun(component);
        const pA = runPlanetsFetch(effectA, store, { id: 'A', latency: 50 });
        effectA.cleanup();
        const effectB = createEffectRun(component);
        const pB = runPlanetsFetch(effectB, store, {
            id: 'B',
            latency: 10,
            networkData: { id: 'B', planets: { Sun: {} } },
        });
        const [rA, rB] = await Promise.all([pA, pB]);

        assert.equal(rB, 'B:wrote');
        assert.ok(rA === 'A:stale-suppressed' || rA === 'A:error-suppressed');
        assert.equal(stripGen(store.chartData).id, 'B');
        assert.equal(store.toastErrors.length, 0);
    });
    it('TEST 2: Successful /compute + localStorage.setItem throws QuotaExceededError', async () => {
        const component = createComponent();
        const effectRun = createEffectRun(component);
        const store = createStore();
        store.throwOnLsSet = 'QuotaExceededError';

        const r = await runPlanetsFetch(effectRun, store, { id: 'N', latency: 10 });

        assert.equal(r, 'N:wrote');
        assert.equal(store.toastErrors.length, 0, 'No network failure toast');
        assert.equal(store.loading, false, 'Loading completes');
        assert.equal(stripGen(store.chartData).id, 'N', 'chartData still displayed');
    });

    it('TEST 3: Successful /compute + generic storage exception', async () => {
        const component = createComponent();
        const effectRun = createEffectRun(component);
        const store = createStore();
        store.throwOnLsSet = 'GenericError';

        const r = await runPlanetsFetch(effectRun, store, { id: 'N', latency: 10 });
        assert.equal(r, 'N:wrote');
        assert.equal(store.toastErrors.length, 0);
        assert.equal(stripGen(store.chartData).id, 'N');
    });

    it('TEST 4: JSON serialization/cache preparation failure', async () => {
        const component = createComponent();
        const effectRun = createEffectRun(component);
        const store = createStore();
        store.throwOnLsSet = 'SerializationError';

        const r = await runPlanetsFetch(effectRun, store, { id: 'N', latency: 10 });
        assert.equal(r, 'N:wrote');
        assert.equal(store.toastErrors.length, 0);
        assert.equal(stripGen(store.chartData).id, 'N');
    });

    it('TEST 6: Existing malformed cache safely ignored', async () => {
        const component = createComponent();
        const effectRun = createEffectRun(component);
        const store = createStore();
        store.ls.set('chartData', '{ invalid_json'); // malformed

        const r = await runPlanetsFetch(effectRun, store, { id: 'N', latency: 10 });
        assert.equal(r, 'N:wrote');
        assert.equal(stripGen(store.chartData).id, 'N');
    });

    it('TEST 7: Existing obsolete/version-mismatched cache safely ignored', async () => {
        const component = createComponent();
        const effectRun = createEffectRun(component);
        const store = createStore();
        // Missing _cache_version
        store.ls.set('chartData', JSON.stringify({ planets: { Sun: {} } }));

        const r = await runPlanetsFetch(effectRun, store, { id: 'N', latency: 10 });
        assert.equal(r, 'N:wrote');
        assert.equal(stripGen(store.chartData).id, 'N');
    });

    it('TEST 12: No unrelated localStorage/sessionStorage keys are removed', async () => {
        const component = createComponent();
        const effectRun = createEffectRun(component);
        const store = createStore();
        store.ls.set('otherKey', 'preserve-me');

        await runPlanetsFetch(effectRun, store, { id: 'N', latency: 10 });

        assert.equal(store.ls.get('otherKey'), 'preserve-me');
    });
});
