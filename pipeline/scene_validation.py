"""Validate scene registries and source coverage without reading media."""
import csv
import io
import re
from collections import defaultdict, deque
from decimal import Decimal
from pathlib import Path, PureWindowsPath
from urllib.parse import unquote, urlsplit

if __package__:
    from .common import ROOT, seconds
else:
    from common import ROOT, seconds


INDEX_HEADER = (
    'id', 'title', 'start', 'end', 'status', 'source_id', 'lifecycle',
    'revision', 'package',
)
COVERAGE_HEADER = (
    'id', 'source_id', 'start', 'end', 'kind', 'scene_id', 'status', 'note',
)
TIMING_HEADER = (
    'source_id', 'duration', 'reference_source_id', 'offset', 'note',
)
CHANGE_HEADER = (
    'change_id', 'type', 'state', 'from_scene', 'from_revision',
    'to_scene', 'to_revision', 'record',
)
SNAPSHOT_HEADER = ('scene_id', 'revision', 'source_id', 'start', 'end')
CHANGE_SECTIONS = {
    'Change metadata': ('change_id', 'type', 'state', 'decision'),
    'Before': SNAPSHOT_HEADER,
    'After': SNAPSHOT_HEADER,
}
DIALOGUE_HEADER = ('id', 'start', 'end', 'speaker', 'text', 'status', 'note', 'source_id')
STATUSES = {'draft', 'verified', 'proposed', 'approved', 'rejected'}
LIFECYCLES = {'active', 'superseded'}
COVERAGE_KINDS = {'scene', 'credits', 'transition', 'unresolved'}


def _read_csv(root, relative_path, expected_header=None, required_header=None):
    path = root / relative_path
    if not path.is_file():
        return None, []

    try:
        with path.open(encoding='utf-8-sig', newline='') as handle:
            reader = csv.DictReader(handle, strict=True)
            header = reader.fieldnames
            if not header:
                raise ValueError(f'{path}: missing CSV header')
            if len(set(header)) != len(header):
                raise ValueError(f'{path}: duplicate CSV header')
            if expected_header and tuple(header) != expected_header:
                raise ValueError(
                    f'{path}: expected CSV header {",".join(expected_header)}; '
                    f'got {",".join(header)}'
                )
            if required_header and not set(required_header) <= set(header):
                missing = ','.join(sorted(set(required_header) - set(header)))
                raise ValueError(f'{path}: missing required CSV columns: {missing}')

            rows = []
            for line_number, row in enumerate(reader, start=2):
                if None in row or any(value is None for value in row.values()):
                    raise ValueError(f'{path}: malformed CSV row {line_number}')
                row['_line'] = line_number
                rows.append(row)
            return path, rows
    except csv.Error as error:
        raise ValueError(f'{path}: malformed CSV: {error}') from error


def _required_value(row, field, path):
    value = row.get(field, '')
    if not value.strip():
        raise ValueError(f'{path}: row {row["_line"]}: empty {field}')
    if value != value.strip():
        raise ValueError(
            f'{path}: row {row["_line"]}: surrounding whitespace in {field}'
        )
    return value


def _time(value, field, path, row_number):
    try:
        seconds(value)
        hours, minutes, seconds_part = value.split(':')
        return Decimal(int(hours) * 3600 + int(minutes) * 60) + Decimal(seconds_part)
    except (TypeError, ValueError) as error:
        raise ValueError(
            f'{path}: row {row_number}: invalid {field}: {value!r} ({error})'
        ) from error


def _positive_integer(value, field, path, row_number):
    try:
        number = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(
            f'{path}: row {row_number}: {field} must be a positive integer'
        ) from error
    if number < 1 or str(number) != value:
        raise ValueError(
            f'{path}: row {row_number}: {field} must be a positive integer'
        )
    return number


def _unique(rows, field, path):
    seen = set()
    for row in rows:
        value = _required_value(row, field, path)
        if value in seen:
            raise ValueError(f'{path}: row {row["_line"]}: duplicate {field} {value}')
        seen.add(value)


