"""Genera parlato Edge TTS e lo converte in WAV PCM tramite ffmpeg.

Edge TTS usa un servizio online Microsoft; le sue condizioni possono cambiare.
La scelta della voce e la verifica dei diritti sono responsabilità dell'utente.
"""
import argparse
import asyncio
import shutil
import subprocess
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--script', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='Nuovo file .wav')
    parser.add_argument('--voice', default='it-IT-ElsaNeural')
    parser.add_argument('--rate', default='+0%')
    args = parser.parse_args()
    text = args.script.read_text(encoding='utf-8').strip()
    if not text:
        raise SystemExit('ERROR: script vuoto')
    if args.output.suffix.lower() != '.wav':
        raise SystemExit('ERROR: --output deve terminare in .wav')
    if args.output.exists():
        raise SystemExit('ERROR: il file di uscita esiste già; scegline uno nuovo')
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        raise SystemExit('ERROR: ffmpeg non trovato. Installa con brew install ffmpeg')
    try:
        import edge_tts
    except ImportError:
        raise SystemExit('ERROR: installa edge-tts nel venv con pip install edge-tts')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        mp3 = Path(tmp) / 'voice.mp3'
        async def synthesize():
            await edge_tts.Communicate(text, args.voice, rate=args.rate).save(str(mp3))
        asyncio.run(synthesize())
        subprocess.run([ffmpeg, '-v', 'error', '-i', str(mp3), '-ar', '48000', '-ac', '2',
                        '-c:a', 'pcm_s24le', '-n', str(args.output)], check=True)
    print(f'Voce generata: {args.output} ({args.voice})')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
