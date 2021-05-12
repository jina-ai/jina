import os
import json
import base64
from pathlib import Path

import pytest
import requests

from jina.docker.hubio import HubIO
from jina.parsers.hub import set_hub_build_parser, set_hub_pushpull_parser

cur_dir = os.path.dirname(os.path.abspath(__file__))
DUMMY_ACCESS_TOKEN = 'dummy access'


@pytest.fixture
def dummy_access_token(tmpdir):
    os.mkdir(os.path.join(str(tmpdir), '.jina'))
    access_path = os.path.join(os.path.join(str(tmpdir), '.jina'), 'access.yml')

    with open(access_path, 'w') as wp:
        wp.write(f'access_token: {DUMMY_ACCESS_TOKEN}')


class MockResponse:
    def __init__(self, response_code: int = 200):
        self.response_code = response_code

    @property
    def text(self):
        return json.dumps(
            {
                'docker_username': base64.b64encode('abc'.encode('ascii')).decode(
                    'ascii'
                ),
                'docker_password': base64.b64encode('def'.encode('ascii')).decode(
                    'ascii'
                ),
            }
        )

    @property
    def status_code(self):
        return self.response_code


@pytest.mark.timeout(360)
def test_hub_build_pull(mocker, monkeypatch, tmpdir, dummy_access_token):

    mock = mocker.Mock()

    def _mock_get(url, headers):
        mock(url=url, headers=headers)
        return MockResponse(response_code=requests.codes.ok)

    def _mock_post(url, headers, data):
        mock(url=url, headers=headers, data=data)
        return MockResponse(response_code=requests.codes.ok)

    def _mock_home():
        return Path(str(tmpdir))

    monkeypatch.setattr(Path, 'home', _mock_home)
    monkeypatch.setattr(requests, 'get', _mock_get)
    monkeypatch.setattr(requests, 'post', _mock_post)
    monkeypatch.setattr(HubIO, '_docker_login', mock)

    args = set_hub_build_parser().parse_args(
        [os.path.join(cur_dir, 'hub-mwu'), '--push', '--raise-error']
    )
    HubIO(args).build()

    args = set_hub_pushpull_parser().parse_args(['jinahub/pod.dummy_mwu_encoder:0.0.6'])
    HubIO(args).pull()


@pytest.mark.timeout(360)
def test_hub_build_uses():
    args = set_hub_build_parser().parse_args(
        [os.path.join(cur_dir, 'hub-mwu'), '--test-uses', '--raise-error']
    )
    HubIO(args).build()
    # build again it shall not fail
    HubIO(args).build()

    args = set_hub_build_parser().parse_args(
        [os.path.join(cur_dir, 'hub-mwu'), '--test-uses', '--daemon', '--raise-error']
    )
    HubIO(args).build()
    # build again it shall not fail
    HubIO(args).build()


@pytest.mark.timeout(360)
def test_hub_build_uses():
    args = set_hub_build_parser().parse_args(
        [os.path.join(cur_dir, 'hub-mwu'), '--test-uses', '--raise-error']
    )
    assert HubIO(args).build()['is_build_success']
    # build again it shall not fail
    assert HubIO(args).build()['is_build_success']

    args = set_hub_build_parser().parse_args(
        [os.path.join(cur_dir, 'hub-mwu'), '--test-uses', '--daemon', '--raise-error']
    )
    assert HubIO(args).build()['is_build_success']
    # build again it shall not fail
    assert HubIO(args).build()['is_build_success']


def test_hub_build_failures():
    for j in [
        'bad-dockerfile',
        'bad-pythonfile',
        'missing-dockerfile',
        'missing-manifest',
    ]:
        args = set_hub_build_parser().parse_args(
            [os.path.join(cur_dir, 'hub-mwu-bad', j)]
        )
        assert not HubIO(args).build()['is_build_success']


def test_hub_build_no_pymodules():
    args = set_hub_build_parser().parse_args(
        [os.path.join(cur_dir, 'hub-mwu-bad', 'fail-to-start')]
    )
    assert HubIO(args).build()['is_build_success']

    args = set_hub_build_parser().parse_args(
        [os.path.join(cur_dir, 'hub-mwu-bad', 'fail-to-start'), '--test-uses']
    )
    assert not HubIO(args).build()['is_build_success']


@pytest.fixture()
def requirements(request, tmpdir):
    requirements_file = os.path.join(tmpdir, 'requirements.txt')
    with open(requirements_file, 'w') as fp:
        fp.write(request.param)


@pytest.mark.parametrize(
    'requirements', ['jina\ntorch>=2', 'jina>=0.2\ntoch==3'], indirect=True
)
def test_jina_version_freeze(requirements, tmpdir):
    import pkg_resources
    from jina import __version__

    args = set_hub_build_parser().parse_args([str(tmpdir)])
    hubio = HubIO(args)
    hubio._freeze_jina_version()
    requirements_file = os.path.join(tmpdir, 'requirements.txt')
    with open(requirements_file, 'r') as fp:
        requirements = pkg_resources.parse_requirements(fp)
        assert len(list(filter(lambda x: 'jina' in str(x), requirements))) == 1
        for req in requirements:
            if 'jina' in str(req):
                assert str(req) == f'jina=={__version__}'


@pytest.mark.parametrize('requirements', ['torch'], indirect=True)
def test_jina_version_freeze_no_jina_dependency(requirements, tmpdir):
    import pkg_resources

    args = set_hub_build_parser().parse_args([str(tmpdir)])
    hubio = HubIO(args)
    hubio._freeze_jina_version()
    requirements_file = os.path.join(tmpdir, 'requirements.txt')
    with open(requirements_file, 'r') as fp:
        requirements = pkg_resources.parse_requirements(fp)
        assert len(list(filter(lambda x: 'jina' in str(x), requirements))) == 0


@pytest.mark.parametrize(
    'requirements', ['git+https://github.com/openai/CLIP.git'], indirect=True
)
def test_jina_version_freeze_no_jina_dependency_git_no_raise(requirements, tmpdir):
    args = set_hub_build_parser().parse_args([str(tmpdir)])
    hubio = HubIO(args)
    hubio._freeze_jina_version()


def test_labels():
    class MockContainers:
        def __init__(self):
            pass

        def build(self, *args, **kwargs):
            labels = kwargs['labels']
            assert all([isinstance(v, str) for k, v in labels.items()])
            assert 'ai.jina.hub.version' in labels
            assert 'ai.jina.hub.name' in labels

            raise BaseException('labels all good')

    args = set_hub_build_parser().parse_args(
        [os.path.join(cur_dir, 'hub-mwu'), '--test-uses', '--raise-error']
    )
    hubio = HubIO(args)
    hubio._raw_client = MockContainers()

    with pytest.raises(BaseException, match='labels all good'):
        hubio.build()
