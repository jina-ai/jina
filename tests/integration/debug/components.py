import io
from typing import Tuple, Dict, Union

import numpy as np

from jina.executors.crafters import BaseCrafter
from jina.executors.decorators import single
from jina.importer import ImportExtensions
from .helper import _crop_image, _move_channel_axis, _load_image


class ImageReader(BaseCrafter):
    """
    Load image file and craft it into image matrix.

    :class:`ImageReader` loads the image from the given file
        path and save the `ndarray` of the image in the Document.

    :param channel_axis: the axis id of the color channel.
        The ``-1`` indicates the color channel info at the last axis
    """

    def __init__(self, channel_axis: int = -1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel_axis = channel_axis

    @single(slice_nargs=2)
    def craft(self, buffer: bytes, uri: str, *args, **kwargs) -> Dict:
        """
        Read image file and craft it into image matrix.

        Read the image from the given file path that specified in `buffer` and save the `ndarray` of the image in
            the `blob` of the document.

        :param buffer: the image in raw bytes
        :param uri: the image file path

        """
        with ImportExtensions(
            required=True,
            verbose=True,
            pkg_name='Pillow',
            logger=self.logger,
            help_text='PIL is missing. Install it with `pip install Pillow`',
        ):
            from PIL import Image

            if buffer:
                raw_img = Image.open(io.BytesIO(buffer))
            elif uri:
                raw_img = Image.open(uri)
            else:
                raise ValueError('no value found in "buffer" and "uri"')
            raw_img = raw_img.convert('RGB')
            img = np.array(raw_img).astype('float32')
            if self.channel_axis != -1:
                img = np.moveaxis(img, -1, self.channel_axis)
            return dict(blob=img)


class CenterImageCropper(BaseCrafter):
    """
    Crop the image with the center crop box.

    The coordinate is the same coordinate-system in the
        :py:mode:`PIL.Image`.

    :param target_size: Desired output size. If size
        is a sequence like (h, w), the output size will
        be matched to this. If size is an int, the
        output will have the same height and width as
        the `target_size`.
    :param channel_axis: Axis for channel
    :param args:  Additional positional arguments
    :param kwargs: Additional keyword arguments
    """

    def __init__(
        self,
        target_size: Union[Tuple[int, int], int] = 224,
        channel_axis: int = -1,
        *args,
        **kwargs
    ):
        """Set Constructor."""
        super().__init__(*args, **kwargs)
        self.target_size = target_size
        self.channel_axis = channel_axis

    @single
    def craft(self, blob: 'np.ndarray', *args, **kwargs) -> Dict:
        """
        Crop the input image array.

        :param blob: The ndarray of the image
        :param args:  Additional positional arguments
        :param kwargs: Additional keyword arguments
        :return: A dict with the cropped image
        """
        raw_img = _load_image(blob, self.channel_axis)
        _img, top, left = _crop_image(raw_img, self.target_size, how='center')
        img = _move_channel_axis(np.asarray(_img), -1, self.channel_axis)
        return dict(offset=0, blob=img.astype('float32'), location=(top, left))
