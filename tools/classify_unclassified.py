"""Move strongly supported unclassified TCU images into gear-family folders."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPARISON = ROOT / 'provenance/unclassified-binary-comparison.json'
CATALOG = ROOT / 'catalog.csv'
RENAMES = ROOT / 'provenance/fitment-renames.csv'

def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)

def write_csv(path, fields, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

data = json.loads(COMPARISON.read_text(encoding='utf-8'))['results']
assert len(data) == 16, 'unexpected unclassified inventory'
mapping = {}
evidence = []
for item in data:
    scores = item['best_by_family']
    four = scores['4EAT']['shared_blocks']
    five = scores['5EAT']['shared_blocks']
    family = '4EAT' if four > five else '5EAT'
    winner = max(four, five)
    loser = min(four, five)
    assert winner >= 300 and winner >= 10 * max(1, loser), item['candidate']
    old = item['candidate']
    new = family + old[len('Unclassified'):]
    path = ROOT / old
    assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256']
    assert not (ROOT / new).exists(), new
    mapping[old] = new
    best = scores[family]
    evidence.append({'old_path':old,'new_path':new,'sha256':item['sha256'],
                     'family':family,'distinctive_blocks':item['distinctive_blocks'],
                     'best_reference':best['path'],'reference_sha256':best['sha256'],
                     'shared_64_byte_blocks':winner,'other_family_shared_blocks':loser,
                     'candidate_fraction':best['candidate_fraction'],
                     'basis':'64-byte content overlap plus exact package/part fitment; no gear count read directly from code'})

fields, rows = read_csv(CATALOG)
assert {r['repo_path'] for r in rows if r['transmission_family']=='Unclassified'} == set(mapping)
for row in rows:
    if row['repo_path'] in mapping:
        row['repo_path'] = mapping[row['repo_path']]
        row['transmission_family'] = row['repo_path'].split('/')[0]
        row['notes'] = (row['notes'] + '; ' if row['notes'] else '') + 'gear family inferred from distinctive ROM overlap and same-generation fitment; see provenance/unclassified-gear-classification.md'

rename_fields, rename_rows = read_csv(RENAMES)
for row in rename_rows:
    row['new_path'] = mapping.get(row['new_path'], row['new_path'])

for old, new in mapping.items():
    destination = ROOT / new
    destination.parent.mkdir(parents=True,exist_ok=True)
    (ROOT / old).rename(destination)

write_csv(CATALOG, fields, rows)
write_csv(RENAMES, rename_fields, rename_rows)
write_csv(ROOT/'provenance/unclassified-gear-classification.csv', list(evidence[0]), evidence)
print('moved', len(mapping), '4EAT', sum(x['family']=='4EAT' for x in evidence), '5EAT', sum(x['family']=='5EAT' for x in evidence))