def _coverage_for_source(rows, source_id, duration, path):
    segments = [row for row in rows if row['source_id'] == source_id]
    segments.sort(key=lambda row: (
        _time(row['start'], 'start', path, row['_line']),
        _time(row['end'], 'end', path, row['_line']),
    ))
    previous_end = 0
    for row in segments:
        start = _time(row['start'], 'start', path, row['_line'])
        end = _time(row['end'], 'end', path, row['_line'])
        if not 0 <= start < end <= duration:
            raise ValueError(
                f'{path}: row {row["_line"]}: invalid coverage interval '
                f'{row["start"]}..{row["end"]} for source {source_id}'
            )
        if start != previous_end:
            issue = 'gap' if start > previous_end else 'overlap'
            raise ValueError(
                f'{path}: row {row["_line"]}: coverage {issue} for {source_id} '
                f'at {row["start"]}'
            )
        previous_end = end
    if segments and previous_end != duration:
        raise ValueError(
            f'{path}: coverage for {source_id} ends at {segments[-1]["end"]}, '
            f'not at source duration'
        )
    return segments


def parse_csv_sections(path, schemas):
    """Read exact top-level Markdown headings followed immediately by CSV fences.

    schemas maps section names (without ``## ``) to ordered CSV headers.
    Unrelated fenced code is ignored. Every requested section occurs once.
    """
    path = Path(path)
    lines = path.read_text(encoding='utf-8-sig').splitlines()
    sections = {}
    index = 0
    fence = None
    while index < len(lines):
        line = lines[index]
        if fence is not None:
            if re.fullmatch(rf' {{0,3}}{re.escape(fence[0])}{{{fence[1]},}}\s*', line):
                fence = None
            index += 1
            continue
        title = line[3:] if line.startswith('## ') else None
        if title in schemas:
            if title in sections:
                raise ValueError(f'{path}: line {index + 1}: duplicate section {title}')
            index += 1
            while index < len(lines) and not lines[index].strip():
                index += 1
            if index >= len(lines) or lines[index] != '```csv':
                raise ValueError(f'{path}: section {title}: expected exact ```csv fence')
            index += 1
            first_line = index + 1
            content = []
            while index < len(lines) and lines[index] != '```':
                content.append(lines[index])
                index += 1
            if index == len(lines):
                raise ValueError(f'{path}: section {title}: unclosed CSV fence')
            if not content or any(not line for line in content):
                raise ValueError(f'{path}: section {title}: empty CSV block or row')
            try:
                rows = list(csv.reader(io.StringIO('\n'.join(content)), strict=True))
            except csv.Error as error:
                raise ValueError(f'{path}: section {title}: invalid CSV: {error}') from error
            header = schemas[title]
            if not rows or tuple(rows[0]) != tuple(header):
                raise ValueError(f'{path}: section {title}: expected header {",".join(header)}')
            parsed = []
            for number, values in enumerate(rows[1:], start=first_line + 1):
                if len(values) != len(header) or any(
                    value != value.strip() or '\n' in value or '\r' in value
                    for value in values
                ):
                    raise ValueError(f'{path}: row {number}: malformed CSV in {title}')
                parsed.append(dict(zip(header, values), _line=number))
            if not parsed:
                raise ValueError(f'{path}: section {title}: missing data rows')
            sections[title] = parsed
            index += 1
            continue
        match = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if match:
            fence = (match[1][0], len(match[1]))
        index += 1
    missing = set(schemas) - set(sections)
    if missing:
        raise ValueError(f'{path}: missing sections: {", ".join(sorted(missing))}')
    return sections


def _relative_file(root, value, label):
    windows = PureWindowsPath(value)
    relative = Path(value.replace('\\', '/'))
    if (not value or value != value.strip() or windows.drive or windows.root
            or relative.is_absolute() or '..' in relative.parts
            or urlsplit(value).scheme):
        raise ValueError(f'{label}: expected a relative file path: {value!r}')
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f'{label}: missing or invalid file path: {value!r}')
    return path


def _snapshot(row, path, timings):
    scene_id = _required_value(row, 'scene_id', path)
    if not re.fullmatch(r'S\d{3,}', scene_id):
        raise ValueError(f'{path}: row {row["_line"]}: invalid scene_id {scene_id}')
    revision = _positive_integer(row['revision'], 'revision', path, row['_line'])
    source_id = _required_value(row, 'source_id', path)
    if source_id != 'video' or source_id not in timings:
        raise ValueError(f'{path}: row {row["_line"]}: snapshot requires video timing')
    start = _time(row['start'], 'start', path, row['_line'])
    end = _time(row['end'], 'end', path, row['_line'])
    if not 0 <= start < end <= timings[source_id][0]:
        raise ValueError(f'{path}: row {row["_line"]}: invalid snapshot interval')
    return (scene_id, revision), (source_id, start, end)


