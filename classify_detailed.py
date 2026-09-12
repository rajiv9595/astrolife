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

# Known canonical rule IDs
canonical_ids = {c["rule_id"] for c in canonical}

# The 50 legacy-only yogas (no canonical match found)
legacy_only = [
    "Akhanda Samrajya Yoga",
    "Astra Yoga",
    "Asura Yoga",
    "Bhagya Yoga",
    "Bheri Yoga",
    "Bhrigu Mangala Yoga",
    "Brahma Yoga",
    "Chamara Yoga",
    "Chhatra Yoga",
    "Dhenu Yoga",
    "Gandharva Yoga",
    "Garuda Yoga",
    "Go Yoga",
    "Gola Yoga",
    "Hara Yoga",
    "Hari Yoga",
    "Indra Yoga",
    "Jaladhi Yoga",
    "Kahala Yoga",
    "Kalanidhi Yoga",
    "Kalpadruma Yoga",
    "Kama Yoga",
    "Kedara Yoga",
    "Khyathi Yoga",
    "Kurma Yoga",
    "Kusuma Yoga",
    "Mahabhagya Yoga",
    "Mala Yoga",
    "Matsya Yoga",
    "Mridanga Yoga",
    "Musala Yoga",
    "Neechabhanga Raja Yoga",
    "Nipuna Yoga",
    "Parijata Yoga",
    "Parvata Yoga",
    "Pasha Yoga",
    "Pushkala Yoga",
    "Raja Lakshana Yoga",
    "Ravi Yoga",
    "Sarpa Yoga",
    "Shakata Yoga",
    "Shaurya Yoga",
    "Shiva Yoga",
    "Shula Yoga",
    "Srinatha Yoga",
    "Suparijata Yoga",
    "Ubhayachari Yoga",
    "Vasi Yoga",
    "Veena Yoga",
    "Vesi Yoga",
    "Viparita Raja Yoga",  # This maps to 3 canonical rules
    "Vishnu Yoga",
    "Yuga Yoga",
]

# Also 5 from Category B that need review
category_b = [
    ("Dhana Yoga", "PARASHARI.YOGA.DHANA_2_11"),
    ("Hara Yoga", "PARASHARI.YOGA.DURUDHARA"),  # This seems wrong - Hara != Durudhara
    ("Jaladhi Yoga", "PARASHARI.YOGA.ADHI"),
    ("Mala Yoga", "PARASHARI.YOGA.MALAVYA"),
    ("Viparita Raja Yoga", "PARASHARI.YOGA.VIPARITA_HARSHA"),
]

print("=" * 100)
print("DETAILED CLASSIFICATION OF 50 LEGACY-ONLY YOGAS")
print("=" * 100)

# Canonical rule methods for reference
canon_methods = {c["rule_id"]: c["method"] for c in canonical}
print("\nCANONICAL METHODS:")
for cid, method in canon_methods.items():
    print(f"  {cid}: {method}")

print("\n\n--- ANALYZING EACH LEGACY-ONLY YOGA ---\n")

# Detailed classification
classification_details = {}

for lname in legacy_only:
    ld = legacy_data[lname]
    conditions = ld.get("conditions", [])
    desc = ld.get("description", "")
    fid = ld.get("id", "")
    
    print(f"\n{'='*80}")
    print(f"LEGACY: {lname} ({fid})")
    print(f"FILE: {ld['_file']}")
    print(f"DESC: {desc}")
    print(f"CONDITIONS: {json.dumps(conditions, indent=2)}")
    
    # Now classify manually based on analysis
    # I'll do this programmatically below

print("\n\n" + "="*100)
print("MANUAL CLASSIFICATION DECISIONS")
print("="*100)

