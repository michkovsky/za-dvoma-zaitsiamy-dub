"""Shared CSV and time helpers; no optional dependencies."""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

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
