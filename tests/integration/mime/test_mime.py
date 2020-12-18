import glob
import os

from jina.flow import Flow

num_docs = 100

cur_dir = os.path.dirname(os.path.abspath(__file__))


def input_fn(pattern='../../**/*.png'):
    idx = 0
    for g in glob.glob(pattern, recursive=True)[:num_docs]:
        with open(g, 'rb') as fp:
            yield fp.read()
            idx += 1


def input_fn2(pattern=os.path.join(cur_dir, '../*.*')):
    for g in glob.glob(pattern, recursive=True)[:num_docs]:
        yield g


def input_fn3():
    for g in [
        os.path.abspath(__file__),  # local file
        'https://github.com/jina-ai/jina/raw/master/.github/1500%D1%85667.gif?raw=true',
        'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AxWcWRUeCEeBO68T3u1qLWarHqMaxDnxhAEaLh0Ssu6ZGfnKcjP4CeDLoJok3o4aOPYAJocsjktZfo4Z7Q/WR1UTgppAAdguAhR+AUm9AnqRH2jgdBZ0R+kKxAFoAME32BL7fwQbcLzhw+dXMmY9BS9K8EarXyWLH8VYK1MACkxlLTY4Eh69XfjpROqjE7P0AeBx6DGmA8/lRRlTCmPkL196pC0aWBkVs2wyjqb/LABVYL8Xgeomjl3VtEMxAeaUrGvnIawVh/oBAAD///GwU6v3yCoVAAAAAElFTkSuQmCC',
        'https://cdn.bulbagarden.net/upload/thumb/2/21/001Bulbasaur.png/240px-001Bulbasaur.png']:
        yield g


def test_dummy_seg(mocker):
    response_mock = mocker.Mock()
    f = Flow().add(uses='- !Buffer2URI | {mimetype: png}')
    with f:
        f.index(input_fn=input_fn, on_done=response_mock)

    response_mock.assert_called()
    response_mock_2 = mocker.Mock()
    f = Flow().add(uses='- !Buffer2URI | {mimetype: png, base64: true}')
    with f:
        f.index(input_fn=input_fn, on_done=response_mock_2)
    response_mock_2.assert_called()


def test_any_file(mocker):
    response_mock = mocker.Mock()
    f = Flow().add(uses='- !URI2DataURI | {base64: true}')
    with f:
        f.index(input_fn=input_fn2, on_done=response_mock)
    response_mock.assert_called()


def test_aba(mocker):
    response_mock = mocker.Mock()
    f = (Flow().add(uses='- !Buffer2URI | {mimetype: png}')
         .add(uses='- !URI2Buffer {}')
         .add(uses='- !Buffer2URI | {mimetype: png}'))

    with f:
        f.index(input_fn=input_fn, on_done=response_mock)
    response_mock.assert_called()


def test_pathURI2Buffer(mocker):
    response_mock = mocker.Mock()
    f = (Flow().add(uses='- !URI2Buffer {}')
         .add(uses='- !Buffer2URI {}'))

    with f:
        f.index(input_fn=input_fn3, on_done=response_mock)
    response_mock.assert_called()


def test_text2datauri(mocker):
    response_mock = mocker.Mock()
    f = (Flow().add(uses='- !Text2URI {}'))

    with f:
        f.index_lines(lines=['abc', '123', 'hello, world'], on_done=response_mock)
    response_mock.assert_called()


def test_gateway_dataui(mocker):
    response_mock = mocker.Mock()
    f = (Flow().add())

    with f:
        f.index_lines(lines=['abc', '123', 'hello, world'], on_done=response_mock)
    response_mock.assert_called()
