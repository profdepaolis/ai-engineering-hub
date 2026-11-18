"""Genera i prompt per Google Flow / Hailuo / Luma da scenes.json.

Il progetto non integra API video: la generazione clip resta manuale nel browser.
Questo script prepara un file prompts.md con un prompt pronto per ogni scena,
con stile coerente e formato verticale 9:16.

Uso:
    python3 tools/make_flow_prompts.py --scenes reels/<reel>/scenes.json --output reels/<reel>/prompts.md
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

STYLE_BLOCK = (
    'vertical 9:16 video, photorealistic, warm cinematic golden-hour light, '
    'smooth camera movement, no text, no watermark, no logo, '
    'consistent color grade across all clips'
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenes', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()

    data = json.loads(args.scenes.read_text(encoding='utf-8'))
    style = data.get('style', STYLE_BLOCK)
    lines = [
        f"# Prompt clip — {data.get('reel', 'reel')}",
        '',
        f"Tema: {data.get('theme', '')}",
        '',
        'Genera ogni clip in **Google Flow** (o Hailuo/Luma come riserva), formato verticale 9:16,',
        'poi scarica i file in `clips/` con i nomi indicati. Le clip AI sono solo supporto visivo:',
        'non presentarle mai come riprese autentiche di luoghi reali.',
        '',
    ]
    for i, scene in enumerate(data.get('scenes', []), 1):
        lines.append(f"## {i}. {scene.get('id')} ({scene.get('component')})")
        lines.append(f"Frame {scene.get('startFrame')}–{scene.get('endFrame')}")
        lines.append(f"Nome suggerito per la clip: `clips/{scene.get('id', i)}.mp4`")
        lines.append('')
        lines.append('**Prompt:**')
        lines.append('')
        lines.append(f"> {scene.get('clipPrompt', '')}, {style}")
        lines.append('')
        if scene.get('photos'):
            lines.append(f"Foto attese: {', '.join(scene['photos'])}")
        if scene.get('text'):
            lines.append(f"Testo a schermo (aggiunto in montaggio, NON nella clip): “{scene['text']}”")
        if scene.get('notes'):
            lines.append(f"Note regia: {scene['notes']}")
        lines.append('')

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text('\n'.join(lines), encoding='utf-8')
    print(f'Prompt generati: {len(data.get("scenes", []))} scene -> {args.output}')
    print('Apri Google Flow nel browser, incolla ogni prompt, genera e scarica in clips/.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
