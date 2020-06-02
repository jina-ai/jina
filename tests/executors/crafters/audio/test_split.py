import unittest

import numpy as np
from jina.executors.crafters.audio.split import AudioSlicer, SlidingWindowAudioSlicer
from tests import JinaTestCase


class MyTestCase(JinaTestCase):
    def test_segment_mono(self):
        n_frames = 100
        frame_length = 2048
        signal_orig = np.random.randn(frame_length * n_frames)

        crafter = AudioSlicer(frame_length)
        crafted_chunks = crafter.craft(signal_orig, 0)

        self.assertEqual(len(crafted_chunks), n_frames)

    def test_segment_stereo(self):
        n_frames = 100
        frame_length = 2048
        signal_orig = np.random.randn(2, frame_length * n_frames)

        crafter = AudioSlicer(frame_length)
        crafted_chunks = crafter.craft(signal_orig, 0)

        self.assertEqual(len(crafted_chunks), n_frames * 2)

    def test_sliding_window_mono(self):
        n_frames = 100
        frame_length = 2048
        signal_orig = np.random.randn(frame_length * n_frames)

        crafter = SlidingWindowAudioSlicer(frame_length, frame_length//2)
        crafted_chunks = crafter.craft(signal_orig, 0)

        self.assertEqual(len(crafted_chunks), n_frames * 2 - 1)

    def test_sliding_window_stereo(self):
        n_frames = 100
        frame_length = 2048
        signal_orig = np.random.randn(2, frame_length * n_frames)

        crafter = SlidingWindowAudioSlicer(frame_length, frame_length//2)
        crafted_chunks = crafter.craft(signal_orig, 0)

        self.assertEqual(len(crafted_chunks), (n_frames * 2 - 1) * 2)


if __name__ == '__main__':
    unittest.main()
