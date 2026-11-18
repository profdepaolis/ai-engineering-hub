import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pipeline


class PipelineTests(unittest.TestCase):
    def test_split_limits_scene_count_without_losing_text(self):
        chunks = pipeline.split_script('Uno. Due. Tre. Quattro. Cinque. Sei. Sette.')
        self.assertEqual(len(chunks), 6)
        self.assertEqual(' '.join(chunks), 'Uno. Due. Tre. Quattro. Cinque. Sei. Sette.')
        with self.assertRaises(ValueError):
            pipeline.split_script(' ')

    def test_init_creates_named_clips_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            text = root / 'text.txt'
            text.write_text('Prima frase. Seconda frase.', encoding='utf8')
            target = root / 'reel'
            pipeline.init(text, target, 'Il Salento')
            data = json.loads((target / 'scenes.json').read_text())
            self.assertEqual([s['clip'] for s in data['scenes']], ['clip-01.mp4', 'clip-02.mp4'])
            self.assertTrue((target / 'prompts.md').is_file())
            with self.assertRaises(ValueError):
                pipeline.init(text, target, 'Il Salento')

    def test_captions_are_checked(self):
        pipeline.validate_captions([{'text': 'Ciao', 'startMs': 0, 'endMs': 100}], 1)
        for invalid in ([], [{'text': '', 'startMs': 0, 'endMs': 100}],
                        [{'text': 'x', 'startMs': 2, 'endMs': 2}],
                        [{'text': 'x', 'startMs': 0, 'endMs': 2000}]):
            with self.assertRaises(ValueError):
                pipeline.validate_captions(invalid, 1)

    def test_elevenlabs_is_explicit_and_requires_credentials(self):
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ValueError):
                pipeline.elevenlabs('text', Path('/not-created.mp3'), '', 'eleven_multilingual_v2')

    def test_render_requires_review_before_any_io(self):
        with self.assertRaisesRegex(ValueError, 'controlla'):
            pipeline.render(Path('nonexistent-project'), False, False)


if __name__ == '__main__':
    unittest.main()