def _validate_changes(root, scene_by_id, timings, diagnostics):
    path, rows = _read_csv(root, Path('scenes/changes/index.csv'), CHANGE_HEADER)
    if path is None:
        if scene_by_id:
            raise ValueError(f'{root}: missing scenes/changes/index.csv')
        return
    groups = defaultdict(list)
    keys = set()
    for row in rows:
        change_id = _required_value(row, 'change_id', path)
        if not re.fullmatch(r'CH\d{3,}', change_id):
            raise ValueError(f'{path}: row {row["_line"]}: invalid change_id {change_id}')
        if row['type'] not in {'boundary', 'split', 'merge'}:
            raise ValueError(f'{path}: row {row["_line"]}: invalid change type')
        if row['state'] not in {'proposed', 'applied'}:
            raise ValueError(f'{path}: row {row["_line"]}: invalid change state')
        old = (row['from_scene'], _positive_integer(
            row['from_revision'], 'from_revision', path, row['_line']))
        new = (row['to_scene'], _positive_integer(
            row['to_revision'], 'to_revision', path, row['_line']))
        key = (change_id, old, new)
        if key in keys:
            raise ValueError(f'{path}: row {row["_line"]}: duplicate change edge {key}')
        keys.add(key)
        groups[change_id].append((row, old, new))

    current = {
        (scene_id, int(row['revision'])): (row['source_id'], start, end)
        for scene_id, (row, start, end) in scene_by_id.items()
    }
    existing = dict(current)
    changes = {}
    reservations = {}
    creating = {}
    replacing = {}
    graph = defaultdict(set)
    record_owners = {}
    for change_id, edges in groups.items():
        row = edges[0][0]
        signature = (row['type'], row['state'], row['record'])
        if any((edge[0]['type'], edge[0]['state'], edge[0]['record']) != signature
               for edge in edges):
            raise ValueError(f'{path}: {change_id}: inconsistent edge metadata')
        record = _relative_file(root, row['record'], f'{path}: {change_id} record')
        if record in record_owners:
            raise ValueError(f'{path}: {change_id}: record shared with another change')
        record_owners[record] = change_id
        sections = parse_csv_sections(record, CHANGE_SECTIONS)
        metadata = sections['Change metadata']
        if len(metadata) != 1:
            raise ValueError(f'{record}: Change metadata requires exactly one row')
        metadata = metadata[0]
        if (metadata['change_id'], metadata['type'], metadata['state']) != (
                change_id, row['type'], row['state']):
            raise ValueError(f'{record}: metadata does not match change index')
        decision = metadata['decision']
        if decision not in (
                {'accepted'} if row['state'] == 'applied' else {'pending', 'rejected'}):
            raise ValueError(f'{record}: invalid decision {decision!r}')
        snapshots = {}
        for section in ('Before', 'After'):
            versions = {}
            for snapshot in sections[section]:
                key, value = _snapshot(snapshot, record, timings)
                if key in versions:
                    raise ValueError(f'{record}: duplicate snapshot {key} in {section}')
                versions[key] = value
            expected = {edge[1 if section == 'Before' else 2] for edge in edges}
            if set(versions) != expected:
                raise ValueError(f'{record}: {section} snapshots do not match edges')
            if len({key[0] for key in versions}) != len(versions):
                raise ValueError(f'{record}: multiple revisions of one scene in {section}')
            snapshots[section] = versions
        before, after = snapshots['Before'], snapshots['After']
        kind = row['type']
        before_ids = {key[0] for key in before}
        after_ids = {key[0] for key in after}
        if kind == 'boundary':
            if (len(before) != 1 or len(after) != 1 or before_ids != after_ids
                    or next(iter(after))[1] <= next(iter(before))[1]):
                raise ValueError(f'{record}: invalid boundary cardinality/revision')
        else:
            valid_shape = (
                len(before) == 1 and len(after) >= 2 if kind == 'split'
                else len(before) >= 2 and len(after) == 1
            )
            if not valid_shape or before_ids & after_ids or any(key[1] != 1 for key in after):
                raise ValueError(f'{record}: invalid {kind} cardinality/new ID/revision')
            for scene_id in after_ids:
                if scene_id in reservations:
                    raise ValueError(f'{record}: new ID {scene_id} already reserved')
                reservations[scene_id] = change_id
        changes[change_id] = (record, kind, row['state'], decision, before, after)
        # Before always describes existing history. Proposed After does not.
        for key, value in list(before.items()) + (
                list(after.items()) if row['state'] == 'applied' else []):
            if key in existing and existing[key] != value:
                raise ValueError(f'{record}: conflicting existing snapshot {key}')
            existing[key] = value
        if row['state'] == 'applied':
            for key in before:
                if key in replacing:
                    raise ValueError(f'{record}: multiple replacing change_id for {key}')
                replacing[key] = change_id
            for key in after:
                if key in creating:
                    raise ValueError(f'{record}: multiple creating change_id for {key}')
                creating[key] = change_id
            for _edge_row, old, new in edges:
                graph[old].add(new)

    # Applied versions form one coherent acyclic history, not just matching times.
    indegree = defaultdict(int)
    for old, successors in graph.items():
        indegree[old] += 0
        for new in successors:
            indegree[new] += 1
    ready = deque(key for key, count in indegree.items() if count == 0)
    visited = 0
    while ready:
        key = ready.popleft()
        visited += 1
        for successor in graph[key]:
            indegree[successor] -= 1
            if indegree[successor] == 0:
                ready.append(successor)
    if visited != len(indegree):
        raise ValueError(f'{path}: cycle in applied version graph')

    # Only current snapshots and applied history establish an existing version.
    established = set(current) | set(creating) | set(replacing)
    for change_id, (record, kind, state, decision, before, after) in changes.items():
        for key in before:
            if key[0] not in scene_by_id or key not in established:
                raise ValueError(f'{record}: unknown Before scene/version {key}')
        if state == 'proposed':
            if kind != 'boundary':
                for key in after:
                    if key[0] in scene_by_id or any(
                            version[0] == key[0] for version in established):
                        raise ValueError(f'{record}: reserved new ID already exists: {key[0]}')
            if decision == 'pending' and any(
                    key not in current or scene_by_id[key[0]][0]['lifecycle'] != 'active'
                    for key in before):
                diagnostics.append(f'{change_id}: застаріла pending-пропозиція; потрібен перегляд.')
            continue
        for key in after:
            if key[0] not in scene_by_id:
                raise ValueError(f'{record}: applied successor must be registered: {key[0]}')
            if key not in current and key not in replacing:
                raise ValueError(f'{record}: applied After has no current or successor snapshot: {key}')
        for key in before:
            if key not in creating and key[0] in reservations:
                raise ValueError(f'{record}: new ID reused as a root version: {key[0]}')

    roots_by_scene = defaultdict(set)
    for version in established:
        if version not in creating:
            roots_by_scene[version[0]].add(version)
    for scene_id, roots in roots_by_scene.items():
        if len(roots) > 1:
            raise ValueError(f'{path}: disconnected scene revision roots for {scene_id}')

    for scene_id, (row, _start, _end) in scene_by_id.items():
        key = (scene_id, int(row['revision']))
        historical = [
            version for version in set(creating) | set(replacing)
            if version[0] == scene_id
        ]
        if historical and key[1] != max(version[1] for version in historical):
            raise ValueError(f'{path}: scene {scene_id} is not at its latest revision')
        replacement = replacing.get(key)
        retired = replacement is not None and changes[replacement][1] != 'boundary'
        if (row['lifecycle'] == 'superseded') != retired:
            raise ValueError(f'{path}: conflicting lifecycle for scene {scene_id}')
        if replacement and not retired:
            raise ValueError(f'{path}: current boundary revision was already replaced: {key}')


