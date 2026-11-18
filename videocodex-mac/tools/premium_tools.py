"""Persistent, CWD-independent V5 tools (Mac version).

Verification never renders; production writes only to new outputs.
Requires: numpy, Pillow, ffmpeg/ffprobe in PATH.
"""
from pathlib import Path
import argparse
import json
import math
import os
import subprocess
import sys
import importlib.util

SK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('salento_tools', SK / 'tools' / 'salento_tools.py')
st = importlib.util.module_from_spec(spec)
spec.loader.exec_module(st)


def configuration():
    return st.config(None)


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def dump(p, data):
    st.write_json(Path(p), data)


def decode(c, p, duration=None):
    import numpy as np
    cmd = [st.tool(c, 'ffmpeg'), '-v', 'error', '-i', str(p)]
    if duration is not None:
        cmd += ['-t', str(duration)]
    return np.frombuffer(
        subprocess.check_output(cmd + ['-f', 'f32le', '-ar', '48000', '-ac', '2', '-']),
        np.float32).reshape(-1, 2).copy()


def excerpt(c, sound):
    import numpy as np
    path = st.safe_audio(c, sound['path'])
    x = decode(c, path, sound['maxDurationSeconds'])
    ni = round(sound.get('fadeInMs', 1) * 48)
    no = round(sound.get('fadeOutMs', 2) * 48)
    if ni + no > len(x):
        raise ValueError('Fades exceed excerpt')
    if ni:
        x[:ni] *= np.linspace(0, 1, ni)[:, None]
    if no:
        x[-no:] *= np.linspace(1, 0, no)[:, None]
    return x


def plan_typing(c, plan):
    from PIL import ImageFont
    import numpy as np
    fps = plan.get('fps', 30)
    font_spec = plan.get('font', {})
    size = font_spec.get('size', 90)
    spacing = font_spec.get('letterSpacing', -0.65)
    font = ImageFont.truetype(str(font_spec.get('path', c['_paths'].get('captionFont', 'Arial'))), size)
    prefix = plan['cuePrefix']
    clicks = plan.get('clicks', [])
    words = plan['words']
    glyphs, events, keys, lines = [], [], {}, {}
    line = 0
    max_width = plan.get('maxWidth', 820)
    last_end = -1
    catalog = {a['path']: a for a in read(c['_paths']['audioCatalog'])['assets']}
    prepared = []
    for sound in clicks:
        sound = dict(sound)
        sound.setdefault('maxDurationSeconds', 0.045)
        sound.setdefault('peakDbFS', -36)
        sound.setdefault('fadeInMs', 1)
        sound.setdefault('fadeOutMs', 2)
        asset = catalog.get(sound['path'], {})
        if not st.cleared(asset):
            raise ValueError('Click rights unavailable: ' + sound['path'])
        if sound['path'].startswith('Music/'):
            raise ValueError('No embedded music')
        x = excerpt(c, sound)
        if not len(x) or np.max(np.abs(x)) < 1e-7:
            raise ValueError('Silent typing excerpt: ' + sound['path'])
        sound['sourcePeakMs'] = int(np.argmax(np.max(np.abs(x), axis=1))) / 48
        prepared.append(sound)

    def measure(t):
        return float(font.getlength(t) + spacing * len(t))

    for wi, word in enumerate(words):
        start = word['startMs'] / 1000
        end = word['endMs'] / 1000
        text = word['text']
        if end < start or start < last_end - 0.001:
            raise ValueError('Words must use ordered real voice intervals')
        last_end = end
        line = word.get('line', line)
        lines.setdefault(line, '')
        if lines[line] and measure(lines[line] + ' ' + text) > max_width and 'line' not in word:
            line += 1
            lines.setdefault(line, '')
        if lines[line]:
            prev = glyphs[-1]
            glyphs.append({'char': ' ', 'cue': prev['cue'], 'word': wi, 'line': line,
                           'x': measure(lines[line]), 'width': measure(' ')})
            lines[line] += ' '
        duration = min(end - start, plan.get('maxWordSeconds', 0.2), max(0.10, len(text) * 0.022))
        for i, ch in enumerate(text):
            frame = max(2, round((start + duration * i / max(1, len(text) - 1)) * fps))
            ident = keys.get(frame)
            if ident is None:
                ident = f'{prefix}-key-{len(events)}'
                keys[frame] = ident
                e = {'id': ident, 'frame': frame, 'component': 'TypingTitle', 'phase': 'character'}
                if prepared:
                    e['sound'] = dict(prepared[(i + wi) % len(prepared)])
                events.append(e)
            g = {'char': ch, 'cue': ident, 'word': wi, 'line': line,
                 'x': measure(lines[line]), 'width': measure(ch)}
            if word.get('color'):
                g['color'] = word['color']
            glyphs.append(g)
            lines[line] += ch
    return {'fps': fps, 'durationInFrames': plan['durationInFrames'],
            'measuredFontSize': size, 'glyphs': glyphs, 'events': events,
            'additionalComponents': ['TypingTitle'], 'lines': lines,
            'lineWidths': {k: measure(v) for k, v in lines.items()},
            'note': 'Merge events with the other motion events, then compile-cues; '
                    'glyphs resolve the compiled cue, not a copied frame.'}


