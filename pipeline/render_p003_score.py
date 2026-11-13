"""Export the source-based P003 verse. Standard library only; outputs stay external."""
import argparse
from array import array
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import sys
import wave
import xml.etree.ElementTree as ET

from common import ROOT, protect_source_directories

PPQ = 480
DIVISIONS = 4
SR = 22050
NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def pitch(name):
    match = re.fullmatch(r'([A-G](?:#)?)(-?\d+)', name)
    if not match:
        raise ValueError(f'Invalid pitch: {name}')
    value = (int(match[2]) + 1) * 12 + NAMES.index(match[1])
    if not 0 <= value <= 127:
        raise ValueError('Pitch outside MIDI range')
    return value


def validate(score):
    if len(score['bars']) != 8 or len(score['guitar']['half_bar_chords']) != 16:
        raise ValueError('P003 requires eight bars and sixteen half-bar chords')
    counts = [0] * 4
    pending = None
    for index, bar in enumerate(score['bars']):
        if bar['source_bar'] != index + 3 or bar['line'] != index // 2 + 1:
            raise ValueError('Unexpected source bar or lyric-line order')
        total = Fraction(0)
        for note in bar['notes']:
            number, duration = pitch(note[0]), Fraction(note[1])
            tie = note[2] if len(note) == 3 else None
            if duration not in {Fraction(1, 4), Fraction(1, 2), Fraction(3, 4),
                                Fraction(1), Fraction(3, 2), Fraction(2)}:
                raise ValueError('Unsupported note duration')
            if pending is not None and (tie != 'stop' or pending != number):
                raise ValueError('Broken tie')
            if tie == 'stop':
                if pending != number:
                    raise ValueError('Tie stop without matching start')
                pending = None
            else:
                counts[bar['line'] - 1] += 1
                if tie == 'start':
                    pending = number
                elif tie is not None:
                    raise ValueError('Invalid tie marker')
            total += duration
        if total != 4:
            raise ValueError(f'Source bar {bar["source_bar"]}: {total}, expected 4 quarters')
    if pending is not None or counts != [10, 9, 10, 10]:
        raise ValueError('Unexpected tie or syllable-attack structure')
    if len(score['verses']) != 3 or any(
            [len(line) for line in verse] != counts for verse in score['verses']):
        raise ValueError('Lyrics do not fit the 10/9/10/10 attack map')
    return counts


def chord(label, transpose):
    match = re.fullmatch(r'([A-G])([m7]?)', label)
    if not match:
        raise ValueError(f'Unsupported chord: {label}')
    root = NAMES.index(match[1]) + transpose
    kind = match[2]
    intervals = [0, 3, 7] if kind == 'm' else [0, 4, 7, 10] if kind == '7' else [0, 4, 7]
    return root % 12, intervals, kind


def guitar_bass(root, fifth=False):
    number = 36 + (root + (7 if fifth else 0)) % 12
    return number + 12 if number < 40 else number


def performance(score, verses, key):
    transpose = -4 if key == 'Am' else 0
    melody, guitar = [], []
    for verse in range(verses):
        offset = Fraction(verse * 32)
        for bar in score['bars']:
            for note in bar['notes']:
                number, duration = pitch(note[0]) + transpose, Fraction(note[1])
                tie = note[2] if len(note) == 3 else None
                if tie == 'stop':
                    melody[-1]['duration'] += duration
                else:
                    melody.append(dict(start=offset, duration=duration, pitch=number, verse=verse))
                offset += duration
        for half, label in enumerate(score['guitar']['half_bar_chords']):
            root, intervals, _ = chord(label, transpose + 4)
            base = Fraction(verse * 32 + half * 2)
            for beat in range(4):
                start = base + Fraction(beat, 2)
                if beat % 2 == 0:
                    numbers = [guitar_bass(root, fifth=beat == 2)]
                else:
                    numbers = [48 + root + step for step in intervals]
                for number in numbers:
                    guitar.append(dict(start=start, duration=Fraction(9, 20), pitch=number, verse=verse))
    return melody, guitar


def vlq(number):
    values = [number & 127]
    number >>= 7
    while number:
        values.insert(0, (number & 127) | 128)
        number >>= 7
    return bytes(values)


def midi_track(events, end_tick):
    result, previous = bytearray(), 0
    for tick, order, message in sorted(events, key=lambda item: (item[0], item[1])):
        result.extend(vlq(tick - previous) + message)
        previous = tick
    result.extend(vlq(end_tick - previous) + b'\xff\x2f\x00')
    return b'MTrk' + struct.pack('>I', len(result)) + result


