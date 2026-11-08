"""Shared CSV and time helpers; no optional dependencies."""
import csv
import os
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def protect_source_directories(target, *, allow_checkout=False):
    """Reject generated output beside or below configured source media."""
    target = Path(target).resolve()
    if not allow_checkout and target.is_relative_to(ROOT.resolve()):
        raise ValueError('Generated output must be outside the repository.')
    config = ROOT/'local/media.json'
    if config.is_file():
        data = json.loads(config.read_text('utf-8-sig'))
        for key in ('video', 'audio'):
            if data.get(key):
                source = Path(data[key]).resolve()
                if target.is_relative_to(source.parent) or (
                        target.exists() and source.exists() and target.samefile(source)):
                    raise ValueError('Generated output must be outside source media directories.')
    return target

def external_work_directory():
    """Optional session-local workspace, never inside the checkout."""
    value = os.environ.get('DUB_WORK_DIR', '').strip()
    config = ROOT/'local/media.json'
    if not value and config.is_file():
        value = json.loads(config.read_text('utf-8-sig')).get('work_dir', '')
        if not isinstance(value, str):
            raise ValueError('work_dir must be a path string.')
        value = value.strip()
    if not value:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError('DUB_WORK_DIR must be an absolute external directory.')
    path = path.resolve()
    if path.is_relative_to(ROOT.resolve()):
        raise ValueError('DUB_WORK_DIR must be outside the repository.')
    return protect_source_directories(path)

def seconds(value):
    if not re.fullmatch(r'\d{2,}:\d{2}:\d{2}\.\d{3}', value):
        raise ValueError(f'Expected HH:MM:SS.mmm, got {value!r}')
    h, m, s = value.split(':')
    if int(m) >= 60 or float(s) >= 60:
        raise ValueError(f'Invalid time: {value}')
    return int(h)*3600 + int(m)*60 + float(s)

def timecode(value):
    milliseconds = round(float(value)*1000)
    hours, remainder = divmod(milliseconds, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    secs, millis = divmod(remainder, 1000)
    return f'{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}'

def read_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError(f'Missing or duplicate header: {path}')
        rows = list(reader)
        if any(None in row or any(v is None for v in row.values()) for row in rows):
            raise ValueError(f'Malformed CSV row: {path}')
        return rows
