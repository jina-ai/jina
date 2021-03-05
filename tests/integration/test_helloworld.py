import os
import subprocess
from pathlib import Path

import pytest
from jina.clients.sugary_io import _input_ndarray
from jina.flow import Flow
from jina.helloworld.helper import download_data
from jina import helper
from jina.parsers.helloworld import (
    set_hw_parser,
    set_hw_chatbot_parser,
    set_hw_multimodal_parser,
)
from pkg_resources import resource_filename

EMPTY_IMAGE_URL = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAYAAAByDd+UAAAECklEQVR42u2WSSi2axjH+ZSFDaUUFobMQ5mHzFPmKfOQKVNIIYkMGUJJUrIRZWFhIbEgWVhZsLBUpCgsJRtDhuv0u/S853O+Tr1Op3M231v3ez/P/dzP/f//r+t/X/djIf/xz+I34P8G+PHxIQsLCzI4OChra2vy+Pio429vb98DfH19la2tLTk/P5fV1VWZm5uT8fFxGR0dlY6ODsnOzpbIyEhxc3OTlJQUaW9vl9raWhkeHjYR+Rbg4eGhJCYmSnFxsVRUVEhTU5M0NjZKfX29NDc3m+7b2tqkt7dXx6qrq2VgYOCL+m8BxsXFSVpammRlZUleXp4UFRVJfn6+qsvNzdXxpKQkycjIkIKCAn3W2dn5C6A5wBYXFxcKSLjS09N1UfqEhARtEDHA4uPjFZy5XV1dXwDNVWlxfX2tCyYnJ5tAU1NTJSYmRokQ7qioKAXmmgjQd3d3fzHN+/u7eYDPz88aOhYB0FBFY9xQZig3SJHLf5RD/ggTTkRZdHS0gsXGxuo96rlmzCBDXquqquTu7u5b6kyAODQ8PFyVGC00NFQB6QHJyclRcMaIRmlpqZSXl5ul8udnCsgi5AslNEIGaGFhoRLBmfSAEg0IAEbb2dnRhZ6ensxXSHhgDQhmoYcABuEeZSEhIbpdAKUgNDQ0KODGxoYuhBdeXl7MAyR/sEYpbiVXGAalgNbV1eniNTU1UllZKZmZmRIQECBeXl5SVlYmR0dHv4QQ91LF6MkxjXEF7O/vVyPQKFuwLykpUdURERHi4OAgVlZW2tvY2MiPHz/E0dFR505PT+v8paUlubm5MU/hw8ODBAYGirOzs9ja2uqilpaWYm1tLXZ2dmJvby9hYWFftgUkqastLS0yOzsrY2Nj0tfXJ1NTU7K4uCjb29tyfHysIZ+ZmZG9vb0/AYk/gO7u7homX19fbYxhFsDIKXnEtUZxwFTU2dbWVpmcnFQQwIaGhpQE9XZkZETVU5tPTk4+ATc3N01bISgoSPPj6empzc/PzwTOcw8PD3FxcdFQk19yCCAgLN7T0yPr6+tydnamCufn5/UAgPTExMQnIKGANS5kEfYlxoAECgFFub+/vwJDyiDEPep5h7wbBwChB4R3cDoKIaWAMKLCYBpOAlzKxsaxhpkobZgIRxPa4OBgVY5izkquIYZ6iADEOmw5jjNOl6urq0/A29tbZYEqo44a1QXlkEEh7FENEa5RxRzyCVEI8R65hTDPaD+fnaZPDJgQHpgDboTOx8dHdnd3dc79/b2srKxo6CHg5OQk3t7eepoYRiKUrq6umgrWPDg4MIGxJ02AFOL9/X39buHzAtex0U9PT/92T11eXsry8rJuDaoP+5I88bny159R4H9/Jv7rvz8AY0k6gVZiXR4AAAAASUVORK5CYII='


def check_hello_world_results(html_path: str):
    from bs4 import BeautifulSoup
    import re

    with open(html_path, 'r') as fp:
        page = fp.read()
    soup = BeautifulSoup(page)
    table = soup.find('table')
    rows = table.find_all('tr')
    assert len(rows) == 129
    for row in rows[1:]:
        cols = row.find_all('img')
        assert len(cols) == 51  # query + results

    evaluation = soup.find_all('h3')[0].text
    assert 'Precision@50' in evaluation
    assert 'Recall@50' in evaluation
    evaluation_results = re.findall(r'\d+\.\d+', evaluation)
    assert len(evaluation_results) == 2
    # not exact to avoid instability, but enough accurate to current results to raise some alarms
    assert float(evaluation_results[0]) > 50.0
    assert float(evaluation_results[1]) >= 0.5


