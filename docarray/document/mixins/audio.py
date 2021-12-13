import wave
from typing import Union, BinaryIO

import numpy as np

from ...helper import T, deprecate_by


class AudioDataMixin:
    """Provide helper functions for :class:`Document` to support audio data. """

    def dump_audio_blob_to_file(
        self: T,
        file: Union[str, BinaryIO],
        sample_rate: int = 44100,
        sample_width: int = 2,
    ) -> T:
        """Save :attr:`.blob` into an wav file. Mono/stereo is preserved.

        :param file: if file is a string, open the file by that name, otherwise treat it as a file-like object.
        :param sample_rate: sampling frequency
        :param sample_width: sample width in bytes

        :return: Document itself after processed
        """
        # Convert to (little-endian) 16 bit integers.
        max_int16 = 2 ** 15
        blob = (self.blob * max_int16).astype('<h')
        n_channels = 2 if self.blob.ndim > 1 else 1

        with wave.open(file, 'w') as f:
            # 2 Channels.
            f.setnchannels(n_channels)
            # 2 bytes per sample.
            f.setsampwidth(sample_width)
            f.setframerate(sample_rate)
            f.writeframes(blob.tobytes())
        return self

    def load_uri_to_audio_blob(self: T) -> T:
        """Convert an audio :attr:`.uri` into :attr:`.blob` inplace

        :return: Document itself after processed
        """
        ifile = wave.open(
            self.uri
        )  #: note wave is Python built-in module https://docs.python.org/3/library/wave.html
        samples = ifile.getnframes()
        audio = ifile.readframes(samples)

        # Convert buffer to float32 using NumPy
        audio_as_np_int16 = np.frombuffer(audio, dtype=np.int16)
        audio_as_np_float32 = audio_as_np_int16.astype(np.float32)

        # Normalise float32 array so that values are between -1.0 and +1.0
        max_int16 = 2 ** 15
        audio_normalised = audio_as_np_float32 / max_int16

        channels = ifile.getnchannels()
        if channels == 2:
            # 1 for mono, 2 for stereo
            audio_stereo = np.empty((int(len(audio_normalised) / channels), channels))
            audio_stereo[:, 0] = audio_normalised[range(0, len(audio_normalised), 2)]
            audio_stereo[:, 1] = audio_normalised[range(1, len(audio_normalised), 2)]

            self.blob = audio_stereo
        else:
            self.blob = audio_normalised
        return self

    convert_uri_to_audio_blob = deprecate_by(load_uri_to_audio_blob)