def _validate_packages(root, scene_by_id, diagnostics):
    owners = {}
    for scene_id, (row, _start, _end) in scene_by_id.items():
        if not row['package']:
            diagnostics.append(f'{scene_id}: пакет не сплановано.')
            continue
        path = _relative_file(root, row['package'], f'scene {scene_id} package')
        if path.name != 'spec.md':
            raise ValueError(f'{path}: scene package must point to spec.md')
        if path in owners:
            raise ValueError(f'{path}: package shared by scenes {owners[path]} and {scene_id}')
        owners[path] = scene_id
        rows = parse_csv_sections(path, {
            'Scene binding': ('scene_id', 'revision', 'source_id'),
        })['Scene binding']
        if len(rows) != 1:
            raise ValueError(f'{path}: Scene binding requires exactly one row')
        binding = rows[0]
        if (binding['scene_id'], binding['revision'], binding['source_id']) != (
                scene_id, row['revision'], row['source_id']):
            raise ValueError(f'{path}: Scene binding does not match current scene {scene_id}')


def _without_inline_code(text):
    """Remove Markdown code spans using equal-length backtick delimiters."""
    runs = list(re.finditer(r'`+', text))
    parts = []
    cursor = 0
    index = 0
    while index < len(runs):
        opening = runs[index]
        preceding = text[:opening.start()]
        backslashes = len(preceding) - len(preceding.rstrip('\\'))
        if backslashes % 2:
            index += 1
            continue
        closing_index = next((j for j in range(index + 1, len(runs))
                              if len(runs[j][0]) == len(opening[0])), None)
        if closing_index is None:
            index += 1
            continue
        parts.append(text[cursor:opening.start()])
        parts.append(' ')
        cursor = runs[closing_index].end()
        index = closing_index + 1
    parts.append(text[cursor:])
    return ''.join(parts)


