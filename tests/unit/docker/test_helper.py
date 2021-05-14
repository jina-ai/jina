import os
from pathlib import PosixPath

import pytest

from jina import __version__
from jina.docker.helper import credentials_file
from jina.docker.hubio import HubIO


def test_credentials_file():
    assert isinstance(credentials_file(), PosixPath)


@pytest.mark.skip(reason='2.0.0rc does not include jina hub')
def test_alias2path_transform():
    # bad naming result to itself
    assert HubIO._alias_to_local_path('abcdefg') == 'abcdefg'

    # good name results to the local path
    assert HubIO._alias_to_local_path('MongoDBIndexer') != 'MongoDBIndexer'
    assert os.path.exists(HubIO._alias_to_local_path('MongoDBIndexer'))


@pytest.mark.skip(reason='2.0.0rc does not include jina hub')
def test_alias2tag_transform():
    # bad naming result to itself
    assert HubIO._alias_to_docker_image_name('abcdefg') == 'abcdefg'

    # good name results to the local path
    assert HubIO._alias_to_docker_image_name('MongoDBIndexer') != 'MongoDBIndexer'
    assert HubIO._alias_to_docker_image_name('MongoDBIndexer').startswith('jinahub/')
    assert HubIO._alias_to_docker_image_name('MongoDBIndexer').endswith(__version__)
