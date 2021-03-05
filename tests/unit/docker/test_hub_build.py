import os

import pytest

from jina.docker.hubio import HubIO
from jina.parsers.hub import set_hub_build_parser, set_hub_pushpull_parser

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.timeout(360)
def test_hub_build_pull():
    args = set_hub_build_parser().parse_args(
        [os.path.join(cur_dir, 'hub-mwu'), '--push', '--test-uses', '--raise-error']
    )
    HubIO(args).build()

    args = set_hub_pushpull_parser().parse_args(['jinahub/pod.dummy_mwu_encoder'])
    HubIO(args).pull()

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