def _prose_blocks(path):
    if not path.is_file():
        return []
    text = path.read_text(encoding='utf-8-sig')
    text = re.sub(r'<!--(?:.*?-->|.*\Z)', ' ', text, flags=re.DOTALL)
    lines = text.splitlines()
    prose = []
    fence = None
    for line in lines:
        if fence is not None:
            if re.fullmatch(rf' {{0,3}}{re.escape(fence[0])}{{{fence[1]},}}\s*', line):
                fence = None
            continue
        match = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if match:
            fence = (match[1][0], len(match[1]))
            prose.append('')
        elif not line.startswith(('    ', '\t')):
            prose.append(line)
    return [_without_inline_code(block) for block in re.split(
        r'\n\s*\n', '\n'.join(prose)) if block.strip()]


def _has_editorial_record(path, line_id, phrase):
    # Presence of an explicit prose record is not verification of its evidence.
    for block in _prose_blocks(path):
        # A generic acceptance-table header is not an affirmative record for
        # every ID appearing elsewhere in that table. Require actual prose.
        block = '\n'.join(line for line in block.splitlines()
                          if not line.lstrip().startswith('|'))
        # An ID-labelled claim ends at the next ID-labelled claim, even when
        # both are written in one paragraph. Never borrow another line's marker.
        claims = list(re.finditer(
            r'(?<![\w-])(?P<id>[A-Za-z][A-Za-z0-9_-]*\d[A-Za-z0-9_-]*)'
            r'(?![\w-])\s*[:—–]', block))
        for index, claim in enumerate(claims):
            if claim['id'] != line_id:
                continue
            end = claims[index + 1].start() if index + 1 < len(claims) else len(block)
            statement = block[claim.end():end]
            match = re.search(phrase, statement, re.IGNORECASE)
            if not match:
                continue
            if re.search(
                    r'(?:\bне|\bnot|потрібн\w*|запропонован\w*|required|pending)'
                    r'\s+(?:(?:явне|explicit)\s+)?$',
                    statement[:match.start()], re.IGNORECASE):
                continue
            explanation = re.sub(r'^[\s:;—–-]+', '', statement[match.end():])
            if explanation.startswith('?') or re.match(
                    r'(?:(?:ще|still|yet)\s+)?(?:не\s+(?:погоджен\w*|прийнят\w*|'
                    r'схвален\w*)|not\s+(?:approved|accepted|agreed)|pending\b|'
                    r'очіку\w*|await\w*)', explanation, re.IGNORECASE):
                continue
            if re.search(r'\w', explanation):
                return True
    return False


def _context_link(readme, target, line_id):
    for block in _prose_blocks(readme):
        if not re.search(r'контекст|context', block, re.IGNORECASE):
            continue
        for label, href in re.findall(r'\[([^\]]+)\]\(([^)\s]+)\)', block):
            link = urlsplit(href)
            if link.scheme or link.netloc:
                continue
            resolved = (readme.parent / unquote(link.path)).resolve()
            if resolved in {target.resolve(), (target.parent / 'README.md').resolve()} and (
                    unquote(link.fragment) == line_id or label == line_id):
                return True
    return False


def _speaker(row, path, characters, readme=None):
    speaker = _required_value(row, 'speaker', path)
    if speaker == 'unknown':
        if not row['note'].strip():
            raise ValueError(f'{path}: row {row["_line"]}: unknown speaker requires note')
        if row['status'] in {'verified', 'approved'} and (
                readme is None or not _has_editorial_record(
                    readme, row['id'], r'прийняте обмеження|accepted limitation')):
            raise ValueError(f'{path}: {row["id"]}: unknown requires an accepted limitation in README')
        return
    members = speaker.split('+')
    if len(set(members)) != len(members) or not set(members) <= characters:
        raise ValueError(f'{path}: row {row["_line"]}: unknown/invalid speaker {speaker}')


