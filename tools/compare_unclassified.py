"""Report distinctive 64-byte block overlap against classified TCU images."""
import collections
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rows = list(csv.DictReader((ROOT / 'catalog.csv').open(encoding='utf-8-sig', newline='')))
unique = {r['sha256']: r for r in rows if not r['repo_path'].startswith('Review/')}

def chunks(path):
    data = path.read_bytes()
    return {hashlib.blake2b(block, digest_size=8).digest()
            for i in range(0, len(data)-63, 16)
            if len(set(block := data[i:i+64])) >= 12}

references = [(r, chunks(ROOT / r['repo_path'])) for r in unique.values()
              if r['transmission_family'] in {'4EAT','5EAT','CVT','6AT'}]
report = []
for c in unique.values():
    if c['transmission_family'] != 'Unclassified':
        continue
    candidate = chunks(ROOT / c['repo_path'])
    scores = []
    for r, ref in references:
        common = len(candidate & ref)
        scores.append({'family':r['transmission_family'], 'sha256':r['sha256'],
                       'path':r['repo_path'], 'shared_blocks':common,
                       'candidate_fraction':round(common/max(1,len(candidate)),4)})
    scores.sort(key=lambda x:x['shared_blocks'], reverse=True)
    report.append({'candidate':c['repo_path'],'sha256':c['sha256'],
                   'distinctive_blocks':len(candidate),'top_references':scores[:5],
                   'best_by_family':{fam:next((s for s in scores if s['family']==fam), None)
                                     for fam in ('4EAT','5EAT','CVT','6AT')}})

path=ROOT/'provenance/unclassified-binary-comparison.json'
if not report:
    raise SystemExit('No Unclassified images remain; use the pre-classification commit to regenerate this report.')
path.write_text(json.dumps({'method':'unique 64-byte windows every 16 bytes, excluding windows with fewer than 12 distinct byte values; overlap is supporting evidence only', 'results': report},indent=2))
for r in report:
    best=r['top_references'][0]
    print(r['sha256'][:12],r['distinctive_blocks'],best['family'],best['shared_blocks'],best['candidate_fraction'],
          [(f,(v or {}).get('shared_blocks',0)) for f,v in r['best_by_family'].items()])
