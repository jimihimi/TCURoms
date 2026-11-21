"""Build model/year filenames from evidenced applicability; never modify firmware.

Run from any directory: python tools/enrich_fitment.py [--apply]
Inputs are pinned to the pre-fitment commit and checked-in evidence. No network
requests are made by this deterministic transformation.
"""
import argparse
import csv
import hashlib
import io
import json
import platform
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = '204b987a598e7aed4bc3284581a560ffd19af516'
DATE = '2026-11-21'

def read_csv(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))

def write_csv(path, rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    path.write_bytes(stream.getvalue().encode('utf-8'))

def years_label(years):
    values = sorted(set(map(int, years)))
    if not values:
        return 'Unknown-Year'
    groups = []
    start = end = values[0]
    for year in values[1:]:
        if year == end + 1:
            end = year
        else:
            groups.append(str(start) if start == end else f'{start}-{end}')
            start = end = year
    groups.append(str(start) if start == end else f'{start}-{end}')
    return '+'.join(groups)

def models_in_header(text):
    text = text.upper()
    patterns = [(r'TRIBEC+CA|TRIBECA', 'Tribeca'), (r'\bWRX\b', 'WRX'),
                (r'\bLEGACY\b|\bLIBERTY\b', 'Legacy'), (r'\bOUTBACK\b', 'Outback'),
                (r'\bFORESTER\b', 'Forester'), (r'\bIMPREZA\b', 'Impreza'),
                (r'\bCROSSTREK\b', 'Crosstrek'), (r'\bXV\b', 'XV'),
                (r'\bBRZ\b', 'BRZ'), (r'\bASCENT\b', 'Ascent'),
                (r'\bLEVORG\b', 'Levorg'), (r'\bBAJA\b', 'Baja')]
    return sorted({name for pattern, name in patterns if re.search(pattern, text)})

def header_years(text):
    # Only an explicit model-year expression; do not interpret trim/ROM numbers.
    result = set()
    for hit in re.finditer(r'((?:(?:19|20)\d{2}|\d{2})(?:\s*[,/]\s*\d{2,4})*)\s*MY\b', text, re.I):
        for token in re.findall(r'\d+', hit[1]):
            number = int(token)
            result.add(number if number >= 1900 else 2000 + number)
    return sorted(result)

def model_label(models):
    return '-'.join(sorted(set(models))) if models else 'Unknown-Model'

def safe(text):
    return re.sub(r'[^A-Za-z0-9_.+-]+', '_', text).strip('_')

def filename_parts(text):
    # Underscores separate identifiers in the original filenames; \b would miss them.
    return sorted(set(re.findall(r'(?<![A-Z0-9])(?:31711|30919)[A-Z0-9]{5}(?![A-Z0-9])', text.upper())))

def main(apply=False):
    base_bytes = subprocess.check_output(['git', '-C', str(ROOT), 'show', BASE + ':catalog.csv'])
    rows = list(csv.DictReader(io.StringIO(base_bytes.decode('utf-8'))))
    original_unknown = {r['sha256'] for r in rows if r['model_group'] == 'Unknown-Model'}
    current = read_csv(ROOT / 'catalog.csv')
    current_paths = {r['sha256']: r['repo_path'] for r in current}
    assert len(rows) == len(current) == 309, 'Unexpected catalog size'
    db = defaultdict(list)
    for r in read_csv(ROOT / 'provenance/market-database-evidence.csv'):
        db[r['package'], r['member']].append(r)
    cross = {(r['package'], r['member']): r for r in read_csv(ROOT / 'provenance/market-cross-reference.csv')}
    online_path = ROOT / 'provenance/part-fitment-online.json'
    online = json.loads(online_path.read_text(encoding='utf-8'))
    products = defaultdict(list)
    for item in online['evidence']:
        assert item['part_number'].lower() in item['url'].lower()
        products[item['part_number']].append(item)
    # Explicit donor statements for existing images; approximate years are omitted.
    donor = {
        'ABD1A03100': (['Legacy'], [2005], 'https://www.romraider.com/forum/viewtopic.php?p=127764#p127764'),
        'ABD1207000': (['Legacy'], [2006], 'https://www.romraider.com/forum/viewtopic.php?p=139133#p139133'),
        'ACD1A06000': (['Legacy'], [2007], 'https://www.romraider.com/forum/viewtopic.php?p=129913#p129913'),
        'ACD1207000': (['Legacy'], [2006], 'https://www.romraider.com/forum/viewtopic.php?p=129924#p129924'),
        'AAD1A06000': (['Legacy'], [2004], 'https://www.romraider.com/forum/viewtopic.php?p=169664#p169664'),
        'B1AE207100': (['Legacy'], [2010], 'https://www.romraider.com/forum/viewtopic.php?p=170833#p170833'),
        '8EFB206000': (['Tribeca'], [2014], 'https://www.romraider.com/forum/viewtopic.php?p=170970#p170970'),
    }
    grouped = defaultdict(list)
    for r in rows:
        key = r['package'], r['member']
        metadata = cross.get(key, {})
        parts = sorted({metadata.get('new_part', ''), metadata.get('target_part', '')} - {''})
        if not parts:
            parts = filename_parts(r['source_alias'])
        records = db.get(key, [])
        firmware_fitments = sorted({(x['Vehicle'].title().replace('Brz', 'BRZ').replace('Wrx', 'WRX').replace('Xv', 'XV'), int(x['Year'])) for x in records if re.fullmatch(r'(?:19|20)\d{2}', x['Year'])})
        models = sorted({x[0] for x in firmware_fitments})
        years = sorted({x[1] for x in firmware_fitments})
        basis = metadata.get('match_level', '') if records else ''
        source_refs = sorted({x['database'] + '#record=' + x['csv_record_number'] for x in records})
        if not firmware_fitments:
            models = models_in_header(r['model_header'])
            years = header_years(r['model_header'])
            basis = 'package_header' if models or years else 'unresolved'
        if not r['package'] and r['rom_id'] in donor:
            models, years, reference = donor[r['rom_id']]
            basis = 'donor_report'; source_refs = [reference]
        if not r['package'] and '31711AJ782' in parts:
            models, years = ['Legacy'], [2003, 2004]
            basis = 'part_specific_forum_report'
            source_refs = ['https://www.romraider.com/forum/viewtopic.php?p=134150#p134150']
        matches = [item for part in parts for item in products.get(part, [])]
        hardware = sorted({(fit['model'], fit['years'], item['part_number'], item['url']) for item in matches for fit in item['fitments']})
        r.update(new_part_number=metadata.get('new_part', ''), target_part_number=metadata.get('target_part', ''),
                 filename_part_numbers=' | '.join(parts) if not metadata else '',
                 applicability_models=' | '.join(models), applicability_years=' | '.join(map(str, years)),
                 applicability_basis=basis, applicability_sources=' | '.join(source_refs),
                 firmware_model_year_pairs=json.dumps(firmware_fitments, separators=(',', ':')),
                 hardware_fitment_json=json.dumps(hardware, separators=(',', ':')),
                 online_part_status='fitment_table_found' if hardware else 'product_page_only' if matches else 'no_exact_product_result' if parts else 'no_part_number_available',
                 online_fitment_sources=' | '.join(sorted({x['url'] for x in matches})),
                 parts_subaru_status='403_and_no_indexed_results' if parts else 'no_part_number_available',
                 fitment_checked_date=DATE, previous_repo_path=r['repo_path'])
        r['_models'] = set(models); r['_years'] = set(years)
        grouped[r['sha256']].append(r)
    plan = []
    for digest, aliases in grouped.items():
        preferred = [r for r in aliases if r['package']] or aliases
        models = set().union(*(r['_models'] for r in preferred))
        years = set().union(*(r['_years'] for r in preferred))
        # Exact-byte aliases may share applicability, without changing source-specific evidence.
        if not models:
            models = set().union(*(r['_models'] for r in aliases))
        if not years:
            years = set().union(*(r['_years'] for r in aliases))
        model = model_label(models)
        old_path = aliases[0]['repo_path']
        parts = Path(old_path).parts
        review_prefix = parts[:2] if parts[0] == 'Review' else ()
        tail = parts[2:] if review_prefix else parts
        families = {r['transmission_family'] for r in aliases} - {'Unclassified'}
        family = next(iter(families)) if len(families) == 1 else tail[0]
        market = tail[1]
        known = sorted({r['rom_id'] for r in aliases if r['rom_id']})
        advertised = sorted({r['header_new_rom_id'] for r in aliases if r['header_new_rom_id']})
        identifiers = known or advertised
        identity = identifiers[0] if len(identifiers) == 1 else 'Multiple-ROM-IDs' if identifiers else 'Unknown-ROM-ID'
        new_parts = {r['new_part_number'] for r in aliases if r['new_part_number']}
        part_set = sorted(new_parts or {p for r in aliases for p in r['filename_part_numbers'].split(' | ') if p} or {r['target_part_number'] for r in aliases if r['target_part_number']})
        part_token = part_set[0] if len(part_set) == 1 else 'Multiple-Parts' if part_set else 'No-Part-Number'
        kind = 'shared-image' if any(r['payload_type'] == 'shared-image' for r in aliases) else 'update-payload'
        filename = safe(f'{years_label(years)}_{model}__{identity}__{part_token}__{digest[:12]}__{kind}') + '.bin'
        new_path = Path(*review_prefix, family, market, model, filename).as_posix()
        assert len(filename) <= 240 and len(new_path) <= 240, new_path
        actual = ROOT / current_paths[digest]
        assert actual.resolve().is_relative_to(ROOT)
        data = actual.read_bytes()
        assert hashlib.sha256(data).hexdigest() == digest
        target = ROOT / new_path
        assert target.resolve().is_relative_to(ROOT)
        assert not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest() == digest
        for r in aliases:
            r['repo_path'] = new_path
            r['model_group'] = model
            r['transmission_family'] = family
            r['filename_years'] = years_label(years)
            r['filename_models'] = model
            r['filename_basis'] = 'union of applicable package records for byte-identical aliases; donor report otherwise'
            r.pop('_models'); r.pop('_years')
        plan.append(dict(old_path=old_path, new_path=new_path, sha256=digest, bytes=len(data), source_path=actual))
    assert len({x['new_path'].casefold() for x in plan}) == len(plan) == 289
    assert {r['sha256'] for r in current} == set(grouped)
    before_unknown = original_unknown
    after_unknown = {r['sha256'] for r in rows if r['model_group'] == 'Unknown-Model'}
    summary = dict(date=DATE, tool='enrich_fitment.py v1', python=platform.python_version(),
                   command='python tools/enrich_fitment.py --apply',
                   script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   base_commit=BASE, catalog_rows=len(rows), binary_count=len(plan),
                   renamed_binaries=sum(x['old_path'] != x['new_path'] for x in plan),
                   binaries_with_years=len({r['sha256'] for r in rows if r['filename_years'] != 'Unknown-Year'}),
                   unknown_model_before=len(before_unknown), unknown_model_after=len(after_unknown),
                   unknown_models_resolved=len(before_unknown - after_unknown),
                   online_parts_searched=len(online['searches']), online_parts_with_fitment=len({e['part_number'] for e in online['evidence'] if e['fitments']}),
                   catalog_rows_with_online_fitment=sum(r['online_part_status'] == 'fitment_table_found' for r in rows),
                   package_rows_with_database_applicability=sum(bool(r['firmware_model_year_pairs'] != '[]') for r in rows if r['package']),
                   unresolved_model_paths=sorted({r['repo_path'] for r in rows if r['model_group'] == 'Unknown-Model'}),
                   binary_sha256_set_unchanged=True, parts_subaru_access='HTTP 403; indexed searches had no results',
                   input_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in ['provenance/part-fitment-online.json', 'provenance/market-cross-reference.csv', 'provenance/market-database-evidence.csv']})
    if apply:
        for item in plan:
            source = item.pop('source_path')
            target = ROOT / item['new_path']
            if source != target:
                target.parent.mkdir(parents=True, exist_ok=True)
                source.rename(target)
        for directory in sorted(ROOT.rglob('*'), key=lambda x: len(x.parts), reverse=True):
            if directory.is_dir() and '.git' not in directory.parts and not any(directory.iterdir()):
                directory.rmdir()
        write_csv(ROOT / 'catalog.csv', rows)
        write_csv(ROOT / 'provenance/fitment-renames.csv', plan)
        (ROOT / 'provenance/fitment-enrichment-summary.json').write_bytes((json.dumps(summary, indent=2) + '\n').encode())
        for r in rows:
            assert hashlib.sha256((ROOT / r['repo_path']).read_bytes()).hexdigest() == r['sha256']
    print(json.dumps(summary, indent=2))
    return summary

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Rename images and write the enriched catalog')
    main(parser.parse_args().apply)
