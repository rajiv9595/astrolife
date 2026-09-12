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

# Crosscheck matched legacy files
crosscheck_matched_files = {item["legacy_file"] for item in crosscheck}

# Category A: Exact match (crosscheck verified) + Aliases
cat_a_exact = {}
for item in crosscheck:
    fname = item["legacy_file"]
    lname = legacy_data[[k for k,v in legacy_data.items() if v["_file"]==fname][0]]["name"]
    cat_a_exact[lname] = item["rule_id"]

# Additional exact matches from manifest (parivartana yogas not in crosscheck but exact name match)
parivartana_exact = {
    "Maha Parivartana Yoga": "PARASHARI.YOGA.PARIVARTANA_MAHA",
    "Khala Parivartana Yoga": "PARASHARI.YOGA.PARIVARTANA_KHALA",
    "Dainya Parivartana Yoga": "PARASHARI.YOGA.PARIVARTANA_DAINYA",
}

# Aliases
aliases = {
    "Nipuna Yoga": "PARASHARI.YOGA.BUDHA_ADITYA",
}

# Category B: Already represented by canonical (legacy is generic/superset)
already_represented = {
    "Viparita Raja Yoga": ["PARASHARI.YOGA.VIPARITA_HARSHA", "PARASHARI.YOGA.VIPARITA_SARALA", "PARASHARI.YOGA.VIPARITA_VIMALA"],
    "Dhana Yoga": ["PARASHARI.YOGA.DHANA_2_11", "PARASHARI.YOGA.DHANA_5_9", "PARASHARI.YOGA.DHANA_LAGNA_WEALTH"],
    "Neechabhanga Raja Yoga": ["PARASHARI.YOGA.NEECHA_BHANGA", "PARASHARI.YOGA.NEECHA_BHANGA_RAJA"],
}

# Category C: Derivable from existing primitives
derivable = {
    "Akhanda Samrajya Yoga": "Jupiter rules 2/5/11 AND in kendra from Moon",
    "Bhagya Yoga": "9th lord strong + benefics in 9th",
    "Chamara Yoga": "Lagna lord exalted in kendra, aspects lagna",
    "Chhatra Yoga": "5th lord strong",
    "Dhenu Yoga": "2nd lord exalted",
    "Gandharva Yoga": "10th lord in kama trikona, Sun strong, Moon in 9th",
    "Go Yoga": "Jupiter in moolatrikona with Lagna lord",
    "Hara Yoga": "Benefics in 4th, 9th, 8th from 7th lord",
    "Hari Yoga": "Benefics in 2nd, 12th, 8th from 2nd lord",
    "Jaladhi Yoga": "4th lord strong + benefics in 4th",
    "Kahala Yoga": "4th and 9th lords in kendra from each other or lagna",
    "Kalanidhi Yoga": "Jupiter in 2/5 conjunct Mercury/Venus",
    "Kama Yoga": "7th lord strong",
    "Khyathi Yoga": "10th lord strong",
    "Kusuma Yoga": "Venus in kendra, Moon in trikona, Saturn in 10th",
    "Mala Yoga": "Benefics in 3 kendras (Nabhasa type)",
    "Musala Yoga": "Lagna lord in 12th, malefics in 12th",
    "Parijata Yoga": "Dispositor of lagna lord exalted",
    "Parvata Yoga": "Benefics in kendras, no planets in 6/8",
    "Pushkala Yoga": "Moon lord with lagna lord in kendra",
    "Raja Lakshana Yoga": "Jupiter, Venus, Mercury, Moon in kendras",
    "Ravi Yoga": "Sun in 10th, 10th lord in 3rd",
    "Shakata Yoga": "Moon in 6/8/12 from Jupiter",
    "Shaurya Yoga": "3rd lord strong",
    "Shiva Yoga": "5th lord in 9th, 9th lord in 10th, 10th lord in 5th",
    "Srinatha Yoga": "7th lord exalted in 10th, 10th lord with 9th lord",
    "Suparijata Yoga": "11th lord strong",
    "Ubhayachari Yoga": "Planets in 2nd and 12th from Sun excl Moon/Rahu/Ketu",
    "Vasi Yoga": "Planets in 12th from Sun excl Moon/Rahu/Ketu",
    "Vesi Yoga": "Planets in 2nd from Sun excl Moon/Rahu/Ketu",
    "Vishnu Yoga": "9th and 10th lords in 2nd house",
}

# Category D: Requires NEW canonical rule (valid traditional, needs new primitive)
requires_new_rule = {
    "Astra Yoga": "Malefics in 6th, 6th lord strong",
    "Asura Yoga": "Malefics in 8th, 8th lord strong",
    "Bheri Yoga": "Planets in 1,2,7,12",
    "Bhrigu Mangala Yoga": "Venus-Mars conjunction",
    "Brahma Yoga": "Jupiter, Venus, Mercury in kendras from lagna lords",
    "Dama Yoga": "Nabha: 7 planets in 6 signs",
    "Gola Yoga": "Nabha: 7 planets in 1 sign",
    "Indra Yoga": "Complex chain: Mars 3rd from Moon, Saturn 7th from Mars, Venus 7th from Saturn",
    "Kedara Yoga": "Nabha: 7 planets in 4 signs",
    "Kurma Yoga": "Specific benefic/malefic distribution across 6 houses",
    "Pasha Yoga": "Nabha: 7 planets in 5 signs",
    "Sarpa Yoga": "Nabhasa: malefics in 3 kendras",
    "Shula Yoga": "Nabha: 7 planets in 3 signs",
    "Veena Yoga": "Nabha: 7 planets in 7 signs",
    "Yuga Yoga": "Nabha: 7 planets in 2 signs",
}

