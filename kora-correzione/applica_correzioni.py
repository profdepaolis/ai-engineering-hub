"""Correzione specifica del progetto KORA. Non modifica o rigenera audio."""
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

EXPECTED_CAPTIONS = '3d3fdcd2c15bf68bc253d7c0f767ec20'
EXPECTED_TIMELINE = 'b510b700c14c836de8c816aa56926d8f'
BOUNDARIES = [0, 308, 565, 884, 1147, 1306, 1478]
MARKERS = ['Al KORA,', 'Tutti i giorni,', "Ma c'è qualcosa", 'Non possiamo svelarvi tutto.', 'Chiamateci o scriveteci']
PROMPTS = [
    'Slow cinematic close-up of gentle sea waves and reflections in soft natural light, calm coastal mood, vertical 9:16, no text, no logo.',
    'Evocative slow shot of a quiet seafront and soft waves in warm daylight, peaceful year-round atmosphere, vertical 9:16, no text, no logo.',
    'Close-up of a simple breakfast or an aperitivo on a table by the sea, warm natural light, slow camera movement, vertical 9:16, no text, no logo.',
    'Atmospheric close-up of sunlight shimmering over quiet sea water, subtle sense of anticipation, slow elegant camera movement, vertical 9:16, no text, no logo.',
    'Gentle detail of the sea seen through soft sunlight, suggestive and mysterious without showing or promising a specific event, vertical 9:16, no text, no logo.',
    'Slow wide shot of a calm sea horizon at soft golden light, inviting and serene, vertical 9:16, no text, no logo.'
]