def _status(row, path):
    if row['status'] not in STATUSES:
        raise ValueError(f'{path}: row {row["_line"]}: invalid status {row["status"]!r}')


def _validate_dialogue(root, scene_by_id, timings):
    _registry, rows = _read_csv(root, Path('characters/index.csv'), required_header=('id',))
    characters = {row['id'] for row in rows}
    canonical = {}
    for base in ('pilots', 'scenes'):
        for path in sorted((root / base).glob('*/dialogue.uk.csv')):
            _path, rows = _read_csv(
                root, path.relative_to(root),
                DIALOGUE_HEADER if base == 'scenes' else None,
                required_header=('id', 'start', 'end', 'speaker', 'text', 'status', 'note'),
            )
            for row in rows:
                line_id = _required_value(row, 'id', path)
                if line_id in canonical:
                    raise ValueError(
                        f'{path}: row {row["_line"]}: duplicate canonical ID {line_id}; '
                        f'also in {canonical[line_id][0]}')
                canonical[line_id] = (path, row)
                _status(row, path)
                if base == 'pilots':
                    # Pilot times and identities are deliberately not scene bindings.
                    continue
                scene_id = path.parent.name
                if scene_id not in scene_by_id or scene_by_id[scene_id][0]['lifecycle'] != 'active':
                    raise ValueError(f'{path}: canonical dialogue requires an active scene owner')
                readme = path.parent / 'README.md'
                _speaker(row, path, characters, readme)
                source_id = _required_value(row, 'source_id', path)
                if source_id not in timings:
                    raise ValueError(f'{path}: {line_id}: missing timing for source_id {source_id}')
                duration, reference, offset = timings[source_id]
                if reference != 'video':
                    raise ValueError(f'{path}: {line_id}: source timing must reference video')
                start = _time(row['start'], 'start', path, row['_line'])
                end = _time(row['end'], 'end', path, row['_line'])
                if not 0 <= start < end <= duration:
                    raise ValueError(f'{path}: {line_id}: invalid source-time interval')
                start, end = start + offset, end + offset
                if not 0 <= start < end <= timings['video'][0]:
                    raise ValueError(f'{path}: {line_id}: converted time exceeds video duration')
                _scene, scene_start, scene_end = scene_by_id[scene_id]
                if scene_start <= start < end <= scene_end:
                    continue
                if not start < scene_end or not end > scene_start:
                    raise ValueError(f'{path}: {line_id}: dialogue has no overlap with its scene')
                if not _has_editorial_record(
                        readme, line_id, r'виняток часової належності|time ownership exception'):
                    raise ValueError(f'{path}: {line_id}: boundary crossing requires README explanation')
                neighbors = [
                    other_id for other_id, (other, other_start, other_end) in scene_by_id.items()
                    if other_id != scene_id and other['lifecycle'] == 'active'
                    and start < other_end and end > other_start
                ]
                for neighbor in neighbors:
                    other_readme = root / 'scenes' / neighbor / 'README.md'
                    if not _context_link(other_readme, path, line_id):
                        raise ValueError(f'{path}: {line_id}: missing context link in {other_readme}')

    for base in ('languages', 'pilots', 'scenes'):
        for name in ('dialogue.csv', 'performed.csv'):
            for path in sorted((root / base).rglob(name)):
                required = ('id', 'source_id', 'speaker', 'text', 'status', 'note')
                if name == 'performed.csv':
                    required += ('start', 'end')
                _path, rows = _read_csv(
                    root, path.relative_to(root),
                    required_header=required,
                )
                _unique(rows, 'id', path)
                for row in rows:
                    source_id = _required_value(row, 'source_id', path)
                    if source_id not in canonical:
                        raise ValueError(f'{path}: row {row["_line"]}: dangling source_id {source_id}')
                    _status(row, path)
                    if name == 'performed.csv':
                        start = _time(row['start'], 'start', path, row['_line'])
                        end = _time(row['end'], 'end', path, row['_line'])
                        if not 0 <= start < end:
                            raise ValueError(f'{path}: row {row["_line"]}: invalid performed interval')
                    owner_path = canonical[source_id][0]
                    if owner_path.is_relative_to(root / 'scenes'):
                        _speaker(row, path, characters, owner_path.parent / 'README.md')