def mix(c, director, voice, output):
    import numpy as np
    if director['fps'] != 30 or director.get('sampleRate') != 48000:
        raise ValueError('Use the canonical 30fps/48kHz compiler')
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Choose a new mix output folder; completed productions are immutable')
    n = director['durationInFrames'] * 1600
    vo = decode(c, voice)
    if math.ceil(len(vo) / 48000 * 30) != director['durationInFrames']:
        raise ValueError('Duration must be derived from this original voice')
    audio = np.zeros((n, 2), np.float32)
    catalog = {a['path']: a for a in read(c['_paths']['audioCatalog'])['assets']}
    audit = []
    for e in director['events']:
        if not e.get('audio'):
            continue
        a = e['audio']
        path = a['path']
        source = st.safe_audio(c, path)
        entry = catalog.get(path, {})
        if path.startswith('Music/') or not st.cleared(entry) or st.digest(source) != a['sha256']:
            raise ValueError('Audio unavailable/changed/uncleared: ' + path)
        if a['startSample'] + a['peakSample'] != e['frame'] * 1600:
            raise ValueError('Cue/keyframe sample mismatch: ' + e['id'])
        sound = {'path': path, 'maxDurationSeconds': a['sampleCount'] / 48000,
                 'fadeInMs': a['fadeInMs'], 'fadeOutMs': a['fadeOutMs']}
        x = excerpt(c, sound)
        x /= max(float(np.max(np.abs(x))), 1e-9)
        x *= 10 ** (a['peakDbFS'] / 20)
        pan = e.get('pan', 0)
        if abs(pan) > 1:
            raise ValueError('Pan must be within [-1,1]')
        x[:, 0] *= math.sqrt(1 - pan * 0.85)
        x[:, 1] *= math.sqrt(1 + pan * 0.85)
        start = a['startSample']
        stop = start + len(x)
        if start < 0 or stop > n:
            raise ValueError('Cue outside voice duration: ' + e['id'])
        audio[start:stop] += x
        audit.append({'id': e['id'], 'frame': e['frame'], 'startSample': start,
                      'peakSample': a['peakSample'], 'pan': pan, 'nominalPeakDbFS': a['peakDbFS']})
    voice_stem = np.zeros_like(audio)
    voice_stem[:len(vo)] = vo
    # Speech-aware soft ducking: 10ms attack, 120ms release, maximum 3dB. No music bus.
    envelope = 0.0
    for start in range(0, n, 480):
        level = float(np.sqrt(np.mean(voice_stem[start:start + 480] ** 2)))
        target = 1.0 if level > 0.015 else 0.0
        envelope = target if target > envelope else envelope + (target - envelope) / 12
        audio[start:start + 480] *= 10 ** (-3 * envelope / 20)
    output.mkdir(parents=True)

    def wav(name, x):
        subprocess.run([st.tool(c, 'ffmpeg'), '-v', 'error', '-f', 'f32le', '-ar', '48000',
                        '-ac', '2', '-i', '-', '-c:a', 'pcm_s24le', '-y', str(output / name)],
                       input=x.astype(np.float32).tobytes(), check=True)

    wav('VOICEOVER_STEM.wav', voice_stem)
    wav('SFX_STEM.wav', audio)
    wav('MIX_RAW.wav', voice_stem + audio)
    log = subprocess.run(
        [st.tool(c, 'ffmpeg'), '-hide_banner', '-i', str(output / 'MIX_RAW.wav'),
         '-af', 'loudnorm=I=-16:TP=-1.8:LRA=11:print_format=json', '-f', 'null', '-'],
        capture_output=True, text=True, check=True).stderr
    m = json.loads(log[log.rfind('{'):log.rfind('}') + 1])
    af = (f"loudnorm=I=-16:TP=-1.8:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
          f"offset={m['target_offset']}:linear=true")
    subprocess.run([st.tool(c, 'ffmpeg'), '-v', 'error', '-i', str(output / 'MIX_RAW.wav'),
                    '-af', af, '-ar', '48000', '-c:a', 'pcm_s24le', '-y', str(output / 'MIX.wav')],
                   check=True)
    dump(output / 'mix-audit.json',
         {'voiceSHA256': st.digest(voice), 'music': False, 'cueCount': len(audit), 'cues': audit,
          'duckingDb': 3, 'loudnessPass1': m,
          'validation': 'Measure LUFS/true peak again on the exported MP4; this audit is not final QA.'})
    return {'output': str(output), 'cueCount': len(audit)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    t = sub.add_parser('plan-typing')
    t.add_argument('--plan', type=Path, required=True)
    t.add_argument('--output', type=Path, required=True)
    m = sub.add_parser('mix')
    m.add_argument('--director', type=Path, required=True)
    m.add_argument('--voice', type=Path, required=True)
    m.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    c = configuration()
    if args.command == 'plan-typing':
        if args.output.exists():
            raise ValueError('Refusing to overwrite an existing typing plan')
        result = plan_typing(c, read(args.plan))
        dump(args.output, result)
    else:
        result = mix(c, read(args.director), args.voice, args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as e:
        raise SystemExit('ERROR: ' + str(e))
