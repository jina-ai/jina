import glob
import os

import pytest

from jina.flow import Flow

num_docs = 100

cur_dir = os.path.dirname(os.path.abspath(__file__))


def input_function(pattern='../../**/*.png'):
    idx = 0
    for g in glob.glob(pattern, recursive=True)[:num_docs]:
        with open(g, 'rb') as fp:
            yield fp.read()
            idx += 1


def input_function2(pattern=os.path.join(cur_dir, '../*.*')):
    for g in glob.glob(pattern, recursive=True)[:num_docs]:
        yield g


def input_function3():
    for g in [
        os.path.abspath(__file__),  # local file
        'https://github.com/jina-ai/jina/raw/master/.github/1500%D1%85667.gif?raw=true',
        'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AxWcWRUeCEeBO68T3u1qLWarHqMaxDnxhAEaLh0Ssu6ZGfnKcjP4CeDLoJok3o4aOPYAJocsjktZfo4Z7Q/WR1UTgppAAdguAhR+AUm9AnqRH2jgdBZ0R+kKxAFoAME32BL7fwQbcLzhw+dXMmY9BS9K8EarXyWLH8VYK1MACkxlLTY4Eh69XfjpROqjE7P0AeBx6DGmA8/lRRlTCmPkL196pC0aWBkVs2wyjqb/LABVYL8Xgeomjl3VtEMxAeaUrGvnIawVh/oBAAD///GwU6v3yCoVAAAAAElFTkSuQmCC',
        'https://cdn.bulbagarden.net/upload/thumb/2/21/001Bulbasaur.png/240px-001Bulbasaur.png',
    ]:
        yield g


@pytest.mark.parametrize('restful', [False, True])
def test_dummy_seg(mocker, restful):
    response_mock = mocker.Mock()
    f = Flow(restful=restful).add(uses='- !Buffer2URI | {mimetype: png}')
    with f:
        f.index(inputs=input_function, on_done=response_mock)

    response_mock.assert_called()
    response_mock_2 = mocker.Mock()
    f = Flow(restful=restful).add(uses='- !Buffer2URI | {mimetype: png, base64: true}')
    with f:
        f.index(inputs=input_function, on_done=response_mock_2)
    response_mock_2.assert_called()


@pytest.mark.parametrize('restful', [False, True])
def test_any_file(mocker, restful):
    response_mock = mocker.Mock()
    f = Flow(restful=restful).add(uses='- !URI2DataURI | {base64: true}')
    with f:
        f.index(inputs=input_function2, on_done=response_mock)
    response_mock.assert_called()


@pytest.mark.parametrize('restful', [False, True])
def test_aba(mocker, restful):
    response_mock = mocker.Mock()
    f = (
        Flow(restful=restful)
        .add(uses='- !Buffer2URI | {mimetype: png}')
        .add(uses='- !URI2Buffer {}')
        .add(uses='- !Buffer2URI | {mimetype: png}')
    )

    with f:
        f.index(inputs=input_function, on_done=response_mock)
    response_mock.assert_called()


@pytest.mark.parametrize('restful', [False, True])
def test_pathURI2Buffer(mocker, restful):
    response_mock = mocker.Mock()
    f = Flow(restful=restful).add(uses='- !URI2Buffer {}').add(uses='- !Buffer2URI {}')

    with f:
        f.index(inputs=input_function3, on_done=response_mock)
    response_mock.assert_called()


@pytest.mark.parametrize('restful', [False, True])
def test_text2datauri(mocker, restful):
    response_mock = mocker.Mock()
    f = Flow(restful=restful).add(uses='- !Text2URI {}')

    with f:
        f.index(['abc', '123', 'hello, world'], on_done=response_mock)
    response_mock.assert_called()


@pytest.mark.parametrize('restful', [False, True])
def test_gateway_dataui(mocker, restful):
    response_mock = mocker.Mock()
    f = Flow(restful=restful).add()

    with f:
        f.index(['abc', '123', 'hello, world'], on_done=response_mock)
    response_mock.assert_called()