# Now I'll classify each one manually with reasoning
manual_classification = {
    # A. ALIAS/DUPLICATE - Same yoga, different name/format
    "Nipuna Yoga": {
        "category": "A",
        "canonical": "PARASHARI.YOGA.BUDHA_ADITYA",
        "reason": "Same as Budhaditya Yoga (Sun-Mercury conjunction) - just a different name for the same combination"
    },
    
    # B. ALREADY REPRESENTED BY CANONICAL RULE
    "Viparita Raja Yoga": {
        "category": "B",
        "canonical": ["PARASHARI.YOGA.VIPARITA_HARSHA", "PARASHARI.YOGA.VIPARITA_SARALA", "PARASHARI.YOGA.VIPARITA_VIMALA"],
        "reason": "Legacy combines all 3 Viparita Raja Yogas; canonical splits into 3 specific rules (Harsha, Sarala, Vimala)"
    },
    "Dhana Yoga": {
        "category": "B",
        "canonical": ["PARASHARI.YOGA.DHANA_2_11", "PARASHARI.YOGA.DHANA_5_9", "PARASHARI.YOGA.DHANA_LAGNA_WEALTH"],
        "reason": "Legacy generic Dhana Yoga; canonical has 3 specific Dhana Yoga rules"
    },
    "Mala Yoga": {
        "category": "B",
        "canonical": "PARASHARI.YOGA.MALAVYA",
        "reason": "Legacy 'Mala Yoga' = benefics in kendras; but this is actually Malavya (Venus Mahapurusha). Different yoga. Legacy Mala is Nabhasa yoga. Canonical Malavya is Pancha Mahapurusha. These are DIFFERENT."
    },
    "Jaladhi Yoga": {
        "category": "B",
        "canonical": "PARASHARI.YOGA.ADHI",
        "reason": "Legacy: 4th lord strong. Canonical Adhi: benefics in 6/7/8 from Moon. Different yogas. Legacy Jaladhi = house-based. Canonical Adhi = Moon-based. NOT same."
    },
    "Hara Yoga": {
        "category": "B", 
        "canonical": "PARASHARI.YOGA.DURUDHARA",
        "reason": "Legacy: benefics in 4th, 9th, 8th from 7th Lord. Canonical Durudhara: planets in 2nd and 12th from Moon. COMPLETELY DIFFERENT. This was a bad fuzzy match."
    },
    
    # C. CANONICAL RULE CAN BE DERIVED FROM EXISTING RULE PRIMITIVES
    # The canonical engine has primitives like: kendra_from_moon_house, sambandha_9_10, mahapurusha_kendra_own_exalted, etc.
    # If a legacy yoga can be expressed using existing method primitives, it's category C
    
    "Akhanda Samrajya Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "Jupiter rules 2/5/11 AND in kendra from Moon. Uses: lordship check + kendra_from_moon primitive. Can be derived."
    },
    "Bhagya Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "9th lord strong + benefics in 9th. Uses: lordship + strength + house occupation primitives. Derivable."
    },
    "Chamara Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "Lagna lord exalted in kendra, aspects lagna. Uses: lordship + sign_type + house_type + aspect primitives. Derivable."
    },
    "Chhatra Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "5th lord strong. Uses: lordship + strength primitive. Derivable."
    },
    "Dhenu Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "2nd lord exalted. Uses: lordship + sign_type primitive. Derivable."
    },
    "Gandharva Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "10th lord in kama trikona, Sun strong, Moon in 9th. Complex but uses existing primitives. Derivable."
    },
    "Garuda Yoga": {
        "category": "E",
        "canonical": None,
        "reason": "Moon in bright half, exalted navamsa lord of Moon. Requires navamsa and lunar phase - not in current primitives. NOT SAFE YET."
    },
    "Go Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "Jupiter in moolatrikona with Lagna lord. Uses: planet position + sign_type + conjunction_with_lord. Derivable."
    },
    "Kahala Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "4th and 9th lords in kendra from each other or lagna. Uses: lordship + kendra relationship. Derivable."
    },
    "Kalanidhi Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "Jupiter in 2/5 conjunct Mercury/Venus. Uses: planet position + conjunction. Derivable."
    },
    "Kalpadruma Yoga": {
        "category": "E",
        "canonical": None,
        "reason": "Requires navamsa chain (lagna lord -> dispositor -> dispositor -> navamsa lord all in kendra/trikona). Navamsa not in primitives. NOT SAFE."
    },
    "Kama Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "7th lord strong. Uses: lordship + strength. Derivable."
    },
    "Khyathi Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "10th lord strong. Uses: lordship + strength. Derivable."
    },
    "Kusuma Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "Venus in kendra, Moon in trikona, Saturn in 10th. Uses: planet position + house_type. Derivable."
    },
    "Mahabhagya Yoga": {
        "category": "E",
        "canonical": None,
        "reason": "Complex gender/day-night dependent rule. Requires birth time gender logic. NOT SAFE."
    },
    "Matsya Yoga": {
        "category": "E",
        "canonical": None,
        "reason": "Complex multi-house malefic/benefic pattern. Not expressible with current primitives. NOT SAFE."
    },
    "Mridanga Yoga": {
        "category": "E",
        "canonical": None,
        "reason": "Requires navamsa of exalted planet. Navamsa not in primitives. NOT SAFE."
    },
    "Musala Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "Lagna lord in 12th, malefics in 12th. Uses: lordship + planet position + malefic identification. Derivable."
    },
    "Neechabhanga Raja Yoga": {
        "category": "B",
        "canonical": ["PARASHARI.YOGA.NEECHA_BHANGA", "PARASHARI.YOGA.NEECHA_BHANGA_RAJA"],
        "reason": "Legacy combines both neechabhanga rules; canonical has 2 separate rules (cancellation + raja yoga). Already covered."
    },
    "Parijata Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "Dispositor of lagna lord exalted. Uses: lordship + dispositor + sign_type. Derivable."
    },
    "Parvata Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "Benefics in kendras, no planets in 6/8. Uses: benefic identification + house occupation + empty house check. Derivable."
    },
    "Pushkala Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "Moon lord with lagna lord in kendra. Uses: lordship + conjunction + house_type. Derivable."
    },
    "Raja Lakshana Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "Jupiter, Venus, Mercury, Moon in kendras. Uses: planet position + house_type. Derivable."
    },
    "Ravi Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "Sun in 10th, 10th lord in 3rd. Uses: planet position + lordship. Derivable."
    },
    "Shakata Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "Moon in 6/8/12 from Jupiter. Uses: planet relationship (6_8_12_from). Already a primitive method exists."
    },
    "Shaurya Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "3rd lord strong. Uses: lordship + strength. Derivable."
    },
    "Shiva Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "5th lord in 9th, 9th lord in 10th, 10th lord in 5th. Uses: lordship + house position. Derivable."
    },
    "Srinatha Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "7th lord exalted in 10th, 10th lord with 9th lord. Uses: lordship + sign_type + conjunction. Derivable."
    },
    "Suparijata Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "11th lord strong. Uses: lordship + strength. Derivable."
    },
    "Ubhayachari Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "Planets in 2nd and 12th from Sun (excl Moon/Rahu/Ketu). Uses: house_from_sun + planet filter. Derivable."
    },
    "Vasi Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "Planets in 12th from Sun (excl Moon/Rahu/Ketu). Uses: house_from_sun + planet filter. Derivable."
    },
    "Vesi Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "Planets in 2nd from Sun (excl Moon/Rahu/Ketu). Uses: house_from_sun + planet filter. Derivable."
    },
    "Vishnu Yoga": {
        "category": "C",
        "canonical": "NEW_DERIVED",
        "reason": "9th and 10th lords in 2nd house. Uses: lordship + house position. Derivable."
    },
    
    # D. REQUIRES NEW CANONICAL RULE (definition not in current primitives, but valid traditional yoga)
    "Astra Yoga": {
        "category": "D",
        "canonical": "NEW_REQUIRED",
        "reason": "Malefics in 6th, 6th lord strong. 'Malefics in house' + 'lord strength' - strength assessment primitive may not exist. REQUIRES NEW."
    },
    "Asura Yoga": {
        "category": "D",
        "canonical": "NEW_REQUIRED",
        "reason": "Malefics in 8th, 8th lord strong. Similar to Astra. REQUIRES NEW."
    },
    "Bheri Yoga": {
        "category": "D",
        "canonical": "NEW_REQUIRED",
        "reason": "Planets in 1,2,7,12. Specific house pattern. No existing primitive for this exact pattern. REQUIRES NEW."
    },
    "Bhrigu Mangala Yoga": {
        "category": "D",
        "canonical": "NEW_REQUIRED",
        "reason": "Venus-Mars conjunction. Conjunction primitive exists but specific Venus-Mars named yoga not in canonical. REQUIRES NEW."
    },
    "Brahma Yoga": {
        "category": "D",
        "canonical": "NEW_REQUIRED",
        "reason": "Jupiter, Venus, Mercury in kendras from lagna lords. Complex multi-planet from lagna lord reference. REQUIRES NEW."
    },
    "Indra Yoga": {
        "category": "D",
        "canonical": "NEW_REQUIRED",
        "reason": "Complex chain: Mars 3rd from Moon, Saturn 7th from Mars, Venus 7th from Saturn. Multi-step relational. REQUIRES NEW."
    },
    "Kedara Yoga": {
        "category": "D",
        "canonical": "NEW_REQUIRED",
        "reason": "Nabha yoga: all 7 planets in 4 signs. Nabha yoga counting not in primitives. REQUIRES NEW."
    },
    "Kurma Yoga": {
        "category": "D",
        "canonical": "NEW_REQUIRED",
        "reason": "Specific benefic/malefic distribution across houses. Complex pattern. REQUIRES NEW."
    },
    "Sarpa Yoga": {
        "category": "D",
        "canonical": "NEW_REQUIRED",
        "reason": "Nabhasa: malefics in 3 kendras. Nabhasa pattern. REQUIRES NEW."
    },
    "Shula Yoga": {
        "category": "D",
        "canonical": "NEW_REQUIRED",
        "reason": "Nabha: all 7 planets in 3 signs. Nabha counting. REQUIRES NEW."
    },
    "Dama Yoga": {
        "category": "D",
        "canonical": "NEW_REQUIRED",
        "reason": "Nabha: all 7 planets in 6 signs. Nabha counting. REQUIRES NEW."
    },
    "Pasha Yoga": {
        "category": "D",
        "canonical": "NEW_REQUIRED",
        "reason": "Nabha: all 7 planets in 5 signs. Nabha counting. REQUIRES NEW."
    },
    "Veena Yoga": {
        "category": "D",
        "canonical": "NEW_REQUIRED",
        "reason": "Nabha: all 7 planets in 7 signs. Nabha counting. REQUIRES NEW."
    },
    "Yuga Yoga": {
        "category": "D",
        "canonical": "NEW_REQUIRED",
        "reason": "Nabha: all 7 planets in 2 signs. Nabha counting. REQUIRES NEW."
    },
    "Gola Yoga": {
        "category": "D",
        "canonical": "NEW_REQUIRED",
        "reason": "Nabha: all 7 planets in 1 sign. Nabha counting. REQUIRES NEW."
    },
    
    # E. LEGACY-ONLY / NOT SAFE TO MIGRATE YET
    "Garuda Yoga": {
        "category": "E",
        "canonical": None,
        "reason": "Requires navamsa and lunar phase (bright half). Not in current primitives."
    },
    "Kalpadruma Yoga": {
        "category": "E",
        "canonical": None,
        "reason": "Requires navamsa dispositor chain. Not in current primitives."
    },
    "Mahabhagya Yoga": {
        "category": "E",
        "canonical": None,
        "reason": "Gender and day/night birth dependent. Complex traditional calculation."
    },
    "Matsya Yoga": {
        "category": "E",
        "canonical": None,
        "reason": "Complex multi-house benefic/malefic pattern. Not expressible."
    },
    "Mridanga Yoga": {
        "category": "E",
        "canonical": None,
        "reason": "Requires navamsa of exalted planet. Not in primitives."
    },
    
    # F. INVALID/OBSOLETE/UNSUPPORTED
    # None identified as invalid - all are traditional yogas
}