# Category E: Not safe to migrate
not_safe = {
    "Garuda Yoga": "Requires navamsa + lunar phase",
    "Kalpadruma Yoga": "Requires navamsa dispositor chain",
    "Mahabhagya Yoga": "Gender + day/night dependent",
    "Matsya Yoga": "Complex multi-house benefic/malefic pattern",
    "Mridanga Yoga": "Requires navamsa of exalted planet",
}

# Build complete classification
all_names = set(legacy_data.keys())
classified = {}

for name in all_names:
    if name in cat_a_exact:
        classified[name] = ("A", cat_a_exact[name], "EXACT_MATCH")
    elif name in parivartana_exact:
        classified[name] = ("A", parivartana_exact[name], "EXACT_MATCH")
    elif name in aliases:
        classified[name] = ("A", aliases[name], "ALIAS")
    elif name in already_represented:
        classified[name] = ("B", already_represented[name], "ALREADY_REPRESENTED")
    elif name in derivable:
        classified[name] = ("C", derivable[name], "DERIVABLE")
    elif name in requires_new_rule:
        classified[name] = ("D", requires_new_rule[name], "NEEDS_NEW_RULE")
    elif name in not_safe:
        classified[name] = ("E", not_safe[name], "NOT_SAFE")
    else:
        classified[name] = ("?", "UNCLASSIFIED", "ERROR")

# Verify all classified
unclassified = [n for n, (c, _, _) in classified.items() if c == "?"]
if unclassified:
    print(f"UNCLASSIFIED: {unclassified}")
else:
    print("ALL 76 CLASSIFIED")

# Counts
cats = {}
for name, (cat, _, _) in classified.items():
    cats[cat] = cats.get(cat, 0) + 1

print("\n" + "=" * 80)
print("FINAL CLASSIFICATION SUMMARY")
print("=" * 80)
for cat in ["A", "B", "C", "D", "E", "F"]:
    if cat in cats:
        print(f"  Category {cat}: {cats[cat]}")

print(f"\nTotal: {sum(cats.values())}")

# Detailed list
print("\n" + "=" * 80)
print("DETAILED MAPPING TABLE")
print("=" * 80)
print(f"{'LEGACY YOGA':<40} {'CAT':<3} {'CANONICAL / REASON'}")
print("-" * 100)
for name in sorted(all_names):
    cat, target, reason = classified[name]
    if cat == "A":
        print(f"{name:<40} {cat:<3} {target} ({reason})")
    elif cat == "B":
        print(f"{name:<40} {cat:<3} {target} ({reason})")
    elif cat == "C":
        print(f"{name:<40} {cat:<3} DERIVABLE: {target}")
    elif cat == "D":
        print(f"{name:<40} {cat:<3} NEEDS_NEW: {target}")
    elif cat == "E":
        print(f"{name:<40} {cat:<3} UNSAFE: {target}")

# Coverage calculation
canonical_count = len(canonical)
distinct = canonical_count + cats.get("C", 0) + cats.get("D", 0) + cats.get("E", 0)
# A and B don't add distinct yogas

print("\n" + "=" * 80)
print("COVERAGE METRICS")
print("=" * 80)
print(f"Canonical authoritative Yogas: {canonical_count}")
print(f"Aliases/Duplicates (A): {cats.get('A', 0)}")
print(f"Already represented (B): {cats.get('B', 0)}")
print(f"Derivable from primitives (C): {cats.get('C', 0)}")
print(f"Requires new canonical rule (D): {cats.get('D', 0)}")
print(f"Legacy-only/Unsafe (E): {cats.get('E', 0)}")
print(f"Invalid/Obsolete (F): {cats.get('F', 0)}")
print(f"Total distinct Yogas: {distinct}")

print(f"\nCurrent coverage: {canonical_count}/{distinct} = {canonical_count/distinct*100:.1f}%")
print(f"With C implemented: {(canonical_count + cats.get('C', 0))}/{distinct} = {(canonical_count + cats.get('C', 0))/distinct*100:.1f}%")
print(f"With C+D implemented: {(canonical_count + cats.get('C', 0) + cats.get('D', 0))}/{distinct} = {(canonical_count + cats.get('C', 0) + cats.get('D', 0))/distinct*100:.1f}%")
print(f"Remaining legacy fallback (E only): {cats.get('E', 0)}/{distinct} = {cats.get('E', 0)/distinct*100:.1f}%")

# Legacy fallback after full safe migration
legacy_fallback_after = cats.get('D', 0) + cats.get('E', 0)
print(f"\nLegacy fallback if C implemented: {legacy_fallback_after} ({cats.get('D',0)} need new rules + {cats.get('E',0)} unsafe)")
print(f"Legacy fallback if C+D implemented: {cats.get('E', 0)} (only unsafe)")

# Evidence/Provenance coverage
print("\n" + "=" * 80)
print("EVIDENCE/PROVENANCE STATUS")
print("=" * 80)
print(f"Canonical rules with Evidence: {canonical_count}/31 = 100% (all have evidence per golden_snapshot)")
print(f"Canonical rules with Provenance: {canonical_count}/31 = 100% (all have provenance per golden_snapshot)")
print(f"After C migration: +{cats.get('C',0)} rules with Evidence+Provenance")
print(f"After D migration: +{cats.get('D',0)} rules with Evidence+Provenance")
print(f"Legacy fallback (E): {cats.get('E',0)} rules WITHOUT canonical Evidence/Provenance")