@pytest.mark.timeout(360)
def test_helloworld_execution(tmpdir):
    cmd = ['jina', 'hello-world', '--workdir', str(tmpdir)]
    is_hello_world_in_stdout = False
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True) as proc:
        for stdout_line in iter(proc.stdout.readline, ""):
            #  'cli = hello-world' is in stdoutput of hello-world script
            #  this should be an indicator that hello-world script is executed
            if 'cli = hello-world' in stdout_line:
                is_hello_world_in_stdout = True
        proc.communicate()
        assert proc.returncode == 0, 'Script exited with non-zero code'
    # is_hello_world_in_stdout  = True
    assert is_hello_world_in_stdout, (
        'No cli = hello-world in stdoutput,' 'probably hello-world wasn\'t executed'
    )


@pytest.mark.timeout(360)
def test_helloworld_py(tmpdir):
    from jina.helloworld.fashion import hello_world

    hello_world(set_hw_parser().parse_args(['--workdir', str(tmpdir)]))
    check_hello_world_results(os.path.join(str(tmpdir), 'hello-world.html'))


@pytest.mark.timeout(360)
def test_helloworld_py_chatbot(tmpdir):
    from jina.helloworld.chatbot import hello_world

    hello_world(
        set_hw_chatbot_parser().parse_args(
            [
                '--workdir',
                str(tmpdir),
                '--unblock-query-flow',
                '--port-expose',
                str(helper.random_port()),
            ]
        )
    )


@pytest.mark.timeout(600)
def test_helloworld_py_multimodal(tmpdir):
    from jina.helloworld.multimodal import hello_world

    hello_world(
        set_hw_multimodal_parser().parse_args(
            [
                '--workdir',
                str(tmpdir),
                '--unblock-query-flow',
                '--port-expose',
                str(helper.random_port()),
            ]
        )
    )


@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ, reason='skip the network test on github workflow'
)
def test_helloworld_flow(tmpdir):
    args = set_hw_parser().parse_args([])

    os.environ['PATH'] += os.pathsep + resource_filename('jina', 'resources/fashion')
    os.environ['SHARDS'] = str(args.shards)
    os.environ['PARALLEL'] = str(args.parallel)
    os.environ['HW_WORKDIR'] = str(tmpdir)

    f = Flow.load_config('helloworld.flow.index.yml')

    targets = {
        'index': {
            'url': args.index_data_url,
            'filename': os.path.join(tmpdir, 'index-original'),
        },
        'query': {
            'url': args.query_data_url,
            'filename': os.path.join(tmpdir, 'query-original'),
        },
    }

    # download the data
    Path(tmpdir).mkdir(parents=True, exist_ok=True)
    download_data(targets)

    # run it!
    with f:
        f.index(
            _input_ndarray(targets['index']['data']),
            request_size=args.index_request_size,
        )


def test_helloworld_flow_dry_run(tmpdir):
    args = set_hw_parser().parse_args([])

    os.environ['PATH'] += os.pathsep + resource_filename('jina', 'resources/fashion')
    os.environ['SHARDS'] = str(args.shards)
    os.environ['PARALLEL'] = str(args.parallel)
    os.environ['HW_WORKDIR'] = str(tmpdir)

    # run it!
    with Flow.load_config('helloworld.flow.index.yml'):
        pass

    # run it!
    with Flow.load_config('helloworld.flow.query.yml'):
        pass


@pytest.mark.skipif(
    'GITHUB_WORKFLOW' in os.environ, reason='skip the network test on github workflow'
)
@pytest.mark.skipif(
    'HTTP_PROXY' not in os.environ,
    reason='skipped. '
    'Set os env `HTTP_PROXY` if you want run test at your local env.',
)
def test_download_proxy():
    import urllib.request

    # first test no proxy
    args = set_hw_parser().parse_args([])

    opener = urllib.request.build_opener()
    if args.download_proxy:
        proxy = urllib.request.ProxyHandler(
            {'http': args.download_proxy, 'https': args.download_proxy}
        )
        opener.add_handler(proxy)
    urllib.request.install_opener(opener)
    # head check
    req = urllib.request.Request(args.index_data_url, method="HEAD")
    response = urllib.request.urlopen(req, timeout=5)
    assert response.status == 200

    # test with proxy
    args = set_hw_parser().parse_args(["--download-proxy", os.getenv("HTTP_PROXY")])

    opener = urllib.request.build_opener()
    if args.download_proxy:
        proxy = urllib.request.ProxyHandler(
            {'http': args.download_proxy, 'https': args.download_proxy}
        )
        opener.add_handler(proxy)
    urllib.request.install_opener(opener)
    # head check
    req = urllib.request.Request(args.index_data_url, method="HEAD")
    response = urllib.request.urlopen(req, timeout=5)
    assert response.status == 200
