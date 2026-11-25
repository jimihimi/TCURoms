"""Relocate cross-ROM-supported TCU images without changing their evidence status."""
import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'Review/Cross-ROM-Supported/'
CATALOG = ROOT / 'catalog.csv'
RENAMES = ROOT / 'provenance/fitment-renames.csv'
OUT = ROOT / 'provenance/cross-rom-relocation.csv'

def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)

def write_csv(path, fields, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

fields, catalog = read_csv(CATALOG)
rename_fields, renames = read_csv(RENAMES)
review = [r for r in catalog if r['repo_path'].startswith(PREFIX)]
assert len(review) == 18 and len({r['sha256'] for r in review}) == 18
mapping = {}
relocation = []
for row in review:
    old = row['repo_path']
    new = old[len(PREFIX):]
    assert new.split('/')[0] == row['transmission_family']
    source, target = (ROOT / old).resolve(), (ROOT / new).resolve()
    assert source.is_relative_to(ROOT) and target.is_relative_to(ROOT)
    assert source.is_file() and not target.exists()
    assert hashlib.sha256(source.read_bytes()).hexdigest() == row['sha256']
    mapping[old] = new
    relocation.append({'old_path':old,'new_path':new,'sha256':row['sha256'],
                       'bytes':row['bytes'],'transmission_family':row['transmission_family'],
                       'evidence_status':row['evidence_status']})

for row in catalog:
    row['repo_path'] = mapping.get(row['repo_path'], row['repo_path'])
for row in renames:
    row['new_path'] = mapping.get(row['new_path'], row['new_path'])

for old, new in mapping.items():
    target = ROOT / new
    target.parent.mkdir(parents=True, exist_ok=True)
    (ROOT / old).rename(target)

write_csv(CATALOG, fields, catalog)
write_csv(RENAMES, rename_fields, renames)
write_csv(OUT, list(relocation[0]), relocation)

review_root = ROOT / 'Review/Cross-ROM-Supported'
for directory in sorted((p for p in review_root.rglob('*') if p.is_dir()),
                        key=lambda p: len(p.parts), reverse=True):
    directory.rmdir()  # refuses to remove any nonempty directory
review_root.rmdir()
(ROOT / 'Review').rmdir()  # likewise, only if no other review content remains
print(f'relocated {len(relocation)} unique binaries without changing their bytes')
