__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Dict

import numpy as np

from .. import BaseCrafter


class AudioMonophoner(BaseCrafter):
    """
    :class:`AudioMonophoner` makes the audio signal monophonic on doc-level.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def craft(self, blob: np.ndarray, *args, **kwargs) -> Dict:
        """
        Reads the `ndarray` of the audio signal, makes the audio signal monophonic and saves the `ndarray` of the
        monophonic signal in the `blob` of the Document.

        :param blob: the ndarray of the audio signal
        :return: a Document dict with the monophonic audio signal
        """
        import librosa
        signal_mono = librosa.to_mono(blob)

        return dict(offset=0, weight=1., blob=signal_mono)
