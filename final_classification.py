import json
from pathlib import Path

# Load all legacy yoga files
legacy_dir = Path(r"C:\Users\RAJIV MEDAPATI\Documents\projects\lifepath\backend\rulesets\yogas")
legacy_files = sorted(legacy_dir.glob("*.json"))

legacy_data = {}
for lf in legacy_files:
    with open(lf) as f:
        data = json.load(f)
        data["_file"] = lf.name
        legacy_data[data["name"]] = data

# Load canonical manifest
with open(r"C:\Users\RAJIV MEDAPATI\Documents\projects\lifepath\backend\core\rules\parashari\manifest.json") as f:
    canonical = json.load(f)

# Load crosscheck
with open(r"C:\Users\RAJIV MEDAPATI\Documents\projects\lifepath\backend\core\rules\parashari\crosscheck.json") as f:
    crosscheck = json.load(f)

crosscheck_map = {item["rule_id"]: item for item in crosscheck}

# CORRECTED CLASSIFICATION
# Based on actual analysis of conditions and canonical primitives

print("=" * 100)
print("CORRECTED FINAL CLASSIFICATION")
print("=" * 100)

# Start with crosscheck verified matches (21 exact)
crosscheck_matched = set()
for item in crosscheck:
    crosscheck_matched.add(item["legacy_file"])

print(f"\nCROSSCHECK VERIFIED (21) - Category A (Exact Match):")
for item in crosscheck:
    print(f"  {item['legacy_file']} -> {item['rule_id']} ({item['verdict']})")

# Category A: Alias/Duplicate (same yoga, different name)
aliases = {
    "Nipuna Yoga": "PARASHARI.YOGA.BUDHA_ADITYA",  # Same as Budhaditya (Sun-Mercury)
}

# Category B: Already represented by canonical rule(s) (legacy is generic/superset)
already_represented = {
    "Viparita Raja Yoga": ["PARASHARI.YOGA.VIPARITA_HARSHA", "PARASHARI.YOGA.VIPARITA_SARALA", "PARASHARI.YOGA.VIPARITA_VIMALA"],
    "Dhana Yoga": ["PARASHARI.YOGA.DHANA_2_11", "PARASHARI.YOGA.DHANA_5_9", "PARASHARI.YOGA.DHANA_LAGNA_WEALTH"],
    "Neechabhanga Raja Yoga": ["PARASHARI.YOGA.NEECHA_BHANGA", "PARASHARI.YOGA.NEECHA_BHANGA_RAJA"],
}

