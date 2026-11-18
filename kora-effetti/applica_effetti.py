#!/usr/bin/env python3
"""Crea una prova KORA separata: video copiato, audio rimissato, nessuna musica."""
import json, os, subprocess, sys
from pathlib import Path

BASE = Path.home() / 'Desktop' / 'SKILL FRANCESCO' / 'PRODUZIONE_VIDEO' / 'videocodex-mac' / 'reels' / 'kora'
SOURCE = BASE / 'output-kora-foto' / 'bozza-kora.mp4'
OUT = BASE / 'output-kora-effetti'
SFX = Path(__file__).resolve().parent / 'swipe-soft.mp3'
# Mezzo delle dissolvenze fra le fotografie, in frame di un video a 30 fps.
FRAMES = [60 + f + 6 for f in (308, 565, 686, 744, 884, 1147, 1306)]


def call(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def main():
    if not SOURCE.is_file() or not SFX.is_file():
        raise ValueError('Bozza o file effetto non trovato. Verifica i percorsi.')
    info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(SOURCE)]))
    streams = info['streams']
    videos = [s for s in streams if s['codec_type'] == 'video']
    audios = [s for s in streams if s['codec_type'] == 'audio']
    duration = float(info['format']['duration'])
    if len(videos) != 1 or len(audios) != 1 or videos[0].get('r_frame_rate') != '30/1' or abs(duration - 53.27) > .2:
        raise ValueError('La bozza non corrisponde alla durata e al formato KORA previsti: mi fermo.')
    OUT.mkdir()  # Never reuse an existing directory.
    stem = OUT / 'SFX.wav'
    video = OUT / 'bozza-kora-effetti.mp4'
    cuts = [round(frame * 1000 / 30) for frame in FRAMES]
    parts = ['[1:a]volume=0.08,asplit=7' + ''.join('[s%d]' % i for i in range(7))]
    for i, t in enumerate(cuts):
        parts.append('[s%d]adelay=%d:all=1[d%d]' % (i, t, i))
    parts.append('[0:a]' + ''.join('[d%d]' % i for i in range(7)) + 'amix=inputs=8:duration=first:normalize=0[m]')
    print('Creo la traccia effetti separata...', flush=True)
    call(['ffmpeg','-hide_banner','-loglevel','error','-n','-f','lavfi','-i',
          'anullsrc=r=48000:cl=stereo:d=%.6f' % duration,'-i',str(SFX),'-filter_complex',';'.join(parts),
          '-map','[m]','-c:a','pcm_s16le',str(stem)])
    print('Creo la nuova bozza (il video originale non viene modificato)...', flush=True)
    call(['ffmpeg','-hide_banner','-loglevel','error','-n','-i',str(SOURCE),'-i',str(stem),
          '-filter_complex','[0:a]volume=-1dB[v];[v][1:a]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.75:level=0:latency=1[a]',
          '-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',str(video)])
    measure = subprocess.run(['ffmpeg','-hide_banner','-i',str(video),'-af','loudnorm=I=-16:TP=-1.8:LRA=11:print_format=json','-f','null',os.devnull], capture_output=True,text=True,check=True).stderr
    loudness = json.loads(measure[measure.rfind('{'):measure.rfind('}')+1])
    (OUT / 'verifica.json').write_text(json.dumps({'sorgente':str(SOURCE),'effetto':'UISFX soft/swipe.mp3, CC0 1.0', 'posizioni_inizio_ms':cuts, 'guadagno_effetto_db':-21.94,'guadagno_voce_db':-1, 'note':'Limiter sul mix; audio AAC ricodificato. Ascoltare e controllare la sincronizzazione.', 'loudness':loudness},ensure_ascii=False,indent=2),encoding='utf-8')
    print('\nFATTO. Nuova bozza:', video)
    print('Traccia effetti separata:', stem)
    print('Misure LUFS / dBTP:',loudness['input_i'],loudness['input_tp'])
    print('Ascolta e confronta con la bozza precedente prima di pubblicare.')

if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        sys.exit('ERRORE: %s\nSe esiste già output-kora-effetti non viene sovrascritta. Chiedi assistenza.' % exc)
