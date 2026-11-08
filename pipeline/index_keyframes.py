"""Read packet keyframe flags without decoding the movie."""
import csv
import json
import subprocess
from common import ROOT, timecode

def main():
    config = json.loads((ROOT/'local/media.json').read_text('utf-8-sig'))
    result = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_packets', '-show_entries', 'packet=pts_time,flags', '-of', 'csv=p=0',
        config['video']], capture_output=True, text=True, check=True)
    timestamps = set()
    for row in csv.reader(result.stdout.splitlines()):
        if len(row) >= 2 and 'K' in row[1]:
            timestamps.add(float(row[0]))
    if not timestamps:
        raise SystemExit('No video key packets found; previous index preserved.')
    target = ROOT/'source/keyframes.csv'
    with target.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['id', 'timecode'])
        writer.writeheader()
        writer.writerows({'id': f'KF{i:04d}', 'timecode': timecode(t)}
                        for i,t in enumerate(sorted(timestamps),1))
    print(f'Indexed {len(timestamps)} keyframe anchors. These are not confirmed scene boundaries.')

if __name__ == '__main__':
    main()
