"""Allinea la voce parola per parola con faster-whisper (locale, gratuito).

Uso:
    python3 tools/align_whisper.py --audio reels/<reel>/voice.wav --output reels/<reel>/captions.json

Installazione: pip3 install faster-whisper
Il modello 'small' è un buon compromesso qualità/velocità su Mac (Apple Silicon ok).
Output: lista di {"text", "startMs", "endMs"} pronta per KineticCaption.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audio', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--model', default='small')
    parser.add_argument('--language', default='it')
    args = parser.parse_args()

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise SystemExit('ERROR: faster-whisper non trovato. Installalo con: pip3 install faster-whisper')

    model = WhisperModel(args.model, device='cpu', compute_type='int8')
    segments, _info = model.transcribe(str(args.audio), language=args.language, word_timestamps=True)

    captions = []
    for segment in segments:
        for word in segment.words or []:
            text = word.word.strip()
            if not text:
                continue
            captions.append({
                'text': text,
                'startMs': round(word.start * 1000),
                'endMs': round(word.end * 1000),
            })

    if not captions:
        raise SystemExit('ERROR: nessuna parola rilevata nella voce')

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(captions, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Caption generate: {len(captions)} parole -> {args.output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
