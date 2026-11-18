import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image
import kora_foto as k


class KoraTest(unittest.TestCase):
    def test_assets_and_logo(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for name in ([' LOGO KORA.PNG', 'colazione 1.png', 'Aperitivo al tramonto.png'] +
                         ['Immagine ChatGPT %d.png' % i for i in range(6)]):
                Image.new('RGB', (10, 10), 'navy').save(root / name)
            logo, photos = k.choose_assets(root)
            self.assertEqual(len(photos), 8)
            self.assertEqual(photos[3].name, 'colazione 1.png')
            self.assertIn('Aperitivo', photos[4].name)
            self.assertEqual(k.bg_for_logo(logo), '#f6f1e7')
            Image.new('RGB', (10, 10), 'black').save(root / 'logo kora-2.png')
            with self.assertRaises(ValueError):
                k.choose_assets(root)

    def test_caption_fix_and_validation_without_touching_voice(self):
        with tempfile.TemporaryDirectory() as d:
            reel = Path(d)
            work = reel / 'prepared'
            (work / 'mix').mkdir(parents=True)
            (work / 'voice.wav').write_bytes(b'voice')
            (work / 'mix' / 'MIX.wav').write_bytes(b'mix')
            (reel / 'script.txt').write_bytes(b'script')
            sha = lambda b: hashlib.sha256(b).hexdigest()
            frames = [0, 308, 565, 884, 1147, 1306]
            timeline = {'durationInFrames': 1478, 'voiceSha256': sha(b'voice'), 'mixSha256': sha(b'mix'),
                        'scriptSha256': sha(b'script'), 'scenes': [{'startFrame': x} for x in frames]}
            captions = [{'text': 'luce', 'startMs': 5520, 'endMs': 5760},
                        {'text': 'è', 'startMs': 5760, 'endMs': 5960},
                        {'text': 'più', 'startMs': 5960, 'endMs': 6160}]
            (work / 'timeline.json').write_text(json.dumps(timeline))
            (work / 'captions.json').write_text(json.dumps(captions, ensure_ascii=False))
            (work / 'director.json').write_text(json.dumps({'events': [{'frame': x} for x in frames]}))
            _, fixed = k.load_prepared(reel)
            self.assertEqual([x['text'] for x in fixed], ['luce', 'più'])
            self.assertEqual(json.loads((work / 'captions.json').read_text()), captions)
            self.assertEqual((work / 'voice.wav').read_bytes(), b'voice')
            (work / 'voice.wav').write_bytes(b'changed')
            with self.assertRaises(ValueError):
                k.load_prepared(reel)


if __name__ == '__main__':
    unittest.main()
