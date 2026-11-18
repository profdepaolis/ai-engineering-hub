"""Local helpers for the existing Salento system. Never render or modify a Reel."""
from __future__ import annotations
import argparse
import array
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

SKILL = Path(__file__).resolve().parents[1]
AUDIO_EXTENSIONS = {'.wav', '.mp3', '.wma', '.flac', '.ogg', '.m4a', '.aiff', '.aif', '.aac', '.opus'}

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def write_json(path, data, backup=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if backup and path.exists():
        shutil.copy2(path, path.with_name(path.name + '.previous'))
    fd, temporary = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf8', newline='\n') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n')
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

def config(path=None):
    c = read_json(path or SKILL / 'config.json')
    root = Path(os.environ.get('BENVENUTI_SALENTO_ROOT', c['workspaceRoot'])).resolve()
    resolved = {}
    for key, rel in c['paths'].items():
        p = (root / rel).resolve()
        if not p.is_relative_to(root):
            raise ValueError(f'Configured path escapes workspace: {key}')
        resolved[key] = p
    c['_root'], c['_paths'] = root, resolved
    return c

def tool(c, name):
    value = os.environ.get('BENVENUTI_SALENTO_' + name.upper(), c['runtime'].get(name, name))
    found = str(Path(value)) if Path(value).is_file() else shutil.which(value)
    if not found:
        raise ValueError(f'{name} unavailable; update runtime paths in config.json')
    return found

def verify(c):
    checks = {k: {'path': str(v), 'exists': v.exists()} for k, v in c['_paths'].items()}
    source = c['_paths']['components'].read_text(encoding='utf8')
    exports = c['_paths']['exports'].read_text(encoding='utf8')
    components = {name: bool(re.search(r'export\s+const\s+' + re.escape(name) + r'\b', source) and re.search(r'\b' + re.escape(name) + r'\b', exports)) for name in c['requiredComponents']}
    runtime = {name: bool(Path(path).is_file() or shutil.which(path)) for name, path in c['runtime'].items()}
    result = {'workspaceRoot': str(c['_root']), 'paths': checks, 'components': components, 'runtime': runtime}
    result['passed'] = all(p['exists'] for p in checks.values()) and all(components.values()) and all(runtime.values())
    return result

def cleared(entry):
    status = str(entry.get('licenseStatus', '')).upper()
    use = str(entry.get('commercialUse', '')).upper()
    return status in {'USER_CONFIRMED', 'VERIFIED', 'LICENSE_VERIFIED'} and (use.startswith('AUTHORIZED') or use.startswith('ALLOWED') or use == 'CLEARED')

