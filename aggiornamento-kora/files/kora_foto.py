"""Prepara o renderizza una bozza KORA da foto locali e dalla voce già preparata.
La voce non viene rigenerata. Richiede revisione umana prima della pubblicazione.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

from PIL import Image, ImageOps
import salento_tools as st

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'GONDAR_FINAL'
INTRO = 60
OUTRO = 60
# Punti di stacco riferiti ai tempi di voce KORA esaminati; fotografie colazione/aperitivo sui passaggi corrispondenti.
CUTS = [0, 308, 565, 686, 744, 884, 1147, 1306, 1478]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def choose_assets(folder):
    folder = folder.resolve()
    if not folder.is_dir():
        raise ValueError('La cartella delle foto non esiste')
    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in {'.jpg', '.jpeg', '.png'}]
    logos = [p for p in files if 'logo' in p.name.casefold() and 'kora' in p.name.casefold()]
    generated = sorted((p for p in files if p.name.casefold().startswith('immagine chatgpt')), key=lambda p: p.name.casefold())
    breakfast = [p for p in files if 'colazione' in p.name.casefold()]
    aperitifs = [p for p in files if 'aperitivo' in p.name.casefold()]
    if len(logos) != 1 or len(generated) != 6 or len(breakfast) != 1 or len(aperitifs) != 1:
        raise ValueError('Servono un logo KORA, sei immagini ChatGPT, una colazione e un aperitivo nella cartella indicata')
    photos = [generated[0], generated[1], generated[2], breakfast[0], aperitifs[0], generated[3], generated[4], generated[5]]
    for file in [logos[0]] + photos:
        with Image.open(file) as img:
            img.verify()
    return logos[0], photos


def load_prepared(reel):
    prepared = reel / 'prepared'
    timeline = st.read_json(prepared / 'timeline.json')
    captions = st.read_json(prepared / 'captions.json')
    director = st.read_json(prepared / 'director.json')
    if timeline.get('durationInFrames') != CUTS[-1] or timeline.get('voiceSha256') != digest(prepared / 'voice.wav'):
        raise ValueError('Voce/timeline diverse dalla versione KORA esaminata')
    if timeline.get('mixSha256') != digest(prepared / 'mix' / 'MIX.wav'):
        raise ValueError('Il mix è stato modificato dalla preparazione')
    if timeline.get('scriptSha256') != digest(reel / 'script.txt'):
        raise ValueError('Il copione è stato modificato')
    expected = [0, 308, 565, 884, 1147, 1306]
    if [s['startFrame'] for s in timeline.get('scenes', [])] != expected or \
       [e.get('frame') for e in director.get('events', [])] != expected:
        raise ValueError('Prima applica la correzione KORA precedente o verifica la timeline')
    if any(e.get('audio') for e in director['events']):
        raise ValueError('Il progetto contiene SFX: richiede un controllo dedicato prima di questa bozza')
    candidates = [i for i in range(1, len(captions) - 1)
        if captions[i]['text'].lower() == 'è' and captions[i-1]['text'].lower() == 'luce'
        and captions[i+1]['text'].lower() == 'più' and 5700 <= captions[i]['startMs'] <= 6100]
    if len(candidates) != 1:
        raise ValueError('Impossibile individuare in sicurezza la parola extra dopo "luce"')
    del captions[candidates[0]]  # User confirmed the spoken phrase has no "è".
    return timeline, captions


def bg_for_logo(path):
    # A contrast heuristic, not a substitute for inspecting the final result.
    with Image.open(path) as logo:
        rgba = logo.convert('RGBA')
        rgba.thumbnail((200, 200))
        pixels = [p for p in rgba.getdata() if p[3] > 48]
        if not pixels:
            raise ValueError('Il logo risulta completamente trasparente')
        luminance = sum((p[0]*0.2126 + p[1]*0.7152 + p[2]*0.0722) for p in pixels) / len(pixels)
        return '#f6f1e7' if luminance < 125 else '#0b2830'


def preflight(reel, folder):
    timeline, captions = load_prepared(reel)
    logo, photos = choose_assets(folder)
    return timeline, captions, logo, photos


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dir', type=Path, required=True)
    parser.add_argument('--photos', type=Path, required=True)
    parser.add_argument('--render', action='store_true', help='Esporta una bozza MP4; può richiedere molto tempo')
    args = parser.parse_args()
    reel = args.dir.resolve()
    timeline, captions, logo, photos = preflight(reel, args.photos)
    print('File verificati. Voce: %.1f s; logo: 2 s iniziali e 2 s finali; totale: %.1f s.' %
          (timeline['durationInFrames']/30, (timeline['durationInFrames']+INTRO+OUTRO)/30))
    print('Le immagini con ChatGPT nel nome potrebbero essere generate: verificare contenuto e provenienza.')
    print('La parola extra dopo luce viene rimossa solo nelle caption della bozza, non nell’audio.')
    print('Nessun SFX aggiunto. Questi sono i file scelti:')
    for i, photo in enumerate(photos, 1):
        print('  %d. %s' % (i, photo.name))
    print('Logo:', logo.name, flush=True)
    if not args.render:
        print('Controllo completato: nessun video creato. Usa --render per creare una bozza.')
        return
    remotion = PROJECT / 'node_modules' / '.bin' / 'remotion'
    if not remotion.is_file():
        raise ValueError('Dipendenze Remotion non trovate: esegui npm ci in GONDAR_FINAL')
    ffmpeg, ffprobe = st.tool(st.config(), 'ffmpeg'), st.tool(st.config(), 'ffprobe')
    output = reel / 'output-kora-foto'
    if output.exists():
        raise ValueError('output-kora-foto esiste già: non sovrascrivo il lavoro precedente')
    staging = PROJECT / 'public' / 'kora-foto' / uuid.uuid4().hex
    output.mkdir()
    staging.mkdir(parents=True)
    try:
        with Image.open(logo) as image:
            ImageOps.exif_transpose(image).convert('RGBA').save(staging / 'logo.png')
        staged_photos = []
        for i, file in enumerate(photos):
            target = staging / ('foto-%02d.jpg' % (i + 1))
            with Image.open(file) as image:
                image = ImageOps.exif_transpose(image).convert('RGB')
                image.thumbnail((2160, 2160), Image.Resampling.LANCZOS)
                image.save(target, quality=90)
            duration = min(CUTS[-1] - CUTS[i], CUTS[i + 1] - CUTS[i] + (12 if i < 7 else 0))
            staged_photos.append({'src': target.relative_to(PROJECT / 'public').as_posix(), 'from': CUTS[i], 'duration': duration})
        shutil.copy2(reel / 'prepared' / 'mix' / 'MIX.wav', staging / 'mix.wav')
        props = {'durationInFrames': CUTS[-1] + INTRO + OUTRO, 'voiceFrames': CUTS[-1],
                 'introFrames': INTRO, 'outroFrames': OUTRO,
                 'logo': (staging/'logo.png').relative_to(PROJECT/'public').as_posix(),
                 'logoBackground': bg_for_logo(logo), 'photos': staged_photos,
                 'audio': (staging/'mix.wav').relative_to(PROJECT/'public').as_posix(), 'captions': captions}
        props_file = output / 'props.json'
        st.write_json(props_file, props)
        cmd = [str(remotion), 'render', str(PROJECT/'src'/'index.ts'), 'KoraReel', str(output/'bozza-kora.mp4'),
               '--props', str(props_file), '--concurrency=1', '--codec=h264', '--audio-codec=aac']
        if os.environ.get('REMOTION_BROWSER_EXECUTABLE'):
            cmd += ['--browser-executable', os.environ['REMOTION_BROWSER_EXECUTABLE']]
        subprocess.run(cmd, cwd=PROJECT, check=True)
        video = output/'bozza-kora.mp4'
        metadata = json.loads(subprocess.check_output([ffprobe, '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(video)]))
        measured = subprocess.run([ffmpeg, '-hide_banner', '-i', str(video), '-af',
            'loudnorm=I=-16:TP=-1.8:LRA=11:print_format=json', '-f', 'null', os.devnull],
            capture_output=True, text=True, check=True).stderr
        loudness = json.loads(measured[measured.rfind('{'):measured.rfind('}')+1])
        st.write_json(output/'verifica.json', {'metadata': metadata, 'loudness': loudness,
            'logo': {'file': logo.name, 'sha256': digest(logo)},
            'immagini': [{'file': p.name, 'sha256': digest(p)} for p in photos],
            'note': ['Bozza da controllare: parole, sincronizzazione, immagini, logo, diritti e orari.',
                     'Le immagini ChatGPT potrebbero non essere fotografie autentiche del locale.',
                     'Niente musica né SFX: non ancora equivalente al preset originale V5.',
                     'I file statici temporanei sono stati cancellati: props.json non è riutilizzabile.']})
        print('BOZZA creata:', video)
        print('Verifica anche:', output/'verifica.json')
    finally:
        shutil.rmtree(staging, ignore_errors=True)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        sys.exit('ERRORE: ' + str(error))
