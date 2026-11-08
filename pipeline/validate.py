"""Check meaningful cross-file invariants using the standard library."""
import hashlib
import json
from pathlib import Path

if __package__:
    from .common import ROOT, read_csv, seconds
    from .scene_validation import validate_scenes
else:
    from common import ROOT, read_csv, seconds
    from scene_validation import validate_scenes

def unique(rows, field, label):
    values = [r[field] for r in rows]
    if len(values) != len(set(values)):
        raise ValueError(f'Duplicate {field}: {label}')

def _is_excluded(relative_path):
    parts = relative_path.parts
    return any(part in ['local', 'media', '.git'] for part in parts) or (
        parts[:2] == ('tests', 'fixtures')
    )

def main(root=ROOT):
    root = Path(root)
    files = [f for f in root.rglob('*.csv') if not _is_excluded(f.relative_to(root))]
    for file in files:
        rows = read_csv(file)
        if rows and 'id' in rows[0]:
            unique(rows,'id',file)
        for row in rows:
            if 'start' in row and 'end' in row and (row['start'] or row['end']):
                if not 0 <= seconds(row['start']) < seconds(row['end']):
                    raise ValueError(f'Invalid time window: {file} {row}')
    concepts = {r['id'] for r in read_csv(root/'glossary.csv')}
    for file in root.glob('languages/*/glossary.csv'):
        rows = read_csv(file)
        unique(rows,'concept_id',file)
        for row in rows:
            if row['concept_id'] not in concepts:
                raise ValueError(f'Unknown concept: {file} {row["concept_id"]}')
    registry = read_csv(root/'characters/index.csv')
    characters = {row['id'] for row in registry}
    cast = {row['id']: row for row in read_csv(root/'source/cast-credits.csv')}
    for row in registry:
        for field in ['in_script', 'in_film', 'in_credits']:
            if row[field] not in ['yes', 'no', 'unknown']:
                raise ValueError(f'Invalid {field}: {row["id"]}')
        credit = cast.get(row['credit_id']) if row['credit_id'] else None
        if row['credit_id'] and credit is None:
            raise ValueError(f'Unknown credit: {row["id"]}')
        if credit and credit['character_id'] != row['id']:
            raise ValueError(f'Credit/character mismatch: {row["id"]}')
        if row['in_credits'] == 'yes':
            if not credit or credit['kind'] != 'named_role' or credit['role'] != row['credit_name']:
                raise ValueError(f'Unsupported credited role: {row["id"]}')
            if row['in_film'] != 'yes':
                raise ValueError(f'Named film credit must confirm presence: {row["id"]}')
        elif row['credit_name'] or (credit and credit['kind'] == 'named_role'):
            raise ValueError(f'Inconsistent credit presence: {row["id"]}')
        if row['in_script'] == 'yes' and not row['script_name']:
            raise ValueError(f'Missing script name: {row["id"]}')
    for row in cast.values():
        seconds(row['timecode'])
        if row['character_id'] and row['character_id'] not in characters:
            raise ValueError(f'Unknown credit character: {row["id"]}')
        if row['kind'] != 'named_role' and row['role']:
            raise ValueError(f'Unnamed performer has an invented credited role: {row["id"]}')
    for file in root.glob('pilots/*/dialogue.uk.csv'):
        for row in read_csv(file):
            if not set(row['speaker'].split('+')) <= characters:
                raise ValueError(f'Unknown speaker: {file} {row["speaker"]}')
    frames = read_csv(root/'source/keyframes.csv')
    stamps = [seconds(r['timecode']) for r in frames]
    if stamps != sorted(set(stamps)):
        raise ValueError('Keyframe timestamps are not unique and increasing.')
    exchange = read_csv(root/'pilots/P001/en/exchange.csv')
    for a,b in zip(exchange,exchange[1:]):
        if seconds(a['end']) > seconds(b['start']):
            raise ValueError('Accidental overlapping voices in repaired pilot exchange.')
    checked = 0
    for file in root.glob('pilots/*/artifacts.csv'):
        for row in read_csv(file):
            media = root/row['file']
            if media.is_file():
                if hashlib.sha256(media.read_bytes()).hexdigest()!=row['sha256']:
                    raise ValueError(f'Artifact hash mismatch: {row["file"]}')
                checked += 1
    evidence_checked = 0
    for row in read_csv(root/'source/credits-evidence.csv'):
        seconds(row['timecode'])
        image = root/row['local_file']
        if image.is_file():
            if hashlib.sha256(image.read_bytes()).hexdigest() != row['sha256']:
                raise ValueError(f'Credit evidence hash mismatch: {row["id"]}')
            evidence_checked += 1
    for file in root.rglob('*.json'):
        if not _is_excluded(file.relative_to(root)):
            json.loads(file.read_text('utf-8-sig'))
    diagnostics = validate_scenes(root)
    for message in diagnostics:
        print(message)
    print(f'OK: {len(files)} CSV tables, {len(frames)} keyframe anchors, '
          f'{len(characters)} character records, credit links, concepts, speakers, times, '
          f'repaired exchange; {checked} local media hashes and {evidence_checked} evidence hashes checked.')
    return diagnostics

if __name__ == '__main__':
    main()