def md5(path):
    return hashlib.md5(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf8'))


def correct_captions(items):
    out = []
    stats = {'apostrofi': 0, 'silenziose': 0, 'al_kora': 0, 'finale': 0, 'scriveteci': 0, 'orario': 0, 'acquista': 0}
    i = 0
    while i < len(items):
        cur = dict(items[i])
        text = cur['text']
        if text.lower() == 'c' and i + 1 < len(items) and items[i + 1]['text'].lower() in ("'è", '’è'):
            cur['text'] = "C'è" if not out else "c'è"
            cur['endMs'] = items[i + 1]['endMs']
            stats['apostrofi'] += 1
            i += 2
        elif text.lower() == 'silenciose,':
            cur['text'] = 'silenziose.'
            stats['silenziose'] += 1
            i += 1
        elif text.lower() == 'alcora':
            a, b = cur['startMs'], cur['endMs']
            mid = a + max(1, round((b - a) * 2 / 6))
            out.append({'text': 'Al', 'startMs': a, 'endMs': mid})
            cur = {'text': 'KORA,', 'startMs': mid, 'endMs': b}
            stats['al_kora'] += 1
            i += 1
        elif text.lower() == 'oscriveteci':
            a, b = cur['startMs'], cur['endMs']
            mid = a + max(1, round((b - a) / 11))
            out.append({'text': 'o', 'startMs': a, 'endMs': mid})
            cur = {'text': 'scriveteci', 'startMs': mid, 'endMs': b}
            stats['scriveteci'] += 1
            i += 1
        elif text.lower() == 'cora,':
            cur['text'] = 'KORA.'
            stats['finale'] += 1
            i += 1
        elif text == '17,':
            cur['text'] = 'diciassette.'
            stats['orario'] += 1
            i += 1
        elif text == 'a' and out and out[-1]['text'].lower() == 'acquista' and i + 1 < len(items) and items[i + 1]['text'].lower() == 'un':
            # The extra ASR token is likely a misrecognition. Keep its interval in "un".
            cur = dict(items[i + 1])
            cur['startMs'] = items[i]['startMs']
            stats['acquista'] += 1
            i += 2
        else:
            i += 1
        out.append(cur)
    wanted = {'apostrofi': 2, 'silenziose': 1, 'al_kora': 1, 'finale': 1, 'scriveteci': 1, 'orario': 1, 'acquista': 1}
    if stats != wanted:
        raise ValueError('Trascrizione diversa da quella esaminata: non applico modifiche. Dettagli: ' + str(stats))
    last = -1
    for word in out:
        if word['startMs'] < last or word['endMs'] <= word['startMs']:
            raise ValueError('Tempi delle caption non validi')
        last = word['startMs']
    return out


def apply(project):
    project = project.resolve()
    work = project / 'prepared'
    paths = {'captions': work / 'captions.json', 'timeline': work / 'timeline.json',
             'director': work / 'director.json', 'manifest': work / 'cues.manifest.json',
             'scenes': project / 'scenes.json', 'prompts': project / 'prompts.md'}
    if md5(paths['captions']) != EXPECTED_CAPTIONS or md5(paths['timeline']) != EXPECTED_TIMELINE:
        raise ValueError('I file non coincidono con quelli esaminati su Drive; nessuna modifica effettuata')
    caps, timeline, director, manifest, scenes = [load(paths[n]) for n in ('captions', 'timeline', 'director', 'manifest', 'scenes')]
    if timeline['durationInFrames'] != BOUNDARIES[-1] or len(timeline['scenes']) != 6:
        raise ValueError('Timeline imprevista')
    if hashlib.sha256((project / 'script.txt').read_bytes()).hexdigest() != timeline['scriptSha256']:
        raise ValueError('Il copione è stato modificato dopo la preparazione')
    if hashlib.sha256((work / 'voice.wav').read_bytes()).hexdigest() != timeline['voiceSha256']:
        raise ValueError('La voce è diversa da quella preparata')
    if hashlib.sha256((work / 'mix' / 'MIX.wav').read_bytes()).hexdigest() != timeline['mixSha256']:
        raise ValueError('Il mix è stato modificato')
    ids = ['scene-%02d' % (i + 1) for i in range(6)]
    for data in (director, manifest):
        if [e['id'] for e in data['events']] != ids or any(e.get('audio') or e.get('sound') for e in data['events']):
            raise ValueError('I cue sono diversi o contengono SFX: ricalcolo audio richiesto')
    if [s.get('cueId') for s in timeline['scenes']] != ids:
        raise ValueError('Cue della timeline non riconosciuti')
    corrected = correct_captions(caps)
    for i, ident in enumerate(ids):
        timeline['scenes'][i]['startFrame'] = BOUNDARIES[i]
        timeline['scenes'][i]['durationInFrames'] = BOUNDARIES[i + 1] - BOUNDARIES[i]
        director['events'][i]['frame'] = BOUNDARIES[i]
        director['keyframes'][ident] = BOUNDARIES[i]
        manifest['events'][i]['frame'] = BOUNDARIES[i]
    text = (project / 'script.txt').read_text(encoding='utf8').strip()
    indexes = [0]
    for marker in MARKERS:
        position = text.find(marker, indexes[-1] + 1)
        if position < 0:
            raise ValueError('Marcatore nel copione non trovato: ' + marker)
        indexes.append(position)
    indexes.append(len(text))
    chunks = [text[indexes[i]:indexes[i + 1]].strip() for i in range(6)]
    if ' '.join(' '.join(chunks).split()) != ' '.join(text.split()):
        raise ValueError('Segmentazione del copione non valida')
    scenes['scenes'] = [{'text': chunks[i], 'clip': 'clip-%02d.mp4' % (i + 1), 'prompt': PROMPTS[i]} for i in range(6)]
    lines = ['# KORA — sei clip, bozza di prompt', '',
        'Clip AI generiche: non presentarle come riprese reali del locale o di un luogo specifico.',
        'Preferire video originali di KORA se disponibili e autorizzati. Verifica sempre licenze e contenuto.',
        'Le clip più corte della scena si ripetono: meglio preparare tagli vari o più lunghi.', '']
    for i in range(6):
        lines += ['## Scena %d — clip-%02d.mp4 — %.1f secondi' % (i + 1, i + 1, (BOUNDARIES[i + 1] - BOUNDARIES[i]) / 30),
                  '', 'Testo voce: ' + chunks[i], '', 'Prompt (modificabile): ' + PROMPTS[i], '']
    payloads = {'captions': corrected, 'timeline': timeline, 'director': director, 'manifest': manifest, 'scenes': scenes}
    outputs = {name: json.dumps(value, ensure_ascii=False, indent=2) + '\n' for name, value in payloads.items()}
    outputs['prompts'] = '\n'.join(lines)
    backup = project / 'backup-prima-correzione-kora'
    if backup.exists():
        raise ValueError('Il backup esiste già: correzione forse già applicata. Non sovrascrivo nulla.')
    backup.mkdir()
    for name, path in paths.items():
        shutil.copy2(path, backup / path.name)
    written = []
    try:
        for name, content in outputs.items():
            path = paths[name]
            tmp = path.with_name(path.name + '.kora.tmp')
            if tmp.exists():
                raise ValueError('File temporaneo già esistente: ' + str(tmp))
            tmp.write_text(content, encoding='utf8')
            os.replace(tmp, path)
            written.append(name)
    except Exception:
        for name in written:
            shutil.copy2(backup / paths[name].name, paths[name])
        raise
    print('Correzione completata. Voce e mix non sono stati modificati.')
    print('Backup originali:', backup)
    print('Scene:', ', '.join('%.1fs' % ((BOUNDARIES[i + 1] - BOUNDARIES[i]) / 30) for i in range(6)))
    print('Controlla ascoltando: KORA, "la luce è più morbida", "acquista un", e "o scriveteci".')
    print('Leggi i nuovi prompt in:', paths['prompts'])


if __name__ == '__main__':
    try:
        if len(sys.argv) != 2:
            raise ValueError('Indica la cartella del progetto: python applica_correzioni.py reels/kora')
        apply(Path(sys.argv[1]))
    except (ValueError, KeyError, OSError) as error:
        sys.exit('ERRORE: ' + str(error))
