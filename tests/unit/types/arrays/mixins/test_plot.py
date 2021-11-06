import os
import random

import numpy as np
import pytest

from jina import DocumentArray, Document, DocumentArrayMemmap
from jina.types.document.generators import from_files


def test_sprite_image_generator(pytestconfig, tmpdir):
    da = DocumentArray(
        from_files(
            [
                f'{pytestconfig.rootdir}/.github/**/*.png',
                f'{pytestconfig.rootdir}/.github/**/*.jpg',
            ]
        )
    )
    da.plot_image_sprites(tmpdir / 'sprint_da.png')
    assert os.path.exists(tmpdir / 'sprint_da.png')
    dam = DocumentArrayMemmap()
    dam.extend(da)
    dam.plot_image_sprites(tmpdir / 'sprint_dam.png')
    assert os.path.exists(tmpdir / 'sprint_dam.png')


def da_and_dam():
    embeddings = np.array([[1, 0, 0], [2, 0, 0], [3, 0, 0]])
    doc_array = DocumentArray(
        [
            Document(embedding=x, tags={'label': random.randint(0, 5)})
            for x in embeddings
        ]
    )
    dam = DocumentArrayMemmap()
    dam.extend(doc_array)
    return doc_array, dam


@pytest.mark.parametrize('colored_tag', [None, 'tags__label', 'id', 'mime_type'])
@pytest.mark.parametrize('kwargs', [{}, dict(s=100, marker='^')])
@pytest.mark.parametrize('da', da_and_dam())
def test_pca_plot_generated(tmpdir, colored_tag, kwargs, da):
    file_path = os.path.join(tmpdir, 'pca_plot.png')
    da.plot_embeddings(file_path, colored_attr=colored_tag, **kwargs)
    assert os.path.exists(file_path)