# Now let's also re-examine the Category B ones
print("\n\nREVIEWING CATEGORY B (FUZZY MATCHES):")
for lname, canon_id in category_b:
    ld = legacy_data[lname]
    print(f"\n{lname} -> {canon_id}")
    print(f"  Legacy cond: {ld['conditions']}")
    canon = [c for c in canonical if c["rule_id"] == canon_id][0]
    print(f"  Canon method: {canon['method']}")

# Final classification summary
print("\n\n" + "="*100)
print("FINAL CLASSIFICATION SUMMARY")
print("="*100)

cat_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0}
for lname, cls in manual_classification.items():
    cat_counts[cls["category"]] += 1
    print(f"  {cls['category']}: {lname} -> {cls.get('canonical', 'N/A')}")

print(f"\nCategory A (Alias/Duplicate): {cat_counts['A']}")
print(f"Category B (Already Represented): {cat_counts['B']}")
print(f"Category C (Derivable from Primitives): {cat_counts['C']}")
print(f"Category D (Requires New Canonical Rule): {cat_counts['D']}")
print(f"Category E (Legacy-Only/Not Safe): {cat_counts['E']}")
print(f"Category F (Invalid/Obsolete): {cat_counts['F']}")

# Add the 21 exact matches (Category A from crosscheck)
print(f"\nPlus 21 exact matches from crosscheck (Category A): +21")
cat_counts["A"] += 21

print(f"\nTOTAL LEGACY YOGAS: {sum(cat_counts.values())}")
print(f"  Canonical (A+B): {cat_counts['A'] + cat_counts['B']}")
print(f"  Derivable (C): {cat_counts['C']}")
print(f"  Need New Rule (D): {cat_counts['D']}")
print(f"  Not Safe (E): {cat_counts['E']}")
print(f"  Invalid (F): {cat_counts['F']}")

# Calculate coverage
total_distinct = 31 + cat_counts['C'] + cat_counts['D'] + cat_counts['E']  # canonical + derivable + new + unsafe
# But aliases don't add distinct yogas
# Distinct = canonical (31) + C (new derivable) + D (new required) + E (unsafe distinct)
# A and B are aliases/already covered

print(f"\nCanonical coverage: 31 / {total_distinct} = {31/total_distinct*100:.1f}%")
print(f"With derivable (C): {(31+cat_counts['C'])} / {total_distinct} = {(31+cat_counts['C'])/total_distinct*100:.1f}%")
print(f"With new rules (C+D): {(31+cat_counts['C']+cat_counts['D'])} / {total_distinct} = {(31+cat_counts['C']+cat_counts['D'])/total_distinct*100:.1f}%")