"""
Astrolife V2 — Phase 6A: Dynamic Rule Knowledge Specification Tests.

Covers schema, serialization, all DSL primitives, composition, UNKNOWN,
separation, provenance, versioning, registry, dependencies, cycles,
firewall, code rejection, tradition isolation, invalid schemas, the golden
synthetic rule (CUSTOM_DEVELOPER fixture, no classical claims), and 50-run
determinism. Synthetic fixtures only; no golden astrology touched.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.rules.dynamic import (
    SCHEMA_VERSION, PRIMITIVES, LOGICAL_OPS,
    RuleIdentity, RuleClassification, SourceReference, RuleProvenance,
    ConditionNode, RuleSemantics, RuleDependencies, RuleEvidenceSpec,
    RuleLifecycle, RuleValidationInfo, DynamicRuleDefinition,
    evaluate_rule, validate_rule, compare_versions,
    DuplicateVersionError, DynamicRuleRegistry,
    to_canonical_json, from_canonical_json, round_trip,
    find_suspicious_text,
)

total_tests = 0
passed_tests = 0
failed_tests = 0


def check(condition: bool, description: str):
    global total_tests, passed_tests, failed_tests
    total_tests += 1
    if condition:
        passed_tests += 1
        print(f"  OK {description}")
    else:
        failed_tests += 1
        print(f"  FAIL {description}")


def P(op, params=None, children=None, n=None):
    return ConditionNode(op=op, params=params or {}, children=children or [], n=n)


def golden_rule(**over):
    base = dict(
        identity=RuleIdentity(rule_id="DEMO.CUSTOM.SYNTHETIC_GOLDEN", rule_version="1.0.0",
                              rule_name="Synthetic Golden Fixture",
                              description="Infrastructure fixture only; not a classical rule."),
        classification=RuleClassification(system="CUSTOM", tradition="CUSTOM_DEVELOPER",
                                          category="FIXTURE", subcategory="GOLDEN"),
        provenance=RuleProvenance(
            source_reference=SourceReference(source_id="DEV-001", title="Developer fixture",
                                             author="Phase 6A harness", verification_status="USER_SUPPLIED"),
            source_type="CUSTOM", source_author="Phase 6A harness", source_title="Developer fixture",
            source_locator="test_dynamic_rules_phase6a.py", provenance_status="CUSTOM",
            confidence="CUSTOM"),
        semantics=RuleSemantics(
            prerequisites=["natal.Mars.sign"],
            formation=P("ALL", children=[
                P("planet_in_sign", {"planet": "Mars", "sign": "Aries"}),
                P("planet_in_varga_sign", {"planet": "Mars", "varga": "D9", "sign": "Aries"}),
                P("rule_formed", {"rule_id": "DEMO.CUSTOM.SUPPORT"}),
            ]),
            cancellation=P("planets_conjunct", {"a": "Mars", "b": "Saturn"}),
            mitigation=P("planets_aspect", {"a": "Jupiter", "b": "Mars"}),
            derived_facts=["demo.fixture.active"]),
        dependencies=RuleDependencies(
            input_facts=["natal.Mars.sign", "varga.D9.Mars", "natal.Saturn.sign",
                         "aspects.Jupiter", "natal.Mars.house"],
            rule_dependencies=["DEMO.CUSTOM.SUPPORT"],
            varga_dependencies=["D9"]),
        evidence=RuleEvidenceSpec(evidence_requirements=["formation"],
                                  evidence_paths=["semantics.formation"]),
        lifecycle=RuleLifecycle(status="ACTIVE"),
        validation=RuleValidationInfo(validation_status="VALID", test_requirements=["fixture"]),
    )
    base.update(over)
    return DynamicRuleDefinition(**base)


def support_rule():
    return DynamicRuleDefinition(
        identity=RuleIdentity(rule_id="DEMO.CUSTOM.SUPPORT", rule_version="1.0.0",
                              rule_name="Support Fixture", description="Rule-dependency target."),
        classification=RuleClassification(system="CUSTOM", tradition="CUSTOM_DEVELOPER",
                                          category="FIXTURE", subcategory="SUPPORT"),
        provenance=RuleProvenance(
            source_reference=SourceReference(source_id="DEV-002", verification_status="USER_SUPPLIED"),
            confidence="CUSTOM"),
        semantics=RuleSemantics(
            formation=P("planet_in_sign", {"planet": "Venus", "sign": "Taurus"})),
        dependencies=RuleDependencies(input_facts=["natal.Venus.sign"]),
        lifecycle=RuleLifecycle(status="ACTIVE"),
        validation=RuleValidationInfo(validation_status="VALID"),
    )


FACTS_FULL = {
    "natal.Mars.sign": "Aries", "natal.Mars.house": 1,
    "natal.Saturn.sign": "Capricorn", "natal.Venus.sign": "Taurus",
    "varga.D9.Mars": "Aries", "aspects.Jupiter": ["Mars", "Venus"],
    "rule:DEMO.CUSTOM.SUPPORT": "FORMED",
}


def resolver_for(facts):
    def resolve(path):
        if path in facts:
            return facts[path]
        raise KeyError(path)
    return resolve


# ---------------------------------------------------------------------------
# 1. Schema construction
# ---------------------------------------------------------------------------
print("\n--- 1. Schema ---")
g = golden_rule()
check(g.schema_version == "6A/1.0.0", "Schema version stamped")
check(g.identity.rule_id == "DEMO.CUSTOM.SYNTHETIC_GOLDEN", "Golden ID stable")
check(len(PRIMITIVES) == 22, f"22 supported primitives (got {len(PRIMITIVES)})")
check(LOGICAL_OPS == {"ALL", "ANY", "NOT", "EXACTLY_N", "AT_LEAST_N", "AT_MOST_N"},
      "Logical composition set exact")

# ---------------------------------------------------------------------------
# 2. Serialization round-trip + determinism
# ---------------------------------------------------------------------------
print("\n--- 2. Serialization ---")
s1 = to_canonical_json(g)
check(from_canonical_json(s1).identity.rule_id == g.identity.rule_id, "Deserialize preserves identity")
check(round_trip(s1) == s1, "Round-trip byte-identical")
s_reordered = to_canonical_json(golden_rule(
    dependencies=RuleDependencies(
        input_facts=["aspects.Jupiter", "natal.Mars.house", "natal.Mars.sign",
                     "natal.Saturn.sign", "varga.D9.Mars"],
        rule_dependencies=["DEMO.CUSTOM.SUPPORT"], varga_dependencies=["D9"])))
check(s_reordered == s1, "Semantically-unordered lists canonicalize (order-insensitive)")
check("utcnow" not in s1 and "datetime" not in s1.lower(), "No timestamps in serialization")

# ---------------------------------------------------------------------------
# 3. All primitives evaluate
# ---------------------------------------------------------------------------
print("\n--- 3. Primitives ---")
facts = dict(FACTS_FULL)
facts.update({
    "natal.Jupiter.sign": "Sagittarius", "natal.Jupiter.house": 9,
    "houses.9.lord": "Jupiter", "houses.1.lord": "Mars",
    "jaimini.drishti": {"Aries": ["Leo", "Scorpio", "Aquarius"]},
    "jaimini.karaka.AK": "Jupiter", "jaimini.pada.1": "Capricorn",
    "dignity.Mars": "OWN", "dasha.JAIMINI_CHARA.active_sign": "Taurus",
    "transit.Jupiter.sign": "Aries", "strength.shadbala.Jupiter": 1.2,
})
R = resolver_for(facts)
cases = [
    ("planet_in_sign", {"planet": "Mars", "sign": "Aries"}, "TRUE"),
    ("planet_in_house", {"planet": "Mars", "house": 1}, "TRUE"),
    ("planet_in_varga_sign", {"planet": "Mars", "varga": "D9", "sign": "Aries"}, "TRUE"),
    ("planet_owns_house", {"planet": "Mars", "house": 1}, "TRUE"),
    ("planets_conjunct", {"a": "Mars", "b": "Saturn"}, "FALSE"),
    ("planets_aspect", {"a": "Jupiter", "b": "Mars"}, "TRUE"),
    ("rashi_drishti", {"from_sign": "Aries", "to_sign": "Leo"}, "TRUE"),
    ("karaka_equals", {"karaka": "AK", "planet": "Jupiter"}, "TRUE"),
    ("pada_equals", {"house": 1, "sign": "Capricorn"}, "TRUE"),
    ("planet_exalted", {"planet": "Mars"}, "FALSE"),
    ("planet_debilitated", {"planet": "Mars"}, "FALSE"),
    ("planet_in_own_sign", {"planet": "Mars"}, "TRUE"),
    ("planet_in_moolatrikona", {"planet": "Mars"}, "FALSE"),
    ("house_is_kendra", {"house": 1}, "TRUE"),
    ("house_is_trikona", {"house": 9}, "TRUE"),
    ("lord_in_house", {"house": 9, "target_house": 9}, "TRUE"),
    ("lord_of_house", {"house": 1, "planet": "Mars"}, "TRUE"),
    ("dasha_active", {"system": "JAIMINI_CHARA", "sign": "Taurus"}, "TRUE"),
    ("transit_in_sign", {"planet": "Jupiter", "sign": "Aries"}, "TRUE"),
    ("transit_conjunct_natal", {"transit_planet": "Jupiter", "natal_planet": "Mars"}, "TRUE"),
    ("strength_threshold", {"planet": "Jupiter", "metric": "shadbala", "min": 1.0}, "TRUE"),
    ("rule_formed", {"rule_id": "DEMO.CUSTOM.SUPPORT"}, "TRUE"),
]
prim_ok = True
ALL_PATHS = ["natal.Mars.sign", "natal.Mars.house", "natal.Saturn.sign", "natal.Venus.sign",
             "natal.Jupiter.sign", "natal.Jupiter.house", "houses.9.lord", "houses.1.lord",
             "jaimini.drishti", "jaimini.karaka.AK", "jaimini.pada.1", "dignity.Mars",
             "dasha.JAIMINI_CHARA.active_sign", "transit.Jupiter.sign",
             "strength.shadbala.Jupiter", "varga.D9.Mars", "aspects.Jupiter"]


def case_rule(op, params, children=None, n=None):
    return golden_rule(
        semantics=RuleSemantics(formation=P(op, params, children, n)),
        dependencies=RuleDependencies(input_facts=list(ALL_PATHS),
                                      rule_dependencies=["DEMO.CUSTOM.SUPPORT"],
                                      varga_dependencies=["D9"]))


for op, params, exp in cases:
    out = evaluate_rule(case_rule(op, params), R)
    if out.formation != ({"TRUE": "FORMED", "FALSE": "NOT_FORMED"}[exp]):
        prim_ok = False
check(prim_ok, "All 22 primitives evaluate correctly (TRUE/FALSE)")
check(evaluate_rule(case_rule("AT_LEAST_N", None, [P("planet_in_sign", {"planet": "Mars", "sign": "Aries"}),
                                                   P("planet_in_sign", {"planet": "Mars", "sign": "Taurus"}),
                                                   P("planet_in_sign", {"planet": "Venus", "sign": "Taurus"})], 2),
                    R).formation == "FORMED",
    "AT_LEAST_N composition")
check(evaluate_rule(case_rule("EXACTLY_N", None, [P("planet_in_sign", {"planet": "Mars", "sign": "Aries"}),
                                                  P("planet_in_sign", {"planet": "Mars", "sign": "Taurus"})], 1),
                    R).formation == "FORMED",
    "EXACTLY_N composition")
check(evaluate_rule(case_rule("AT_MOST_N", None, [P("planet_in_sign", {"planet": "Mars", "sign": "Aries"}),
                                                  P("planet_in_sign", {"planet": "Mars", "sign": "Taurus"})], 1),
                    R).formation == "FORMED",
    "AT_MOST_N composition")
check(evaluate_rule(case_rule("NOT", None, [P("planet_in_sign", {"planet": "Mars", "sign": "Taurus"})]),
                    R).formation == "FORMED",
    "NOT composition")

# ---------------------------------------------------------------------------
# 4. UNKNOWN propagation + separation
# ---------------------------------------------------------------------------
print("\n--- 4. UNKNOWN & Separation ---")
thin = resolver_for({"natal.Mars.sign": "Aries"})
out = evaluate_rule(golden_rule(), thin)
check(out.formation == "UNKNOWN", "Missing D9/rule-dep facts yield UNKNOWN (not FALSE)")
check(out.cancellation in ("CANCELLED", "NOT_CANCELLED", "UNKNOWN"), "Cancellation independent state present")
check(out.mitigation in ("MITIGATED", "NOT_MITIGATED", "UNKNOWN"), "Mitigation independent state present")
full_out = evaluate_rule(golden_rule(), resolver_for(FACTS_FULL))
check(full_out.formation == "FORMED", "Golden fixture FORMED on full facts")
check(full_out.cancellation == "NOT_CANCELLED", "Golden cancellation separate (Mars/Saturn apart)")
check(full_out.mitigation == "MITIGATED", "Golden mitigation separate (Jupiter aspects Mars)")
check(full_out.diagnostics == [], "No undeclared-access diagnostics on golden")
check(len(full_out.evidence) >= 5, "Per-node evidence recorded")

# ---------------------------------------------------------------------------
# 5. Provenance
# ---------------------------------------------------------------------------
print("\n--- 5. Provenance ---")
check(validate_rule(golden_rule(), {"DEMO.CUSTOM.SUPPORT"}) == [], "Golden validates clean")
check(g.provenance.source_reference.verification_status == "USER_SUPPLIED", "Golden stays USER_SUPPLIED")
bad_src = golden_rule(provenance=RuleProvenance(
    source_reference=SourceReference(verification_status="VERIFIED"), confidence="HIGH"))
check(any(d.code == "PROVENANCE" for d in validate_rule(bad_src, {"DEMO.CUSTOM.SUPPORT"})),
      "VERIFIED without locator/quotation rejected")

# ---------------------------------------------------------------------------
# 6. Versioning + registry
# ---------------------------------------------------------------------------
print("\n--- 6. Versioning & Registry ---")
check(compare_versions("1.0.0", "1.1.0") == -1 and compare_versions("2.0.0", "1.9.9") == 1
      and compare_versions("1.0.0", "1.0.0") == 0, "Deterministic semver compare")
reg = DynamicRuleRegistry()
check(reg.register(support_rule()) == [], "Support rule registers")
check(reg.register(golden_rule()) == [], "Golden registers with dependency satisfied")
try:
    reg.register(golden_rule())
    check(False, "Duplicate version rejected")
except DuplicateVersionError:
    check(True, "Duplicate version rejected (immutability)")
v2 = golden_rule(identity=RuleIdentity(rule_id="DEMO.CUSTOM.SYNTHETIC_GOLDEN", rule_version="1.1.0",
                                       rule_name="Synthetic Golden Fixture", description="v1.1.0"))
check(reg.register(v2) == [], "New version registers (modification path)")
check(reg.list_versions("DEMO.CUSTOM.SYNTHETIC_GOLDEN") == ["1.0.0", "1.1.0"], "Version listing ordered")
check(reg.get("DEMO.CUSTOM.SYNTHETIC_GOLDEN").identity.rule_version == "1.1.0", "Latest-version retrieval")
check(len(reg.filter_by(tradition="CUSTOM_DEVELOPER")) == 2, "Filter by tradition (latest per ID)")
check(len(reg.filter_by(verification="USER_SUPPLIED")) == 2, "Filter by provenance")
check(reg.deprecate("DEMO.CUSTOM.SUPPORT", "1.0.0", "DEMO.CUSTOM.SUPPORT@2.0.0"), "Deprecate works")
check(reg.get("DEMO.CUSTOM.SUPPORT", "1.0.0").lifecycle.status == "DEPRECATED", "Deprecation recorded")
cyc = DynamicRuleRegistry()
ra = support_rule().model_copy(update={"identity": RuleIdentity(
    rule_id="DEMO.CUSTOM.A", rule_version="1.0.0", rule_name="A", description="a"),
    "dependencies": support_rule().dependencies.model_copy(update={"rule_dependencies": ["DEMO.CUSTOM.B"]})})
rb = support_rule().model_copy(update={"identity": RuleIdentity(
    rule_id="DEMO.CUSTOM.B", rule_version="1.0.0", rule_name="B", description="b"),
    "dependencies": support_rule().dependencies.model_copy(update={"rule_dependencies": ["DEMO.CUSTOM.A"]})})
cyc.register(ra, {"DEMO.CUSTOM.A", "DEMO.CUSTOM.B"})
cyc.register(rb, {"DEMO.CUSTOM.A", "DEMO.CUSTOM.B"})
check(any(d.code == "CYCLE" for d in cyc.validate_graph()), "Registry cycle detection flags A<->B")

# ---------------------------------------------------------------------------
# 7. Dependencies, firewall, invalid schemas
# ---------------------------------------------------------------------------
print("\n--- 7. Dependencies & Firewall ---")
undecl = golden_rule(dependencies=RuleDependencies(input_facts=["natal.Mars.sign"]))
out_u = evaluate_rule(undecl, resolver_for(FACTS_FULL))
check(any(d.startswith("UNDECLARED_ACCESS") for d in out_u.diagnostics), "Undeclared access flagged at evaluation")
fw = golden_rule(classification=RuleClassification(system="X", tradition="JAIMINI_CLASSICAL",
                                                   category="Y", subcategory="Z"),
                 dependencies=RuleDependencies(input_facts=["natal.Mars.sign", "western.foo"]))
check(any(d.code == "FIREWALL" for d in validate_rule(fw, set())), "JAIMINI firewall rejects western.* namespace")
bad_planet = golden_rule(semantics=RuleSemantics(
    formation=P("planet_in_sign", {"planet": "Pluto", "sign": "Aries"})))
check(any(d.code == "VOCABULARY" for d in validate_rule(bad_planet, {"DEMO.CUSTOM.SUPPORT"})),
      "Invalid planet rejected")
bad_op = golden_rule(semantics=RuleSemantics(formation=P("compute_anything", {"x": 1})))
check(any(d.code == "CONDITION" for d in validate_rule(bad_op, {"DEMO.CUSTOM.SUPPORT"})),
      "Unknown op rejected")
missing_dep = golden_rule(dependencies=RuleDependencies(input_facts=["natal.Mars.sign"],
                                                        rule_dependencies=["NOPE.MISSING.RULE"]))
check(any(d.code == "DEPENDENCY" for d in validate_rule(missing_dep, {"DEMO.CUSTOM.SUPPORT"})),
      "Unknown rule dependency rejected")
self_dep = golden_rule(dependencies=RuleDependencies(
    input_facts=["natal.Mars.sign"], rule_dependencies=["DEMO.CUSTOM.SYNTHETIC_GOLDEN"]))
check(any(d.code == "CYCLE" for d in validate_rule(self_dep, {"DEMO.CUSTOM.SYNTHETIC_GOLDEN"})),
      "Self-dependency cycle rejected")

# ---------------------------------------------------------------------------
# 8. Security
# ---------------------------------------------------------------------------
print("\n--- 8. Security ---")
payloads = ["eval(__import__('os').system('rm -rf /'))", "exec(open('/etc/passwd').read())",
            "__import__('subprocess')", "import os; os.system('x')", "lambda x: x",
            "`rm -rf /`", "$(reboot)", "SELECT * FROM users", "open('/etc/passwd')",
            "a.__class__.__subclasses__()", "requests.get('http://evil')"]
sec_ok = True
for pl in payloads:
    evil = golden_rule(semantics=RuleSemantics(formation=P("planet_in_sign", {"planet": "Mars", "sign": pl})))
    if not any(d.code == "ARBITRARY_CODE" for d in validate_rule(evil, {"DEMO.CUSTOM.SUPPORT"})):
        sec_ok = False
check(sec_ok, "All executable payload classes rejected (eval/exec/import/lambda/shell/SQL)")
check(find_suspicious_text("Mars is important for execution policy text") == [],
      "No false positives on benign prose")
# Evaluator never executes: payload as data resolves by equality only
out_evil = evaluate_rule(golden_rule(semantics=RuleSemantics(
    formation=P("planet_in_sign", {"planet": "Mars", "sign": "Aries"}))),
    resolver_for({"natal.Mars.sign": "eval(1)"}))
check(out_evil.formation == "NOT_FORMED", "Payload strings are inert data (equality only)")

# ---------------------------------------------------------------------------
# 9. Tradition isolation
# ---------------------------------------------------------------------------
print("\n--- 9. Tradition Isolation ---")
west = golden_rule(
    identity=RuleIdentity(rule_id="DEMO.WESTERN.X", rule_version="1.0.0", rule_name="X", description="x"),
    classification=RuleClassification(system="W", tradition="WESTERN", category="C", subcategory="S"),
    dependencies=RuleDependencies(input_facts=["natal.Mars.sign", "jaimini.karaka.AK"]))
check(any(d.code == "FIREWALL" for d in validate_rule(west, set())), "WESTERN cannot read jaimini.*")
check(len(reg.filter_by(category="FIXTURE")) == 2, "Filter by category")

# ---------------------------------------------------------------------------
# 10. Determinism (50 runs)
# ---------------------------------------------------------------------------
print("\n--- 10. Determinism ---")
R50 = resolver_for(FACTS_FULL)
first = (to_canonical_json(golden_rule()),
         evaluate_rule(golden_rule(), R50).model_dump_json())
det_ok = True
for _ in range(50):
    if (to_canonical_json(golden_rule()),
            evaluate_rule(golden_rule(), R50).model_dump_json()) != first:
        det_ok = False
        break
check(det_ok, "50 runs: same bytes, same outcome, same evidence")

# ---------------------------------------------------------------------------
# RESULTS
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print(f"PHASE 6A TEST RESULTS: {passed_tests} passed, {failed_tests} failed out of {total_tests} total")
print("=" * 70)
sys.exit(1 if failed_tests else 0)
