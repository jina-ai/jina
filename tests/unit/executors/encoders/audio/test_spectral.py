import numpy as np

from jina.hub.encoders.audio.spectral import MFCCTimbreEncoder, ChromaPitchEncoder
from tests import JinaTestCase


class SpectralTestCase(JinaTestCase):
    def test_mfcc_encoder(self):
        batch_size = 10
        n_frames = 5
        signal_length = 500 * n_frames
        test_data = np.random.randn(batch_size, signal_length)
        n_mfcc = 12
        encoder = MFCCTimbreEncoder(n_mfcc=n_mfcc)
        encoded_data = encoder.encode(test_data)
        assert encoded_data.shape == (batch_size, n_mfcc * n_frames)

    def test_chroma_encoder(self):
        batch_size = 10
        n_frames = 5
        signal_length = 500 * n_frames
        test_data = np.random.randn(batch_size, signal_length)
        encoder = ChromaPitchEncoder()
        encoded_data = encoder.encode(test_data)
        assert encoded_data.shape == (batch_size, 12 * n_frames)
