import json
from pathlib import Path

# Legacy yoga files
legacy_dir = Path(r"C:\Users\RAJIV MEDAPATI\Documents\projects\lifepath\backend\rulesets\yogas")
legacy_files = sorted(legacy_dir.glob("*.json"))

# Load canonical manifest
with open(r"C:\Users\RAJIV MEDAPATI\Documents\projects\lifepath\backend\core\rules\parashari\manifest.json") as f:
    canonical = json.load(f)

# Load crosscheck for known mappings
with open(r"C:\Users\RAJIV MEDAPATI\Documents\projects\lifepath\backend\core\rules\parashari\crosscheck.json") as f:
    crosscheck = json.load(f)

crosscheck_map = {item["rule_id"]: item for item in crosscheck}

# Normalized name function
def normalize(name):
    return name.lower().replace("yoga", "").replace("mahapurusha", "").replace("raja", "").replace("parivartana", "").strip().replace(" ", "_").replace("-", "_")

print("=" * 120)
print("DETERMINISTIC MAPPING TABLE: LEGACY YOGA -> CANONICAL RULE")
print("=" * 120)

legacy_data = []
for lf in legacy_files:
    with open(lf) as f:
        data = json.load(f)
        data["_file"] = lf.name
        legacy_data.append(data)

# Classifications
classifications = {}
for ld in legacy_data:
    fname = ld["_file"]
    lname = ld["name"]
    lid = ld.get("id", fname.replace(".json", ""))
    lnorm = normalize(lname)
    
    # Check crosscheck first
    matched_canonical = None
    match_type = None
    
    # Direct canonical match by rule_id pattern
    for canon in canonical:
        cname = canon["name"]
        cnorm = normalize(cname)
        if cnorm == lnorm or cname.lower() == lname.lower():
            matched_canonical = canon["rule_id"]
            match_type = "EXACT_NAME"
            break
    
    if not matched_canonical:
        # Check crosscheck
        for canon in canonical:
            if canon["rule_id"] in crosscheck_map:
                cc = crosscheck_map[canon["rule_id"]]
                if cc.get("legacy_file") == fname:
                    matched_canonical = canon["rule_id"]
                    match_type = "CROSSCHECK"
                    break
    
    if not matched_canonical:
        # Fuzzy match on normalized names
        for canon in canonical:
            cname = canon["name"]
            cnorm = normalize(cname)
            # Check if legacy name contains canonical core or vice versa
            lcore = lname.lower().replace("yoga", "").replace("mahapurusha", "").strip()
            ccore = cname.lower().replace("yoga", "").replace("mahapurusha", "").strip()
            if lcore == ccore or lcore in ccore or ccore in lcore:
                matched_canonical = canon["rule_id"]
                match_type = "FUZZY"
                break
    
    if matched_canonical:
        classifications[fname] = {
            "legacy_name": lname,
            "legacy_id": lid,
            "canonical_rule_id": matched_canonical,
            "match_type": match_type,
            "category": "A" if match_type in ["EXACT_NAME", "CROSSCHECK"] else "B",
            "conditions": ld.get("conditions", []),
            "description": ld.get("description", "")
        }
    else:
        classifications[fname] = {
            "legacy_name": lname,
            "legacy_id": lid,
            "canonical_rule_id": None,
            "match_type": "NONE",
            "category": "D",  # Will refine below
            "conditions": ld.get("conditions", []),
            "description": ld.get("description", "")
        }

# Print mapping table
print(f"{'LEGACY FILE':<40} {'LEGACY NAME':<40} {'CANONICAL RULE ID':<50} {'MATCH':<12} {'CAT'}")
print("-" * 160)
for fname, cls in sorted(classifications.items()):
    cname = cls["legacy_name"][:38]
    canon = cls["canonical_rule_id"] or "NONE"
    print(f"{fname:<40} {cname:<40} {canon:<50} {cls['match_type']:<12} {cls['category']}")

print("\n\nCLASSIFICATION SUMMARY:")
cats = {}
for fname, cls in classifications.items():
    cat = cls["category"]
    cats[cat] = cats.get(cat, 0) + 1
for cat in sorted(cats.keys()):
    print(f"  Category {cat}: {cats[cat]}")

print(f"\nTotal legacy: {len(classifications)}")
print(f"Total canonical: {len(canonical)}")