def scan_audio(c, output=None):
    library, catalog = c['_paths']['audioLibrary'], c['_paths']['audioCatalog']
    old = read_json(catalog) if catalog.exists() else {'schemaVersion': 1, 'assets': []}
    old_by_path = {a['path'].replace('\\', '/'): a for a in old.get('assets', [])}
    entries, seen = [], set()
    counts = {'new': 0, 'changed': 0, 'unchanged': 0, 'missing': 0, 'fingerprintBaselines': 0}
    for path in sorted(library.rglob('*')):
        if not path.is_file() or path.suffix.lower() not in AUDIO_EXTENSIONS:
            continue
        rel = path.relative_to(library).as_posix()
        seen.add(rel)
        previous = old_by_path.get(rel)
        entry = copy.deepcopy(previous) if previous else {'path': rel, 'licenseStatus': 'UNKNOWN', 'commercialUse': 'NOT_CLEARED', 'licenseEvidence': None}
        sha = digest(path)
        changed = previous is not None and previous.get('sha256') is not None and previous['sha256'] != sha
        category = path.parent.relative_to(library).as_posix()
        entry.update(path=rel, category=category if category != '.' else 'Uncategorized', sha256=sha, sizeBytes=path.stat().st_size, status='AVAILABLE')
        if changed:
            entry['previousAuthorization'] = {k: previous.get(k) for k in ('sha256', 'licenseStatus', 'commercialUse', 'licenseEvidence')}
            entry.update(licenseStatus='UNKNOWN', commercialUse='NOT_CLEARED', licenseEvidence=None, rightsReviewReason='CONTENT_CHANGED')
        if previous is None or changed or previous.get('durationSeconds') is None:
            raw = subprocess.run([tool(c, 'ffprobe'), '-v', 'error', '-show_entries', 'format=duration:stream=codec_type,sample_rate,channels', '-of', 'json', str(path)], capture_output=True, text=True, check=True)
            meta = json.loads(raw.stdout)
            stream = next(s for s in meta['streams'] if s.get('codec_type') == 'audio')
            levels = subprocess.run([tool(c, 'ffmpeg'), '-hide_banner', '-i', str(path), '-af', 'volumedetect', '-vn', '-sn', '-dn', '-f', 'null', os.devnull], capture_output=True, text=True, check=True).stderr
            entry.update(durationSeconds=float(meta['format']['duration']), sampleRate=int(stream['sample_rate']), channels=int(stream['channels']))
            for field, token in [('meanVolumeDb', 'mean_volume'), ('peakVolumeDb', 'max_volume')]:
                match = re.search(token + r':\s*(-?[\d.]+) dB', levels)
                entry[field] = float(match.group(1)) if match else None
        if previous is None:
            counts['new'] += 1
        elif changed:
            counts['changed'] += 1
        else:
            counts['unchanged'] += 1
            if not previous.get('sha256'):
                counts['fingerprintBaselines'] += 1
                entry['fingerprintNote'] = 'First SHA256 baseline; historical authorization retained from existing catalog, no retroactive integrity claim.'
        entries.append(entry)
    for rel, previous in old_by_path.items():
        if rel not in seen:
            entries.append({**previous, 'status': 'MISSING'})
            counts['missing'] += 1
    result = {**old, 'schemaVersion': 2, 'levelMethod': 'FFmpeg volumedetect RMS and sample peak; not LUFS or true peak', 'assets': entries}
    comparable = {k: v for k, v in result.items() if k != 'generatedAt'}
    old_comparable = {k: v for k, v in old.items() if k != 'generatedAt'}
    changed_catalog = comparable != old_comparable
    target = Path(output) if output else catalog
    if output or changed_catalog:
        result['generatedAt'] = datetime.now(timezone.utc).isoformat()
        write_json(target, result, backup=not output and catalog.exists())
    counts.update(available=len(seen), authorized=sum(cleared(a) and a.get('status') != 'MISSING' for a in entries), output=str(target), written=bool(output or changed_catalog))
    return counts

def safe_audio(c, relative):
    root = c['_paths']['audioLibrary'].resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f'Audio asset missing or outside AUDIO_LIBRARY: {relative}')
    return path