# Category C: Derivable from existing canonical primitives
# These use combinations of: lordship, house position, sign_type, conjunction, aspect, strength, kendra/trikona, moon/sun relationships
derivable = {
    "Akhanda Samrajya Yoga": "Jupiter rules 2/5/11 AND in kendra from Moon (lordship + kendra_from_moon)",
    "Bhagya Yoga": "9th lord strong + benefics in 9th (lordship + strength + house_occupation)",
    "Chamara Yoga": "Lagna lord exalted in kendra, aspects lagna (lordship + sign_type + house_type + aspect)",
    "Chhatra Yoga": "5th lord strong (lordship + strength)",
    "Dhenu Yoga": "2nd lord exalted (lordship + sign_type)",
    "Gandharva Yoga": "10th lord in kama trikona, Sun strong, Moon in 9th (lordship + house_type + strength)",
    "Go Yoga": "Jupiter in moolatrikona with Lagna lord (planet + sign_type + conjunction_with_lord)",
    "Hara Yoga": "Benefics in 4th, 9th, 8th from 7th lord (lordship + house_from_planet + benefic_id)",
    "Jaladhi Yoga": "4th lord strong + benefics in 4th (lordship + strength + house_occupation + benefic_id)",
    "Kahala Yoga": "4th and 9th lords in kendra from each other or lagna (lordship + kendra_relationship)",
    "Kalanidhi Yoga": "Jupiter in 2/5 conjunct Mercury/Venus (planet + house + conjunction)",
    "Kama Yoga": "7th lord strong (lordship + strength)",
    "Khyathi Yoga": "10th lord strong (lordship + strength)",
    "Kusuma Yoga": "Venus in kendra, Moon in trikona, Saturn in 10th (planet + house_type)",
    "Mala Yoga": "Benefics in 3 kendras (benefic_id + house_type + count) - Nabhasa type",
    "Musala Yoga": "Lagna lord in 12th, malefics in 12th (lordship + house + malefic_id)",
    "Parijata Yoga": "Dispositor of lagna lord exalted (lordship + dispositor + sign_type)",
    "Parvata Yoga": "Benefics in kendras, no planets in 6/8 (benefic_id + house_type + empty_house_check)",
    "Pushkala Yoga": "Moon lord with lagna lord in kendra (lordship + conjunction + house_type)",
    "Raja Lakshana Yoga": "Jupiter, Venus, Mercury, Moon in kendras (planet + house_type)",
    "Ravi Yoga": "Sun in 10th, 10th lord in 3rd (planet + lordship + house)",
    "Shakata Yoga": "Moon in 6/8/12 from Jupiter (planet_relationship_6_8_12) - PRIMITIVE EXISTS",
    "Shaurya Yoga": "3rd lord strong (lordship + strength)",
    "Shiva Yoga": "5th lord in 9th, 9th lord in 10th, 10th lord in 5th (lordship + house_position)",
    "Srinatha Yoga": "7th lord exalted in 10th, 10th lord with 9th lord (lordship + sign_type + conjunction)",
    "Suparijata Yoga": "11th lord strong (lordship + strength)",
    "Ubhayachari Yoga": "Planets in 2nd and 12th from Sun excl Moon/Rahu/Ketu (house_from_sun + planet_filter)",
    "Vasi Yoga": "Planets in 12th from Sun excl Moon/Rahu/Ketu (house_from_sun + planet_filter)",
    "Vesi Yoga": "Planets in 2nd from Sun excl Moon/Rahu/Ketu (house_from_sun + planet_filter)",
    "Vishnu Yoga": "9th and 10th lords in 2nd house (lordship + house_position)",
}

# Category D: Requires NEW canonical rule (valid traditional yoga but needs new primitive/method)
# These need Nabha yoga counting, or complex patterns not in current primitives
requires_new_rule = {
    "Astra Yoga": "Malefics in 6th, 6th lord strong - needs 'malefics_in_house' + strength primitive",
    "Asura Yoga": "Malefics in 8th, 8th lord strong - similar to Astra",
    "Bheri Yoga": "Planets in 1,2,7,12 - specific house pattern, no primitive",
    "Bhrigu Mangala Yoga": "Venus-Mars conjunction - specific named conjunction yoga",
    "Brahma Yoga": "Jupiter, Venus, Mercury in kendras from lagna lords - complex multi-ref",
    "Indra Yoga": "Complex chain: Mars 3rd from Moon, Saturn 7th from Mars, Venus 7th from Saturn",
    "Kedara Yoga": "Nabha: 7 planets in 4 signs - needs nabha counting primitive",
    "Kurma Yoga": "Specific benefic/malefic distribution across 6 houses - complex pattern",
    "Sarpa Yoga": "Nabhasa: malefics in 3 kendras - nabha type",
    "Shula Yoga": "Nabha: 7 planets in 3 signs - nabha counting",
    "Dama Yoga": "Nabha: 7 planets in 6 signs - nabha counting",
    "Pasha Yoga": "Nabha: 7 planets in 5 signs - nabha counting",
    "Veena Yoga": "Nabha: 7 planets in 7 signs - nabha counting",
    "Yuga Yoga": "Nabha: 7 planets in 2 signs - nabha counting",
    "Gola Yoga": "Nabha: 7 planets in 1 sign - nabha counting",
}

# Category E: Legacy-only / Not safe to migrate (requires navamsa, lunar phase, gender, etc)
not_safe = {
    "Garuda Yoga": "Requires navamsa (exalted navamsa lord of Moon) and lunar phase (bright half)",
    "Kalpadruma Yoga": "Requires navamsa dispositor chain (lagna lord -> dispositor -> dispositor -> navamsa lord)",
    "Mahabhagya Yoga": "Gender and day/night birth dependent - complex traditional calculation",
    "Matsya Yoga": "Complex multi-house benefic/malefic pattern across 6 houses",
    "Mridanga Yoga": "Requires navamsa (lord of navamsa of exalted planet)",
}

# Category F: Invalid/Obsolete - None identified