def validate_scenes(root=ROOT):
    """Validate scene/source registries below root and return non-error diagnostics.

    Missing scene, coverage, or timing registries are tolerated only while no
    scene rows exist. Returned messages report an unbuilt map and unresolved
    coverage; malformed or inconsistent data raises ValueError.
    """
    root = Path(root)
    index_path, scenes = _read_csv(root, Path('scenes/index.csv'), INDEX_HEADER)
    coverage_path, coverage = _read_csv(
        root, Path('scenes/coverage.csv'), COVERAGE_HEADER
    )
    timing_path, timing = _read_csv(root, Path('source/timing.csv'), TIMING_HEADER)
    media_path, media = _read_csv(
        root, Path('source/media.csv'), required_header=('id',)
    )

    if scenes and (coverage_path is None or timing_path is None or media_path is None):
        missing = [
            label for path, label in (
                (coverage_path, 'scenes/coverage.csv'),
                (timing_path, 'source/timing.csv'),
                (media_path, 'source/media.csv'),
            ) if path is None
        ]
        raise ValueError(
            f'{root}: non-empty scene set requires registries: {", ".join(missing)}'
        )
    if coverage and (timing_path is None or media_path is None):
        raise ValueError(
            f'{root}: coverage rows require source/timing.csv and source/media.csv'
        )

    scene_file = index_path or root / 'scenes/index.csv'
    coverage_file = coverage_path or root / 'scenes/coverage.csv'
    timing_file = timing_path or root / 'source/timing.csv'
    media_file = media_path or root / 'source/media.csv'

    _unique(scenes, 'id', scene_file)
    _unique(coverage, 'id', coverage_file)
    _unique(timing, 'source_id', timing_file)
    _unique(media, 'id', media_file)

    source_ids = {_required_value(row, 'id', media_file) for row in media}
    timings = {}
    for row in timing:
        source_id = _required_value(row, 'source_id', timing_file)
        reference_id = _required_value(row, 'reference_source_id', timing_file)
        if source_id not in source_ids:
            raise ValueError(
                f'{timing_file}: row {row["_line"]}: unknown source_id {source_id}'
            )
        if reference_id not in source_ids:
            raise ValueError(
                f'{timing_file}: row {row["_line"]}: unknown reference_source_id '
                f'{reference_id}'
            )
        duration = _time(row['duration'], 'duration', timing_file, row['_line'])
        if duration <= 0:
            raise ValueError(
                f'{timing_file}: row {row["_line"]}: duration must be positive'
            )
        if not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)', row['offset']):
            raise ValueError(f'{timing_file}: row {row["_line"]}: invalid decimal offset')
        offset = Decimal(row['offset'])
        if source_id == reference_id and offset != 0:
            raise ValueError(
                f'{timing_file}: row {row["_line"]}: self-referenced timing '
                f'must have offset 0'
            )
        if source_id not in {'video', 'audio'} or reference_id != 'video':
            raise ValueError(f'{timing_file}: row {row["_line"]}: timing must reference video')
        timings[source_id] = (duration, reference_id, offset)

    for source_id, (_duration, reference_id, _offset) in timings.items():
        if reference_id not in timings:
            row = next(row for row in timing if row['source_id'] == source_id)
            raise ValueError(
                f'{timing_file}: row {row["_line"]}: missing timing for reference '
                f'source_id {reference_id}'
            )

    scene_by_id = {}
    for row in scenes:
        scene_id = _required_value(row, 'id', scene_file)
        if not re.fullmatch(r'S\d{3,}', scene_id):
            raise ValueError(f'{scene_file}: row {row["_line"]}: invalid scene ID {scene_id}')
        source_id = _required_value(row, 'source_id', scene_file)
        if source_id != 'video':
            raise ValueError(f'{scene_file}: row {row["_line"]}: scene source_id must be video')
        if source_id not in source_ids:
            raise ValueError(
                f'{scene_file}: row {row["_line"]}: unknown source_id {source_id}'
            )
        if source_id not in timings:
            raise ValueError(
                f'{scene_file}: row {row["_line"]}: missing timing for source_id '
                f'{source_id}'
            )
        if row['status'] not in STATUSES:
            raise ValueError(
                f'{scene_file}: row {row["_line"]}: invalid status {row["status"]!r}'
            )
        if row['lifecycle'] not in LIFECYCLES:
            raise ValueError(
                f'{scene_file}: row {row["_line"]}: invalid lifecycle '
                f'{row["lifecycle"]!r}'
            )
        _positive_integer(row['revision'], 'revision', scene_file, row['_line'])
        start = _time(row['start'], 'start', scene_file, row['_line'])
        end = _time(row['end'], 'end', scene_file, row['_line'])
        duration = timings[source_id][0]
        if not 0 <= start < end <= duration:
            raise ValueError(
                f'{scene_file}: row {row["_line"]}: invalid scene interval '
                f'{row["start"]}..{row["end"]} for duration {duration}'
            )
        scene_by_id[scene_id] = (row, start, end)

    coverage_by_scene = {}
    unresolved = {}
    for row in coverage:
        source_id = _required_value(row, 'source_id', coverage_file)
        if source_id != 'video':
            raise ValueError(f'{coverage_file}: row {row["_line"]}: '
                             'primary coverage source_id must be video')
        if source_id not in source_ids:
            raise ValueError(
                f'{coverage_file}: row {row["_line"]}: unknown source_id {source_id}'
            )
        if source_id not in timings:
            raise ValueError(
                f'{coverage_file}: row {row["_line"]}: missing timing for source_id '
                f'{source_id}'
            )
        if row['status'] not in STATUSES:
            raise ValueError(
                f'{coverage_file}: row {row["_line"]}: invalid status {row["status"]!r}'
            )
        kind = row['kind']
        if kind not in COVERAGE_KINDS:
            raise ValueError(
                f'{coverage_file}: row {row["_line"]}: invalid kind {kind!r}'
            )
        if row['scene_id'] != row['scene_id'].strip():
            raise ValueError(
                f'{coverage_file}: row {row["_line"]}: surrounding whitespace '
                'in scene_id'
            )
        scene_id = row['scene_id']
        if kind == 'scene':
            if not scene_id:
                raise ValueError(
                    f'{coverage_file}: row {row["_line"]}: scene segment requires scene_id'
                )
            scene = scene_by_id.get(scene_id)
            if scene is None or scene[0]['lifecycle'] != 'active':
                raise ValueError(
                    f'{coverage_file}: row {row["_line"]}: unknown or non-active '
                    f'scene_id {scene_id}'
                )
            scene_row, scene_start, scene_end = scene
            start = _time(row['start'], 'start', coverage_file, row['_line'])
            end = _time(row['end'], 'end', coverage_file, row['_line'])
            if source_id != scene_row['source_id'] or (start, end) != (
                scene_start, scene_end
            ):
                raise ValueError(
                    f'{coverage_file}: row {row["_line"]}: scene segment does not '
                    f'match scene {scene_id} source and boundaries'
                )
            coverage_by_scene[scene_id] = coverage_by_scene.get(scene_id, 0) + 1
        elif scene_id:
            raise ValueError(
                f'{coverage_file}: row {row["_line"]}: {kind} segment must not have '
                f'scene_id {scene_id}'
            )
        start = _time(row['start'], 'start', coverage_file, row['_line'])
        end = _time(row['end'], 'end', coverage_file, row['_line'])
        if kind == 'unresolved':
            unresolved[source_id] = unresolved.get(source_id, 0) + end - start

    for scene_id, (row, _start, _end) in scene_by_id.items():
        count = coverage_by_scene.get(scene_id, 0)
        if row['lifecycle'] == 'active' and count != 1:
            raise ValueError(
                f'{scene_file}: scene {scene_id} has {count} scene coverage segments; '
                'each active scene requires exactly one'
            )
        if row['lifecycle'] == 'superseded' and count:
            raise ValueError(
                f'{scene_file}: superseded scene {scene_id} must not have coverage'
            )

    diagnostics = []
    if not coverage:
        diagnostics.append('покриття не побудовано.')
    else:
        by_source = {}
        for row in coverage:
            by_source.setdefault(row['source_id'], []).append(row)
        for source_id, segments in by_source.items():
            duration, _reference_id, _offset = timings[source_id]
            _coverage_for_source(segments, source_id, duration, coverage_file)
    for source_id, duration in sorted(unresolved.items()):
        diagnostics.append(
            f'Нерозібраний обсяг для {source_id}: {duration:g} с.'
        )
    _validate_changes(root, scene_by_id, timings, diagnostics)
    _validate_packages(root, scene_by_id, diagnostics)
    _validate_dialogue(root, scene_by_id, timings)
    return diagnostics
