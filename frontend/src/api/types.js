/**
 * JSDoc type contracts for canonical backend responses — Phase 11.
 * The project uses plain JavaScript (no TypeScript build); these typedefs
 * document the API map for editors and reviewers. Types never calculate.
 *
 * Coverage: ChartFacts, VargaFacts, Panchanga, Vimshottari Dasha,
 * Chara Dasha, Transit, Strength (Shadbala/Bhava/Vimsopaka/Avastha/Dignity),
 * Yoga, Dosha, Jaimini (Karakas/Drishti/Arudhas), RuleResult, Evidence,
 * AgentResult, Prediction (EVENT_WINDOW), Research (EXPERIMENTAL).
 *
 * @typedef {Object} PlanetPosition
 * @property {string} sign
 * @property {number} longitude
 * @property {number} [house]
 * @property {{nakshatra: string, pada: number}} [nakshatra]
 * @property {boolean} [retrograde]
 * @property {string} [star_lord]
 *
 * @typedef {Object} ComputeResponse
 * @property {string} [jd_ut]
 * @property {number} [ayanamsha_deg]
 * @property {Object.<string, PlanetPosition>} planets
 * @property {{sign: string}} ascendant
 * @property {object} [whole_sign_houses]
 * @property {object} [vargas]
 * @property {object} [vimshottari]
 * @property {object} [nakshatra_of_moon]
 * @property {Array} [yogas]
 * @property {object} [strengths]
 * @property {object} [jaimini]
 * @property {object} [ashtakavarga]
 * @property {object} [shadbala]
 * @property {object} [maitri]
 * @property {object} [panchanga_advanced]
 * @property {object} [advanced_doshas]
 * @property {string} [moon_sign]
 * @property {string} [tithi]
 * @property {string} [karana]
 *
 * @typedef {Object} DynamicStateResponse
 * @property {object} [dasha]
 * @property {object} [panchanga]
 * @property {object} [transits]
 *
 * @typedef {Object} YogaResult
 * @property {string} [rule_id]
 * @property {string} [name]
 * @property {string} [tradition]
 * @property {string} formation - FORMED | NOT_FORMED | UNKNOWN | INVALID | CONFLICTED | UNSUPPORTED
 * @property {string} [strength]
 * @property {string} [cancellation]
 * @property {string} [mitigation]
 * @property {Array} [evidence]
 * @property {object} [provenance]
 *
 * @typedef {Object} DoshaResult
 * @property {string} formation
 * @property {string} [severity]
 * @property {string} [mitigation]
 * @property {string} [tradition]
 *
 * @typedef {Object} AgentResult
 * @property {string} [agent]
 * @property {string} [status]
 * @property {object} [provenance]
 * @property {string} [uncertainty]
 *
 * @typedef {Object} PredictionEvent
 * @property {string} [event_category]
 * @property {string} [status]
 * @property {object} [timing_window]
 * @property {object} [evidence]
 * @property {string} [uncertainty]
 *
 * @typedef {Object} ResearchRuleView
 * @property {string} rule_id
 * @property {string} rule_version
 * @property {string} lifecycle_status - EXPERIMENTAL | TESTED | PROMOTED | ...
 * @property {string} [tradition]
 *
 * @typedef {Object} NormalizedApiError
 * @property {string} kind - VALIDATION_ERROR | NOT_FOUND | UNAVAILABLE | INVALID_INPUT | CONFLICT | UNKNOWN | INTERNAL_ERROR
 * @property {string} message
 * @property {number} [httpStatus]
 * @property {unknown} [detail]
 */

export const TYPE_CONTRACT_VERSION = '11.0.0';
