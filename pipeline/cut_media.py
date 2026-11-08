"""Preview or extract an exact interval, with separate original Ukrainian audio."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from common import ROOT, seconds, external_work_directory, protect_source_directories

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', required=True)
    parser.add_argument('--start', required=True)
    parser.add_argument('--end', required=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--output-dir', type=Path, help='Clip directory; overrides DUB_WORK_DIR.')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.id):
        parser.error('ID must contain only letters, numbers, underscore or hyphen.')
    start, end = seconds(args.start), seconds(args.end)
    if end <= start:
        parser.error('End must follow start.')
    config = json.loads((ROOT/'local/media.json').read_text('utf-8-sig'))
    work = external_work_directory() if args.output_dir is None else None
    output_dir = args.output_dir if args.output_dir is not None else (
        work/'exports' if work else ROOT/'media/scenes')
    target = protect_source_directories(output_dir/f'{args.id}.mp4',
        allow_checkout=args.output_dir is None and work is None)
    command = ['ffmpeg', '-hide_banner', '-nostdin', '-n', '-ss', str(start),
        '-i', config['video'], '-ss', str(start), '-i', config['audio'],
        '-map', '0:v:0', '-map', '1:a:0', '-t', str(end-start),
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-threads', '2',
        '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(target)]
    print(subprocess.list2cmdline(command))
    if args.execute:
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(command, check=True)

if __name__ == '__main__':
    main()
