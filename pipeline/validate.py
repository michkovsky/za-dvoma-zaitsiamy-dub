"""Check meaningful cross-file invariants using the standard library."""
import hashlib
import json
from common import ROOT, read_csv, seconds

def unique(rows, field, label):
    values = [r[field] for r in rows]
    if len(values) != len(set(values)):
        raise ValueError(f'Duplicate {field}: {label}')

def main():
    files = [f for f in ROOT.rglob('*.csv') if not any(
        part in ['local','media','.git'] for part in f.relative_to(ROOT).parts)]
    for file in files:
        rows = read_csv(file)
        if rows and 'id' in rows[0]:
            unique(rows,'id',file)
        for row in rows:
            if 'start' in row and 'end' in row and (row['start'] or row['end']):
                if not 0 <= seconds(row['start']) < seconds(row['end']):
                    raise ValueError(f'Invalid time window: {file} {row}')
    concepts = {r['id'] for r in read_csv(ROOT/'glossary.csv')}
    for file in ROOT.glob('languages/*/glossary.csv'):
        rows = read_csv(file)
        unique(rows,'concept_id',file)
        for row in rows:
            if row['concept_id'] not in concepts:
                raise ValueError(f'Unknown concept: {file} {row["concept_id"]}')
    characters = {f.stem for f in (ROOT/'characters').glob('*.md') if f.name!='README.md'}
    for file in list(ROOT.glob('pilots/*/dialogue.uk.csv')) + list(ROOT.glob('scenes/*/dialogue.uk.csv')):
        for row in read_csv(file):
            if not set(row['speaker'].split('+')) <= characters:
                raise ValueError(f'Unknown speaker: {file} {row["speaker"]}')
    frames = read_csv(ROOT/'source/keyframes.csv')
    stamps = [seconds(r['timecode']) for r in frames]
    if stamps != sorted(set(stamps)):
        raise ValueError('Keyframe timestamps are not unique and increasing.')
    exchange = read_csv(ROOT/'pilots/P001/en/exchange.csv')
    for a,b in zip(exchange,exchange[1:]):
        if seconds(a['end']) > seconds(b['start']):
            raise ValueError('Accidental overlapping voices in repaired pilot exchange.')
    checked = 0
    for file in ROOT.glob('pilots/*/artifacts.csv'):
        for row in read_csv(file):
            media = ROOT/row['file']
            if media.is_file():
                if hashlib.sha256(media.read_bytes()).hexdigest()!=row['sha256']:
                    raise ValueError(f'Artifact hash mismatch: {row["file"]}')
                checked += 1
    for file in ROOT.rglob('*.json'):
        if not any(part in ['local','media','.git'] for part in file.relative_to(ROOT).parts):
            json.loads(file.read_text('utf-8-sig'))
    print(f'OK: {len(files)} CSV tables, {len(frames)} keyframe anchors, '
          f'concepts, speakers, times, repaired exchange; {checked} local media hashes checked.')

if __name__ == '__main__':
    main()
