"""Pipeline sperimentale: testo + voce ElevenLabs + clip -> bozza verticale.

Leggere README_MAC.md prima di eseguire: le clip e la revisione restano manuali.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import uuid
from pathlib import Path

import salento_tools as st
import premium_tools as premium

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'GONDAR_FINAL'


def run(cmd, cwd=None):
    subprocess.run([str(x) for x in cmd], check=True, cwd=cwd)


def split_script(text):
    chunks = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', text) if s.strip()]
    if not chunks:
        raise ValueError('Il testo è vuoto')
    # Keep the number of manually generated clips manageable.
    while len(chunks) > 6:
        chunks[-2:] = [' '.join(chunks[-2:])]
    return chunks


def init(script, directory, title):
    text = script.read_text(encoding='utf8').strip()
    sentences = split_script(text)
    if directory.exists():
        raise ValueError('La cartella esiste: scegli un nome nuovo')
    if not title.strip() or len(title) > 70:
        raise ValueError('Titolo richiesto, massimo 70 caratteri')
    directory.mkdir(parents=True)
    (directory / 'script.txt').write_text(text + '\n', encoding='utf8')
    scenes = {'title': title, 'scenes': [
        {'text': sentence, 'clip': f'clip-{i:02d}.mp4',
         'prompt': (f'Visual illustration for this narration: {sentence}. '
                    'Vertical 9:16 cinematic footage, no written text, no logos. '
                    'Do not depict invented footage as documentary evidence.')}
        for i, sentence in enumerate(sentences, 1)]}
    st.write_json(directory / 'scenes.json', scenes)
    (directory / 'clips').mkdir()
    lines = ['# Prompt da revisionare prima dell’uso', '',
             'Per ogni scena crea una clip verticale e salvala con il nome indicato nella cartella clips.',
             'I prompt sono bozze automatiche: specifica luogo, inquadratura e stile; verifica diritti e accuratezza.', '']
    for i, scene in enumerate(scenes['scenes'], 1):
        lines += [f'## Scena {i} — {scene["clip"]}', '', f'Testo: {scene["text"]}', '', scene['prompt'], '']
    (directory / 'prompts.md').write_text('\n'.join(lines), encoding='utf8')
    print(f'Progetto creato: {directory} — {len(sentences)} clip richieste. Vedi prompts.md.')


def elevenlabs(text, target, voice_id, model):
    key = os.environ.get('ELEVENLABS_API_KEY')
    if not key or not voice_id:
        raise ValueError('Per ElevenLabs imposta ELEVENLABS_API_KEY e --voice-id (o ELEVENLABS_VOICE_ID)')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', voice_id):
        raise ValueError('Voice ID non valido')
    payload = json.dumps({'text': text, 'model_id': model}).encode('utf8')
    req = urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}',
        data=payload, headers={'xi-api-key': key, 'Content-Type': 'application/json', 'Accept': 'audio/mpeg'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=180) as response, target.open('xb') as f:
            shutil.copyfileobj(response, f)
    except urllib.error.HTTPError as e:
        raise ValueError(f'ElevenLabs ha risposto HTTP {e.code}; controlla account, quota e Voice ID') from None


def probe(c, file):
    data = subprocess.check_output([st.tool(c, 'ffprobe'), '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(file)], text=True)
    return json.loads(data)


def validate_captions(captions, duration_seconds):
    if not isinstance(captions, list) or not captions:
        raise ValueError('Nessuna caption: controlla audio o trascrizione')
    previous = -1
    for item in captions:
        a, b = item.get('startMs'), item.get('endMs')
        if not isinstance(item.get('text'), str) or not item['text'].strip() or \
           not isinstance(a, (int, float)) or not isinstance(b, (int, float)) or \
           not math.isfinite(a) or not math.isfinite(b) or a < previous or b <= a or b > duration_seconds * 1000 + 50:
            raise ValueError(f'Caption non valida o fuori dalla voce: {item}')
        previous = a


def prepare(directory, source, use_eleven, voice_id, model, whisper, captions_path, transition_sfx):
    c = st.config()
    directory = directory.resolve()
    scenes = st.read_json(directory / 'scenes.json')
    if not scenes.get('scenes') or not scenes.get('title'):
        raise ValueError('scenes.json deve contenere title e almeno una scena')
    text = (directory / 'script.txt').read_text(encoding='utf8').strip()
    if not text:
        raise ValueError('Script vuoto')
    scene_text = ' '.join(str(s.get('text', '')) for s in scenes['scenes'])
    if ' '.join(scene_text.split()) != ' '.join(text.split()):
        raise ValueError('Il testo delle scene non corrisponde allo script: riallinea scenes.json')
    if not isinstance(scenes['title'], str) or len(scenes['title']) > 70:
        raise ValueError('Titolo non valido: massimo 70 caratteri')
    work = directory / 'prepared'
    if work.exists():
        raise ValueError('prepared esiste già: rinominala o crea un nuovo progetto per riprovare')
    if not use_eleven and (not source or not source.is_file()):
        raise ValueError('Indica un audio esistente con --voice oppure scegli --elevenlabs')
    ffmpeg = st.tool(c, 'ffmpeg')
    st.tool(c, 'ffprobe')
    work.mkdir()
    if use_eleven:
        print('Invio del testo a ElevenLabs; il servizio può consumare crediti.', flush=True)
        source = work / 'elevenlabs-original.mp3'
        elevenlabs(text, source, voice_id, model)
    else:
        source = source.resolve()
    voice = work / 'voice.wav'
    run([ffmpeg, '-v', 'error', '-i', source, '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s16le', '-n', voice])
    import wave
    with wave.open(str(voice), 'rb') as w:
        frames = w.getnframes()
    if frames <= 0:
        raise ValueError('La voce è vuota')
    duration = math.ceil(frames / 1600)
    if captions_path:
        captions = st.read_json(captions_path)
    else:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise ValueError('Installa faster-whisper oppure fornisci --captions') from None
        print(f'Trascrizione con Whisper {whisper} su CPU; il primo avvio scarica il modello.', flush=True)
        model_instance = WhisperModel(whisper, device='cpu', compute_type='int8')
        segments, _ = model_instance.transcribe(str(voice), language='it', word_timestamps=True)
        captions = [{'text': w.word.strip(), 'startMs': round(w.start * 1000), 'endMs': round(w.end * 1000)}
                    for s in segments for w in (s.words or []) if w.word.strip() and w.end > w.start]
    validate_captions(captions, frames / 48000)
    st.write_json(work / 'captions.json', captions)
    # Partition at recognized word boundaries based on relative amount of script in each scene.
    scene_data = scenes['scenes']
    if len(scene_data) > len(captions):
        raise ValueError('Troppe scene rispetto alle parole riconosciute')
    weights = [max(1, len(s.get('text', '').split())) for s in scene_data]
    boundaries = [0]
    cumulative = 0
    for i, weight in enumerate(weights[:-1]):
        cumulative += weight
        idx = round(cumulative / sum(weights) * len(captions))
        idx = max(i + 1, min(len(captions) - (len(weights) - i - 1), idx))
        boundary = round(captions[idx]['startMs'] * 30 / 1000)
        boundary = max(boundaries[-1] + 1, min(duration - (len(weights) - i - 1), boundary))
        boundaries.append(boundary)
    boundaries.append(duration)
    events, timeline = [], []
    sound = None
    if transition_sfx:
        peak = st.measure_peak(c, transition_sfx, 0.3)
        sound = {'path': transition_sfx, 'sourcePeakMs': peak['sourcePeakMs'],
                 'peakDbFS': -25, 'maxDurationSeconds': 0.3, 'fadeInMs': 1, 'fadeOutMs': 4}
    for i, scene in enumerate(scene_data):
        cue = f'scene-{i + 1:02d}'
        start, end = boundaries[i:i + 2]
        event = {'id': cue, 'frame': start, 'component': 'TypingTitle' if i == 0 else 'SceneBackground', 'phase': 'start'}
        if i > 0 and sound:
            event['sound'] = dict(sound)
        events.append(event)
        name = scene.get('clip', '')
        if not isinstance(name, str) or not name or Path(name).name != name or not name.lower().endswith('.mp4'):
            raise ValueError('Ogni scena deve indicare un semplice nome file .mp4')
        timeline.append({'startFrame': start, 'durationInFrames': end - start, 'cueId': cue, 'clip': name})
    manifest = {'fps': 30, 'durationInFrames': duration, 'additionalComponents': ['SceneBackground'], 'events': events}
    st.write_json(work / 'cues.manifest.json', manifest)
    director = st.compile_cues(c, manifest, work / 'director.json')
    # If no licensed library is provided, keep voice and a silent SFX stem.
    premium.mix(c, director, voice, work / 'mix')
    st.write_json(work / 'timeline.json', {'title': scenes['title'], 'durationInFrames': duration, 'scenes': timeline,
                                           'voiceSha256': st.digest(voice), 'mixSha256': st.digest(work / 'mix' / 'MIX.wav'),
                                           'scriptSha256': st.digest(directory / 'script.txt')})
    print('Preparazione completata. Correggi prepared/captions.json e verifica scene/timing in prepared/timeline.json.')
    if not sound:
        print('Non ci sono SFX: per i cambi scena usa --transition-sfx dopo aver verificato i diritti.')
    else:
        print('SFX applicato ai cambi scena. Ascolta e regola: il typing non ha ancora SFX.')


def render(directory, allow_placeholders, reviewed):
    if not reviewed:
        raise ValueError('Prima controlla testo, caption, timing e diritti delle clip, poi aggiungi --reviewed')
    c = st.config()
    directory = directory.resolve()
    work = directory / 'prepared'
    timeline = st.read_json(work / 'timeline.json')
    director = st.read_json(work / 'director.json')
    captions = st.read_json(work / 'captions.json')
    voice = work / 'voice.wav'
    if st.digest(voice) != timeline['voiceSha256'] or st.digest(directory / 'script.txt') != timeline['scriptSha256']:
        raise ValueError('Voce o script modificati dopo la preparazione: ricrea prepared')
    if st.digest(work / 'mix' / 'MIX.wav') != timeline['mixSha256']:
        raise ValueError('Il mix è stato modificato dopo la preparazione')
    duration = timeline['durationInFrames']
    validate_captions(captions, duration / 30)
    if director['durationInFrames'] != duration or director['fps'] != 30:
        raise ValueError('Director e timeline non corrispondono')
    previous_end = 0
    for scene in timeline['scenes']:
        if (scene['startFrame'] != previous_end or scene['durationInFrames'] <= 0 or
                director['keyframes'].get(scene['cueId']) != scene['startFrame']):
            raise ValueError('Scene non continue o non sincronizzate con il director')
        previous_end += scene['durationInFrames']
    if previous_end != duration:
        raise ValueError('La durata delle scene non corrisponde alla voce')
    result = directory / 'output'
    if result.exists():
        raise ValueError('output esiste già: scegli un progetto diverso o conserva/rinomina il vecchio output')
    if not (PROJECT / 'node_modules' / '.bin' / 'remotion').exists():
        raise ValueError('Prima esegui npm ci nella cartella GONDAR_FINAL')
    paths = []
    warnings = []
    for scene in timeline['scenes']:
        clip = (directory / 'clips' / scene['clip']).resolve()
        if not clip.is_relative_to((directory / 'clips').resolve()):
            raise ValueError('Clip fuori dalla cartella clips')
        if not clip.is_file():
            if not allow_placeholders:
                raise ValueError(f'Clip mancante: {clip}. Per una bozza usa --allow-placeholders')
            warnings.append(f'Clip mancante: {scene["clip"]}; sfondo segnaposto')
            paths.append(None)
            continue
        meta = probe(c, clip)
        if not any(s.get('codec_type') == 'video' for s in meta['streams']):
            raise ValueError(f'Non è un video: {clip}')
        secs = float(meta.get('format', {}).get('duration', 0))
        if not math.isfinite(secs) or secs <= 0:
            raise ValueError(f'Durata clip non valida: {clip}')
        paths.append((clip, max(1, math.floor(secs * 30))))
    staging = PROJECT / 'public' / 'pipeline' / uuid.uuid4().hex
    result.mkdir()
    staging.mkdir(parents=True)
    try:
        mix = work / 'mix' / 'MIX.wav'
        shutil.copy2(mix, staging / 'mix.wav')
        for index, (scene, source) in enumerate(zip(timeline['scenes'], paths), 1):
            if source:
                target = staging / f'clip-{index:02d}.mp4'
                shutil.copy2(source[0], target)
                scene['clip'] = target.relative_to(PROJECT / 'public').as_posix()
                scene['clipFrames'] = source[1]
            else:
                scene.pop('clip', None)
        props = {'durationInFrames': duration, 'title': timeline['title'], 'captions': captions,
                 'audio': (staging / 'mix.wav').relative_to(PROJECT / 'public').as_posix(),
                 'scenes': timeline['scenes'], 'director': director}
        props_file = result / 'props.json'
        st.write_json(props_file, props)
        output = result / 'reel.mp4'
        command = [PROJECT / 'node_modules' / '.bin' / 'remotion', 'render', PROJECT / 'src' / 'index.ts',
                   'AutomaticReel', output, '--props', props_file, '--concurrency=1', '--codec=h264', '--audio-codec=aac']
        if os.environ.get('REMOTION_BROWSER_EXECUTABLE'):
            command += ['--browser-executable', os.environ['REMOTION_BROWSER_EXECUTABLE']]
        run(command, cwd=PROJECT)
        metadata = probe(c, output)
        measured = subprocess.run([st.tool(c, 'ffmpeg'), '-hide_banner', '-i', str(output), '-af',
                                   'loudnorm=I=-16:TP=-1.8:LRA=11:print_format=json', '-f', 'null', os.devnull],
                                  capture_output=True, text=True, check=True).stderr
        loudness = json.loads(measured[measured.rfind('{'):measured.rfind('}') + 1])
        st.write_json(result / 'qa.json', {'metadata': metadata, 'loudness': loudness, 'warnings': warnings + [
            'Controllare LUFS e true peak misurati, sincronizzazione, diritti e autenticità delle clip.',
            ('SFX solo ai cambi scena; typing senza SFX.' if any(e.get('audio') for e in director['events'])
             else 'Nessun SFX: versione preliminare non equivalente al preset originale V5.'),
            'La revisione umana resta necessaria; tempistiche delle scene basate su una stima.']})
        print(f'Video pronto per revisione: {output}\nControlla output/qa.json.')
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    i = sub.add_parser('init')
    i.add_argument('--script', type=Path, required=True)
    i.add_argument('--dir', type=Path, required=True)
    i.add_argument('--title', required=True)
    p = sub.add_parser('prepare')
    p.add_argument('--dir', type=Path, required=True)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--voice', type=Path)
    group.add_argument('--elevenlabs', action='store_true')
    p.add_argument('--voice-id', default=os.environ.get('ELEVENLABS_VOICE_ID'))
    p.add_argument('--eleven-model', default='eleven_multilingual_v2')
    p.add_argument('--whisper-model', default='base')
    p.add_argument('--captions', type=Path, help='Caption già revisionate, per saltare Whisper')
    p.add_argument('--transition-sfx', help='File relativo ad AUDIO_LIBRARY, già autorizzato e scansionato')
    r = sub.add_parser('render')
    r.add_argument('--dir', type=Path, required=True)
    r.add_argument('--reviewed', action='store_true')
    r.add_argument('--allow-placeholders', action='store_true')
    args = parser.parse_args()
    if args.command == 'init':
        init(args.script, args.dir, args.title)
    elif args.command == 'prepare':
        prepare(args.dir, args.voice, args.elevenlabs, args.voice_id, args.eleven_model, args.whisper_model, args.captions, args.transition_sfx)
    else:
        render(args.dir, args.allow_placeholders, args.reviewed)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as e:
        sys.exit(f'ERROR: {e}')
