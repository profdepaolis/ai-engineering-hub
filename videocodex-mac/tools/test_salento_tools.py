import copy
import json
import tempfile
import unittest
from pathlib import Path

import salento_tools as st


class CompileCueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.library = self.root / 'audio'
        self.library.mkdir()
        self.asset = self.library / 'click.wav'
        self.asset.write_bytes(b'test audio contents')
        self.catalog = self.root / 'catalog.json'
        self.entry = {'path': 'click.wav', 'status': 'AVAILABLE', 'sha256': st.digest(self.asset),
                      'licenseStatus': 'USER_CONFIRMED', 'commercialUse': 'AUTHORIZED',
                      'durationSeconds': 0.2}
        self.save_catalog()
        self.c = {'_paths': {'audioLibrary': self.library, 'audioCatalog': self.catalog},
                  'requiredComponents': ['TypingTitle']}
        self.manifest = {'fps': 30, 'durationInFrames': 90, 'events': [
            {'id': 'click-1', 'frame': 30, 'component': 'TypingTitle', 'phase': 'character',
             'sound': {'path': 'click.wav', 'sourcePeakMs': 50, 'peakDbFS': -12,
                       'maxDurationSeconds': 0.2}}]}

    def tearDown(self):
        self.temp.cleanup()

    def save_catalog(self):
        self.catalog.write_text(json.dumps({'assets': [self.entry]}))

    def test_sample_alignment(self):
        out = st.compile_cues(self.c, self.manifest)
        sound = out['events'][0]['audio']
        self.assertEqual(sound['targetSample'], 48000)
        self.assertEqual(sound['startSample'] + sound['peakSample'], 48000)
        self.assertEqual(out['keyframes']['click-1'], 30)

    def test_rights_hash_and_path_rejected(self):
        self.entry['licenseStatus'] = 'UNKNOWN'
        self.save_catalog()
        with self.assertRaises(ValueError):
            st.compile_cues(self.c, self.manifest)
        self.entry['licenseStatus'] = 'USER_CONFIRMED'
        self.entry['sha256'] = None
        self.save_catalog()
        with self.assertRaises(ValueError):
            st.compile_cues(self.c, self.manifest)
        self.entry['sha256'] = '0' * 64
        self.save_catalog()
        with self.assertRaises(ValueError):
            st.compile_cues(self.c, self.manifest)
        with self.assertRaises(ValueError):
            st.safe_audio(self.c, '../catalog.json')

    def test_frame_and_output_guards(self):
        manifest = copy.deepcopy(self.manifest)
        manifest['events'][0]['frame'] = 90
        with self.assertRaises(ValueError):
            st.compile_cues(self.c, manifest)
        output = self.root / 'director.json'
        st.compile_cues(self.c, self.manifest, output)
        with self.assertRaises(ValueError):
            st.compile_cues(self.c, self.manifest, output)
        with self.assertRaises(ValueError):
            st.compile_cues(self.c, self.manifest, self.catalog, True)


if __name__ == '__main__':
    unittest.main()
