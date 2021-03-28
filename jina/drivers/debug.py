import os

import numpy as np

from jina.drivers import FlatRecursiveMixin, BaseRecursiveDriver
from jina.importer import ImportExtensions

if False:
    # noinspection PyUnreachableCode
    from jina import DocumentSet


class PngToDiskDriver(FlatRecursiveMixin, BaseRecursiveDriver):
    """A driver that can store an intermediate representation of a png in the workspace, under a given folder.

    Useful for debugging Crafters in the Flow

    :param workspace: the folder where we store the pngs
    :param prefix: the subfolder to add to workspace
    :param top: limit the pngs to first N
    """

    def __init__(self, workspace, prefix='', top=10, *args, **kwargs):
        self.prefix = prefix
        self.top = top
        self.done = 0
        self.workspace = workspace
        self.folder = os.path.join(self.workspace, self.prefix)
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
        super().__init__(*args, **kwargs)

    def _apply_all(
        self,
        docs: 'DocumentSet',
        *args,
        **kwargs,
    ) -> None:
        def _move_channel_axis(
            img: 'np.ndarray', channel_axis_to_move: int, target_channel_axis: int = -1
        ) -> 'np.ndarray':
            if channel_axis_to_move == target_channel_axis:
                return img
            return np.moveaxis(img, channel_axis_to_move, target_channel_axis)

        def _load_image(blob: 'np.ndarray', channel_axis: int):
            with ImportExtensions(
                required=True,
                pkg_name='Pillow',
                verbose=True,
                logger=self.logger,
                help_text='PIL is missing. Install it with `pip install Pillow`',
            ):
                from PIL import Image

                img = _move_channel_axis(blob, channel_axis)
                return Image.fromarray(img.astype('uint8'))

        for d in docs:
            if self.done < self.top:
                img = _load_image(d.blob, -1)
                path = os.path.join(self.folder, f'{self.done}.png')
                img.save(path)
                self.done += 1