def measure_peak(c, relative, maximum):
    path = safe_audio(c, relative)
    if not math.isfinite(maximum) or not 0 < maximum <= 30:
        raise ValueError('max-duration must be finite, >0 and <=30 seconds')
    sr = 48000
    raw = subprocess.check_output([tool(c, 'ffmpeg'), '-v', 'error', '-i', str(path), '-t', str(maximum), '-ar', str(sr), '-ac', '1', '-f', 'f32le', '-'])
    samples = array.array('f')
    samples.frombytes(raw)
    if not samples:
        raise ValueError('Empty audio')
    window = 480
    energies = [sum(v * v for v in samples[i:i + window]) / len(samples[i:i + window]) for i in range(0, len(samples), window)]
    block = max(range(len(energies)), key=energies.__getitem__)
    peak = min(len(samples) - 1, block * window + window // 2)
    return {'path': relative, 'sourcePeakSample': peak, 'sourcePeakMs': peak / 48, 'sampleRate': sr, 'method': 'Maximum 10 ms RMS block; confirm perceptual timing after fades', 'maxDurationSeconds': maximum}

def compile_cues(c, manifest, output=None, overwrite=False):
    if manifest.get('fps') != 30:
        raise ValueError('This output contract requires fps=30')
    duration = manifest.get('durationInFrames')
    if type(duration) is not int or duration <= 0:
        raise ValueError('durationInFrames must be a positive integer derived from the voiceover')
    catalog = read_json(c['_paths']['audioCatalog'])
    by_path = {a['path'].replace('\\', '/'): a for a in catalog['assets']}
    out = {'schemaVersion': 1, 'fps': 30, 'sampleRate': 48000, 'durationInFrames': duration, 'keyframes': {}, 'events': []}
    for original in manifest.get('events', []):
        event = copy.deepcopy(original)
        ident, frame = event.get('id'), event.get('frame')
        if not isinstance(ident, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]*', ident) or ident in out['keyframes']:
            raise ValueError(f'Invalid/duplicate cue id: {ident}')
        if type(frame) is not int or not 0 <= frame < duration:
            raise ValueError(f'Cue frame outside timeline: {ident}')
        if event.get('component') not in c['requiredComponents'] and event.get('component') not in manifest.get('additionalComponents', []):
            raise ValueError(f'Unknown component for {ident}; register additive extensions in additionalComponents')
        if not event.get('phase'):
            raise ValueError(f'Animation phase missing: {ident}')
        out['keyframes'][ident] = frame
        if event.get('sound'):
            sound = event['sound']
            rel = sound['path'].replace('\\', '/')
            path = safe_audio(c, rel)
            entry = by_path.get(rel, {})
            if not cleared(entry) or entry.get('status') == 'MISSING':
                raise ValueError(f'Audio rights unavailable: {rel}')
            if entry.get('sha256') and entry['sha256'] != digest(path):
                raise ValueError(f'Audio replaced since catalog scan: {rel}')
            peak_ms = sound.get('sourcePeakMs')
            gain = sound.get('peakDbFS')
            maximum = sound.get('maxDurationSeconds')
            if not isinstance(peak_ms, (int, float)) or not math.isfinite(peak_ms) or peak_ms < 0:
                raise ValueError(f'Measured sourcePeakMs required: {ident}')
            if not isinstance(gain, (int, float)) or not math.isfinite(gain) or not -80 <= gain <= -1:
                raise ValueError(f'peakDbFS must be within -80..-1: {ident}')
            if not isinstance(maximum, (int, float)) or not math.isfinite(maximum) or maximum <= 0:
                raise ValueError(f'maxDurationSeconds required: {ident}')
            available = float(entry.get('durationSeconds', 0))
            seconds = min(maximum, available)
            peak_sample = round(peak_ms * 48)
            target_sample = frame * 1600
            start = target_sample - peak_sample
            sample_count = round(seconds * 48000)
            if start < 0 or peak_sample >= sample_count or start + sample_count > duration * 1600:
                raise ValueError(f'Cue cannot align within timeline; select/trim another sound: {ident}')
            fades = [float(sound.get(k, 15 if k == 'fadeInMs' else 35)) for k in ['fadeInMs', 'fadeOutMs']]
            if any(not math.isfinite(v) or v < 0 for v in fades) or sum(fades) > seconds * 1000:
                raise ValueError(f'Invalid fades: {ident}')
            event['audio'] = {'path': rel, 'sha256': digest(path), 'startSample': start, 'peakSample': peak_sample, 'targetSample': target_sample, 'sampleCount': sample_count, 'peakDbFS': gain, 'fadeInMs': fades[0], 'fadeOutMs': fades[1], 'licenseStatus': entry['licenseStatus']}
        out['events'].append(event)
    if not out['events']:
        raise ValueError('No animation events')
    if output:
        destination = Path(output).resolve()
        protected = {p.resolve() for p in c['_paths'].values() if p.is_file()}
        if destination in protected:
            raise ValueError('Cannot overwrite an existing canonical system/legacy file')
        if destination.exists() and not overwrite:
            raise ValueError('Output exists; choose a new path or explicitly use --overwrite')
        if destination.suffix.lower() != '.json':
            raise ValueError('Cue output must be JSON')
        write_json(destination, out, backup=destination.exists())
    return out

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('verify')
    scan = sub.add_parser('scan-audio'); scan.add_argument('--output', type=Path)
    peak = sub.add_parser('peak'); peak.add_argument('--asset', required=True); peak.add_argument('--max-duration', type=float, default=2)
    cues = sub.add_parser('compile-cues'); cues.add_argument('--manifest', type=Path, required=True); cues.add_argument('--output', type=Path, required=True); cues.add_argument('--overwrite', action='store_true')
    args = parser.parse_args(); c = config(args.config)
    if args.command == 'verify':
        result = verify(c)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['passed'] else 1
    if args.command == 'scan-audio': result = scan_audio(c, args.output)
    elif args.command == 'peak': result = measure_peak(c, args.asset, args.max_duration)
    else:
        compiled = compile_cues(c, read_json(args.manifest), args.output, args.overwrite)
        result = {'output': str(args.output), 'events': len(compiled['events']), 'audioEvents': sum('audio' in e for e in compiled['events'])}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        raise SystemExit(f'ERROR: {error}')