# Now let's count properly
all_legacy_names = set(legacy_data.keys())
print(f"\nTotal legacy yoga definitions: {len(all_legacy_names)}")

# Categorize each
cat_a = set()  # Alias/Duplicate
cat_b = set()  # Already represented
cat_c = set()  # Derivable
cat_d = set()  # Requires new rule
cat_e = set()  # Not safe

for name in all_legacy_names:
    if name in aliases:
        cat_a.add(name)
    elif name in already_represented:
        cat_b.add(name)
    elif name in derivable:
        cat_c.add(name)
    elif name in requires_new_rule:
        cat_d.add(name)
    elif name in not_safe:
        cat_e.add(name)
    else:
        # Check if it's in crosscheck matched
        fname = legacy_data[name]["_file"]
        if fname in crosscheck_matched:
            cat_a.add(name)  # Crosscheck verified = canonical match
        else:
            print(f"  UNCLASSIFIED: {name} ({fname})")

print(f"\nCategory A (Alias/Duplicate + Crosscheck Exact): {len(cat_a)}")
for n in sorted(cat_a):
    if n in aliases:
        print(f"  ALIAS: {n} -> {aliases[n]}")
    else:
        fname = legacy_data[n]["_file"]
        cc = crosscheck_map.get([c for c in crosscheck if c["legacy_file"] == fname][0]["rule_id"] if any(c["legacy_file"] == fname for c in crosscheck) else None, {})
        print(f"  EXACT: {n} -> {cc.get('rule_id', '?')}")

print(f"\nCategory B (Already Represented by Canonical): {len(cat_b)}")
for n in sorted(cat_b):
    print(f"  {n} -> {already_represented[n]}")

print(f"\nCategory C (Derivable from Primitives): {len(cat_c)}")
for n in sorted(cat_c):
    print(f"  {n}: {derivable[n]}")

print(f"\nCategory D (Requires New Canonical Rule): {len(cat_d)}")
for n in sorted(cat_d):
    print(f"  {n}: {requires_new_rule[n]}")

print(f"\nCategory E (Legacy-Only / Not Safe): {len(cat_e)}")
for n in sorted(cat_e):
    print(f"  {n}: {not_safe[n]}")

print(f"\nCategory F (Invalid/Obsolete): 0")

# Summary
print("\n" + "=" * 100)
print("COVERAGE CALCULATION")
print("=" * 100)

canonical_count = len(canonical)  # 31
# Distinct yogas = canonical (31) + derivable new (C) + requires_new (D) + not_safe (E)
# A and B are aliases/already-covered, don't add distinct count
distinct_yogas = canonical_count + len(cat_c) + len(cat_d) + len(cat_e)
print(f"Canonical authoritative Yogas: {canonical_count}")
print(f"New derivable (C): {len(cat_c)}")
print(f"New required rules (D): {len(cat_d)}")
print(f"Unsafe/legacy-only (E): {len(cat_e)}")
print(f"Aliases/duplicates (A): {len(cat_a)}")
print(f"Already represented (B): {len(cat_b)}")
print(f"Total distinct Yogas: {distinct_yogas}")

coverage_now = canonical_count / distinct_yogas * 100
coverage_with_c = (canonical_count + len(cat_c)) / distinct_yogas * 100
coverage_with_cd = (canonical_count + len(cat_c) + len(cat_d)) / distinct_yogas * 100

print(f"\nCurrent canonical coverage: {canonical_count}/{distinct_yogas} = {coverage_now:.1f}%")
print(f"With derivable (C) implemented: {(canonical_count + len(cat_c))}/{distinct_yogas} = {coverage_with_c:.1f}%")
print(f"With new rules (C+D) implemented: {(canonical_count + len(cat_c) + len(cat_d))}/{distinct_yogas} = {coverage_with_cd:.1f}%")
print(f"Remaining legacy fallback (E): {len(cat_e)}/{distinct_yogas} = {len(cat_e)/distinct_yogas*100:.1f}%")

# Also show legacy fallback count
legacy_fallback = len(cat_e) + len(cat_d)  # D needs new rules, E unsafe
print(f"\nLegacy fallback remaining if only C implemented: {len(cat_d) + len(cat_e)} ({len(cat_d)} need new rules, {len(cat_e)} unsafe)")
print(f"Legacy fallback remaining if C+D implemented: {len(cat_e)} (only unsafe)")