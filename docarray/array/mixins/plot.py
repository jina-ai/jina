import copy
import json
import os.path
import shutil
import tempfile
import threading
import warnings
from math import sqrt, ceil, floor
from typing import Optional

import numpy as np


from ...helper import random_port, __resources_path__


class PlotMixin:
    """Helper functions for plotting the arrays. """

    def plot_embeddings(
        self,
        title: str = 'MyDocumentArray',
        path: Optional[str] = None,
        image_sprites: bool = False,
        min_image_size: int = 16,
        channel_axis: int = -1,
        start_server: bool = True,
        port: Optional[int] = None,
    ) -> str:
        """Interactively visualize :attr:`.embeddings` using the Embedding Projector.

        :param title: the title of this visualization. If you want to compare multiple embeddings at the same time,
                make sure to give different names each time and set ``path`` to the same value.
        :param port: if set, run the embedding-projector frontend at given port. Otherwise a random port is used.
        :param image_sprites: if set, visualize the dots using :attr:`.uri` and :attr:`.blob`.
        :param path: if set, then append the visualization to an existing folder, where you can compare multiple
            embeddings at the same time. Make sure to use a different ``title`` each time .
        :param min_image_size: only used when `image_sprites=True`. the minimum size of the image
        :param channel_axis: only used when `image_sprites=True`. the axis id of the color channel, ``-1`` indicates the color channel info at the last axis
        :param start_server: if set, start a HTTP server and open the frontend directly. Otherwise, you need to rely on ``return`` path and serve by yourself.
        :return: the path to the embeddings visualization info.
        """
        path = path or tempfile.mkdtemp()
        emb_fn = f'{title}.tsv'
        meta_fn = f'{title}.metas.tsv'
        config_fn = f'config.json'
        sprite_fn = f'{title}.png'

        if image_sprites:
            img_per_row = ceil(sqrt(len(self)))
            canvas_size = min(img_per_row * min_image_size, 8192)
            img_size = max(int(canvas_size / img_per_row), min_image_size)

            max_docs = ceil(canvas_size / img_size) ** 2
            if len(self) > max_docs:
                warnings.warn(
                    f'''
                    {self!r} has more than {max_docs} elements, which is the maximum number of image sprites can support. 
                    The resulting visualization may not be correct. You can do the following:
                    
                    - use fewer images: `da[:10000].plot_embeddings()`
                    - reduce the `min_image_size` to a smaller number, say 8 or 4 (but bear in mind you can hardly recognize anything with a 4x4 image)
                    - turn off `image_sprites` via `da.plot_embeddings(image_sprites=False)`
                    '''
                )

            self.plot_image_sprites(
                os.path.join(path, sprite_fn),
                canvas_size=canvas_size,
                min_size=min_image_size,
                channel_axis=channel_axis,
            )

        self.save_embeddings_csv(os.path.join(path, emb_fn), delimiter='\t')
        self.save_csv(
            os.path.join(path, meta_fn),
            exclude_fields=('embedding', 'blob', 'scores'),
            dialect='excel-tab',
        )

        _epj_config = {
            'embeddings': [
                {
                    'tensorName': title,
                    'tensorShape': list(self.embeddings.shape),
                    'tensorPath': f'/static/{emb_fn}',
                    'metadataPath': f'/static/{meta_fn}',
                    'sprite': {
                        'imagePath': f'/static/{sprite_fn}',
                        'singleImageDim': (img_size,) * 2,
                    }
                    if image_sprites
                    else {},
                }
            ]
        }

        if os.path.exists(os.path.join(path, config_fn)):
            with open(os.path.join(path, config_fn)) as fp:
                old_config = json.load(fp)
                _epj_config['embeddings'].extend(old_config.get('embeddings', []))

        with open(os.path.join(path, config_fn), 'w') as fp:
            json.dump(_epj_config, fp)

        shutil.copyfile(
            os.path.join(__resources_path__, 'embedding-projector/index.html'),
            os.path.join(path, 'index.html'),
        )

        if start_server:

            def _get_fastapi_app():
                from fastapi import FastAPI
                from starlette.middleware.cors import CORSMiddleware
                from starlette.staticfiles import StaticFiles

                app = FastAPI()
                app.add_middleware(
                    CORSMiddleware,
                    allow_origins=['*'],
                    allow_credentials=True,
                    allow_methods=['*'],
                    allow_headers=['*'],
                )
                app.mount('/static', StaticFiles(directory=path), name='static')
                return app

            import uvicorn

            app = _get_fastapi_app()
            port = port or random_port()
            t_m = threading.Thread(
                target=uvicorn.run,
                kwargs=dict(app=app, port=port, log_level='error'),
                daemon=True,
            )
            t_m.start()
            url_html_path = (
                f'http://localhost:{port}/static/index.html?config={config_fn}'
            )
            try:
                import webbrowser

                webbrowser.open(url_html_path, new=2)
            except:
                pass  # intentional pass, browser support isn't cross-platform
            finally:
                print(
                    f'You should see a webpage opened in your browser, '
                    f'if not, you may open {url_html_path} manually'
                )
            t_m.join()
        return path

    def plot_embeddings_legacy(
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
            from ...math.dimensionality_reduction import PCA

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
            _d = copy.deepcopy(d)
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

        from PIL import Image

        im = Image.fromarray(sprite_img)

        if output:
            with open(output, 'wb') as fp:
                im.save(fp)
        else:
            plt.gca().set_axis_off()
            plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
            plt.margins(0, 0)
            plt.gca().xaxis.set_major_locator(plt.NullLocator())
            plt.gca().yaxis.set_major_locator(plt.NullLocator())
            plt.imshow(im)
            plt.show()
