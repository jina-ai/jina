import unittest

from jina.executors.crafters.audio.io import AudioReader
from tests import JinaTestCase


class MyTestCase(JinaTestCase):
    def test_io(self):
        import librosa
        audio_file_path = librosa.util.example_audio_file()

        crafter = AudioReader()
        crafted_doc = crafter.craft(audio_file_path, 0)

        signal = crafted_doc['blob']
        self.assertEqual(signal.shape, (2, 1355168))


if __name__ == '__main__':
    unittest.main()