def write_midi(path, melody, guitar, bpm, verses, key):
    end = 32 * verses * PPQ
    tempo = round(60_000_000 / bpm)
    signature = bytes([0 if key == 'Am' else 4, 1])
    conductor = [(0, 0, b'\xff\x51\x03' + tempo.to_bytes(3, 'big')),
                 (0, 1, b'\xff\x58\x04\x04\x02\x18\x08'),
                 (0, 2, b'\xff\x59\x02' + signature)]
    tracks = [midi_track(conductor, end)]
    for channel, (name, program, notes) in enumerate([
            ('Shared verse melody', 0, melody), ('Editorial nylon guitar', 24, guitar)]):
        encoded = name.encode('ascii')
        events = [(0, -2, b'\xff\x03' + vlq(len(encoded)) + encoded),
                  (0, -1, bytes([0xC0 + channel, program]))]
        for note in notes:
            start = round(note['start'] * PPQ)
            stop = round((note['start'] + note['duration']) * PPQ)
            events.extend([(start, 1, bytes([0x90 + channel, note['pitch'], 86])),
                           (stop, 0, bytes([0x80 + channel, note['pitch'], 0]))])
        tracks.append(midi_track(events, end))
    path.write_bytes(b'MThd' + struct.pack('>IHHH', 6, 1, len(tracks), PPQ) + b''.join(tracks))


def sub(parent, name, value=None, **attrs):
    node = ET.SubElement(parent, name, {key: str(item) for key, item in attrs.items()})
    if value is not None:
        node.text = str(value)
    return node


def xml_note(measure, number, duration, *, is_chord=False, tie=None, lyric=None):
    node = sub(measure, 'note')
    if is_chord:
        sub(node, 'chord')
    p = sub(node, 'pitch')
    name = NAMES[number % 12]
    sub(p, 'step', name[0])
    if '#' in name:
        sub(p, 'alter', 1)
    sub(p, 'octave', number // 12 - 1)
    sub(node, 'duration', int(duration * DIVISIONS))
    if tie:
        sub(node, 'tie', type=tie)
    types = {Fraction(1, 4): '16th', Fraction(1, 2): 'eighth', Fraction(3, 4): 'eighth',
             Fraction(1): 'quarter', Fraction(3, 2): 'quarter', Fraction(2): 'half'}
    sub(node, 'type', types[duration])
    if duration in {Fraction(3, 4), Fraction(3, 2)}:
        sub(node, 'dot')
    if tie:
        sub(sub(node, 'notations'), 'tied', type=tie)
    if lyric is not None:
        for index, text in enumerate(lyric, 1):
            sub(sub(node, 'lyric', number=str(index)), 'text', text)


def write_musicxml(path, score, key, bpm):
    transpose = -4 if key == 'Am' else 0
    root = ET.Element('score-partwise', version='4.0')
    sub(sub(root, 'work'), 'work-title', 'P003 — shared verse / source reading, proposed')
    identification = sub(root, 'identification')
    sub(identification, 'creator', 'Source image: V. Homoliaka; editorial guitar and lyric alignment', type='composer')
    parts = sub(root, 'part-list')
    for channel, (part_id, name) in enumerate([
            ('P1', 'Melody — shared by three verses'), ('P2', 'Guitar — editorial accompaniment')], 1):
        part_info = sub(parts, 'score-part', id=part_id)
        sub(part_info, 'part-name', name)
        instrument_id = part_id + '-I1'
        sub(sub(part_info, 'score-instrument', id=instrument_id), 'instrument-name', name)
        midi = sub(part_info, 'midi-instrument', id=instrument_id)
        sub(midi, 'midi-channel', channel)
        sub(midi, 'midi-program', 1 if part_id == 'P1' else 25)
    for part_id in ['P1', 'P2']:
        part = sub(root, 'part', id=part_id)
        slots = [0] * 4
        for index, bar in enumerate(score['bars']):
            measure = sub(part, 'measure', number=str(index + 1))
            if index == 0:
                attributes = sub(measure, 'attributes')
                sub(attributes, 'divisions', DIVISIONS)
                key_node = sub(attributes, 'key')
                sub(key_node, 'fifths', 0 if key == 'Am' else 4)
                sub(key_node, 'mode', 'minor')
                time = sub(attributes, 'time')
                sub(time, 'beats', 4)
                sub(time, 'beat-type', 4)
                clef = sub(attributes, 'clef')
                sub(clef, 'sign', 'G')
                sub(clef, 'line', 2)
                if part_id == 'P2':
                    transposition = sub(attributes, 'transpose')
                    sub(transposition, 'diatonic', 0)
                    sub(transposition, 'chromatic', 0)
                    sub(transposition, 'octave-change', -1)
                direction = sub(measure, 'direction')
                sub(sub(direction, 'direction-type'), 'words', 'Proposed source reading; editorial 4/4; trial tempo, not film synchronization')
                sub(direction, 'sound', tempo=bpm)
            if part_id == 'P1':
                for note in bar['notes']:
                    tie = note[2] if len(note) == 3 else None
                    line = bar['line'] - 1
                    lyrics = None
                    if tie != 'stop':
                        lyrics = [verse[line][slots[line]] for verse in score['verses']]
                        slots[line] += 1
                    xml_note(measure, pitch(note[0]) + transpose, Fraction(note[1]), tie=tie, lyric=lyrics)
            else:
                for half in range(2):
                    label = score['guitar']['half_bar_chords'][index * 2 + half]
                    number, intervals, kind = chord(label, transpose + 4)
                    harmony = sub(measure, 'harmony')
                    r = sub(harmony, 'root')
                    sub(r, 'root-step', NAMES[number][0])
                    if '#' in NAMES[number]:
                        sub(r, 'root-alter', 1)
                    sub(harmony, 'kind', {'m': 'minor', '7': 'dominant', '': 'major'}[kind])
                    for beat in range(4):
                        if beat % 2 == 0:
                            values = [guitar_bass(number, fifth=beat == 2)]
                        else:
                            values = [48 + number + interval for interval in intervals]
                        for pos, value in enumerate(values):
                            # Guitar treble clef sounds an octave below its written pitches.
                            xml_note(measure, value + 12, Fraction(1, 2), is_chord=pos > 0)
    ET.indent(root)
    ET.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)


