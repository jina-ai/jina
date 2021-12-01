from contextlib import nullcontext
from math import sqrt, ceil, floor
from typing import Optional

import numpy as np

from .... import Document
from ....helper import deprecated_method
from ....logging.profile import ProgressBar


class PlotMixin:
    """Helper functions for plotting the arrays. """

    @deprecated_method(new_function_name='plot_embeddings')
    def visualize(self, *args, **kwargs):
        """Deprecated! Please use :meth:`.plot_embeddings` instead.

        Plot embeddings in a 2D projection with the PCA algorithm. This function requires ``matplotlib`` installed.

        :param args: extra args
        :param kwargs: extra kwargs
        """
        self.plot_embeddings(*args, **kwargs)

    def plot_embeddings(
        self,
        output: Optional[str] = None,
        title: Optional[str] = None,
        colored_attr: Optional[str] = None,
        colormap: str = 'rainbow',
        method: str = 'pca',
        show_axis: bool = False,
        **kwargs,
    ):
        """Plot embeddings in a 2D projection with the PCA algorithm. This function requires ``matplotlib`` installed.

        If `tag_name` is provided the plot uses a distinct color for each unique tag value in the
        documents of the DocumentArray.

        :param output: Optional path to store the visualization. If not given, show in UI
        :param title: Optional title of the plot. When not given, the default title is used.
        :param colored_attr: Optional str that specifies attribute used to color the plot, it supports dunder expression
            such as `tags__label`, `matches__0__id`.
        :param colormap: the colormap string supported by matplotlib.
        :param method: the visualization method, available `pca`, `tsne`. `pca` is fast but may not well represent
                nonlinear relationship of high-dimensional data. `tsne` requires scikit-learn to be installed and is
                much slower.
        :param show_axis: If set, axis and bounding box of the plot will be printed.
        :param kwargs: extra kwargs pass to matplotlib.plot
        """

        x_mat = self.embeddings
        assert isinstance(
            x_mat, np.ndarray
        ), f'Type {type(x_mat)} not currently supported, use np.ndarray embeddings'

        if method == 'tsne':
            from sklearn.manifold import TSNE

            x_mat_2d = TSNE(n_components=2).fit_transform(x_mat)
        else:
            from ....math.dimensionality_reduction import PCA

            x_mat_2d = PCA(n_components=2).fit_transform(x_mat)

        plt_kwargs = {
            'x': x_mat_2d[:, 0],
            'y': x_mat_2d[:, 1],
            'alpha': 0.2,
            'marker': '.',
        }

        import matplotlib.pyplot as plt

        plt.figure(figsize=(8, 8))

        plt.title(title or f'{len(x_mat)} Documents with {method}')

        if colored_attr:
            tags = []

            for x in self:
                try:
                    tags.append(getattr(x, colored_attr))
                except (KeyError, AttributeError, ValueError):
                    tags.append(None)
            tag_to_num = {tag: num for num, tag in enumerate(set(tags))}
            plt_kwargs['c'] = np.array([tag_to_num[ni] for ni in tags])
            plt_kwargs['cmap'] = plt.get_cmap(colormap)

        # update the plt_kwargs
        plt_kwargs.update(kwargs)

        plt.scatter(**plt_kwargs)

        if not show_axis:
            plt.gca().set_axis_off()
            plt.gca().xaxis.set_major_locator(plt.NullLocator())
            plt.gca().yaxis.set_major_locator(plt.NullLocator())

        if output:
            plt.savefig(output, bbox_inches='tight', pad_inches=0.1)
        else:
            plt.show()

    def plot_image_sprites(
        self,
        output: Optional[str] = None,
        canvas_size: int = 512,
        min_size: int = 16,
        channel_axis: int = -1,
    ) -> None:
        """Generate a sprite image for all image blobs in this DocumentArray-like object.

        An image sprite is a collection of images put into a single image. It is always square-sized.
        Each sub-image is also square-sized and equally-sized.

        :param output: Optional path to store the visualization. If not given, show in UI
        :param canvas_size: the size of the canvas
        :param min_size: the minimum size of the image
        :param channel_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis
        """
        if not self:
            raise ValueError(f'{self!r} is empty')

        import matplotlib.pyplot as plt

        img_per_row = ceil(sqrt(len(self)))
        img_size = int(canvas_size / img_per_row)

        if img_size < min_size:
            # image is too small, recompute the size
            img_size = min_size
            img_per_row = int(canvas_size / img_size)

        max_num_img = img_per_row ** 2
        sprite_img = np.zeros(
            [img_size * img_per_row, img_size * img_per_row, 3], dtype='uint8'
        )
        img_id = 0

        for d in self:
            _d = Document(d, copy=True)
            if _d.content_type != 'blob':
                _d.load_uri_to_image_blob()
                channel_axis = -1

            _d.set_image_blob_channel_axis(channel_axis, -1).set_image_blob_shape(
                shape=(img_size, img_size)
            )

            row_id = floor(img_id / img_per_row)
            col_id = img_id % img_per_row
            sprite_img[
                (row_id * img_size) : ((row_id + 1) * img_size),
                (col_id * img_size) : ((col_id + 1) * img_size),
            ] = _d.blob

            img_id += 1
            if img_id >= max_num_img:
                break

        plt.gca().set_axis_off()
        plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
        plt.margins(0, 0)
        plt.gca().xaxis.set_major_locator(plt.NullLocator())
        plt.gca().yaxis.set_major_locator(plt.NullLocator())

        plt.imshow(sprite_img)
        if output:
            plt.savefig(output, bbox_inches='tight', pad_inches=0.1, transparent=True)
        else:
            plt.show()
