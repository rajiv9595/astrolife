import json

# Load golden snapshot (canonical results)
with open(r'backend\core\rules\parashari\golden_snapshot.json') as f:
    golden = json.load(f)

print('CANONICAL GOLDEN CHART RESULTS (FORMED):')
for r in golden['results']:
    if r['formation'] == 'FORMED':
        print(f'  {r["rule_id"]}: strength={r["strength"]}, planets={r["planets"]}, evidence={r["n_evidence"]}')

print()
not_formed = [r for r in golden['results'] if r['formation'] == 'NOT_FORMED']
print(f'CANONICAL NOT_FORMED: {len(not_formed)}')

# Load crosscheck for legacy comparison
with open(r'backend\core\rules\parashari\crosscheck.json') as f:
    crosscheck = json.load(f)

print()
print('CROSSCHECK COMPARISON (Legacy vs Canonical):')
for item in crosscheck:
    legacy_active = item.get('legacy_active', False)
    new_formed = item.get('new_formed', False)
    if legacy_active != new_formed:
        print(f'  DIFFERENCE: {item["rule_id"]} | legacy_active={legacy_active} | new_formed={new_formed} | {item.get("reason", "")}')
    else:
        status = "FORMED" if new_formed else "NOT_FORMED"
        print(f'  MATCH: {item["rule_id"]} | both={status}')