def synth(notes, bpm, length, guitar=False):
    samples = array('f', [0.0]) * length
    for note in notes:
        start = round(float(note['start']) * 60 / bpm * SR)
        count = round(float(note['duration']) * 60 / bpm * SR)
        frequency = 440 * 2 ** ((note['pitch'] - 69) / 12)
        for i in range(count):
            t = i / SR
            envelope = min(1, i / (SR * .008)) * min(1, (count - 1 - i) / (SR * .02))
            envelope *= math.exp(-t * (5 if guitar else 1.2))
            angle = 2 * math.pi * frequency * t
            tone = math.sin(angle) + .25 * math.sin(2 * angle) + .09 * math.sin(3 * angle)
            samples[start + i] += tone * envelope * (.16 if guitar else .3)
    return samples


def write_wav(path, samples, gain):
    pcm = array('h', (round(value * gain * 32767) for value in samples))
    if sys.byteorder != 'little':
        pcm.byteswap()
    with wave.open(str(path), 'wb') as handle:
        handle.setparams((1, 2, SR, 0, 'NONE', 'not compressed'))
        handle.writeframes(pcm.tobytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--score', type=Path, default=ROOT / 'pilots/P003/music/score.json')
    parser.add_argument('--output-dir', type=Path, required=True, help='New external directory; never overwritten')
    parser.add_argument('--key', choices=['Am', 'C#m'], default='Am')
    parser.add_argument('--bpm', type=float)
    parser.add_argument('--verses', type=int, choices=[1, 3], default=1)
    args = parser.parse_args()
    score = json.loads(args.score.read_text(encoding='utf-8-sig'))
    counts = validate(score)
    bpm = args.bpm if args.bpm is not None else score['preview_tempo_quarter_bpm']
    if not math.isfinite(bpm) or not 40 <= bpm <= 240:
        parser.error('Trial quarter-note tempo must be between 40 and 240 BPM')
    output = protect_source_directories(args.output_dir)
    if output.exists():
        parser.error('Output directory exists; choose a new version')
    melody, guitar = performance(score, args.verses, args.key)
    template = [(n['start'], n['duration'], n['pitch']) for n in melody if n['verse'] == 0]
    for verse in range(args.verses):
        actual = [(n['start'] - verse * 32, n['duration'], n['pitch']) for n in melody if n['verse'] == verse]
        if actual != template:
            raise ValueError('Verse melody differs from the shared template')
    output.mkdir(parents=True)
    write_midi(output / 'score.mid', melody, guitar, bpm, args.verses, args.key)
    write_musicxml(output / 'score.musicxml', score, args.key, bpm)
    seconds = 32 * args.verses * 60 / bpm
    length = math.ceil((seconds + .25) * SR)
    lead = synth(melody, bpm, length)
    backing = synth(guitar, bpm, length, guitar=True)
    mix = array('f', (a + b for a, b in zip(lead, backing)))
    peak = max(max(abs(x) for x in values) for values in [lead, backing, mix])
    gain = min(1, .85 / peak)
    for name, values in [('melody.wav', lead), ('guitar.wav', backing), ('mix.wav', mix)]:
        write_wav(output / name, values, gain)
    report = dict(score_id=score['id'], score_sha256=sha(args.score), script_sha256=sha(Path(__file__)),
                  key=args.key, transpose_semitones=-4 if args.key == 'Am' else 0,
                  trial_quarter_bpm=bpm, bpm_status='editorial, not film tempo',
                  meter='4/4 editorial grouping from bar durations', verses=args.verses,
                  bars_per_verse=8, quarters_per_verse=32, syllable_attacks_per_line=counts,
                  melodic_attacks_per_verse=len(template), repeated_melody_identical=True,
                  musical_seconds=seconds, wav_seconds=length / SR, output_gain=gain,
                  max_absolute_sample=peak * gain, clipping_samples=0,
                  melody_status='manual reading of user image, proposed',
                  guitar_status='editorial bass/chord arrangement, not extracted film guitar',
                  lyric_alignment_status=score['lyric_alignment_status'],
                  outputs={p.name: sha(p) for p in sorted(output.iterdir())})
    (output / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=True))


if __name__ == '__main__':
    main()
