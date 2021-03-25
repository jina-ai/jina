import os
from glob import glob

import pytest

from jina import Flow

# noinspection PyUnresolvedReferences
from . import components


@pytest.mark.parametrize('top', [1, 3, 99])
def test_pngtodisk(tmpdir, top):
    tmpdir = str(tmpdir)
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    image_src = os.path.join(cur_dir, 'png/**.png')
    files = list(glob(image_src))
    assert files

    os.environ['JINA_WORKSPACE'] = tmpdir
    os.environ['PNG_TOP'] = str(top)

    with Flow().add(uses='craft.yml') as f:
        f.index_files(image_src, read_mode='rb')

    assert os.path.exists(os.path.join(tmpdir, 'norm'))
    assert os.path.exists(os.path.join(tmpdir, 'crop'))

    results_expected = min((len(files), top))

    glob_results_norm = glob(os.path.join(tmpdir, 'norm', '*.png'))
    assert len(glob_results_norm) == results_expected

    glob_results_crop = glob(os.path.join(tmpdir, 'crop', '*.png'))
    assert len(glob_results_crop) == results_expected
