import cgi
import itertools
import json
import os
import shutil
import urllib
from argparse import Namespace
from io import BytesIO
from pathlib import Path

import docker
import hubble
import pytest
import requests
import yaml

from jina.hubble import helper, hubio
from jina.hubble.helper import disk_cache_offline, get_requirements_env_variables
from jina.hubble.hubapi import get_secret_path
from jina.hubble.hubio import HubExecutor, HubIO
from jina.parsers.hubble import (
    set_hub_new_parser,
    set_hub_pull_parser,
    set_hub_push_parser,
    set_hub_status_parser,
)

cur_dir = os.path.dirname(os.path.abspath(__file__))


class PostMockResponse:
    def __init__(self, response_code: int = 201, response_error: str = ''):
        self.response_code = response_code
        self.response_error = response_error

    def json(self):
        return {
            'type': 'complete',
            'subject': 'createExecutor',
            'message': 'Successfully pushed w7qckiqy',
            'payload': {
                'id': 'w7qckiqy',
                'secret': 'f7386f9ef7ea238fd955f2de9fb254a0',
                'visibility': 'public',
            },
        }

    @property
    def text(self):
        return json.dumps(self.json())

    @property
    def status_code(self):
        return self.response_code

    def iter_lines(self):
        logs = [
            '{"type":"init","subject":"createExecutor"}',
            '{"type":"start","subject":"extractZip"}',
            '{"type":"done","subject":"extractZip"}',
            '{"type":"start","subject":"pushImage"}',
            '{"type":"done","subject":"pushImage"}',
            '{"type":"progress","subject":"buildWorkspace"}',
            '{"type":"console","subject":"pushImage","payload":"payload_test"}',
            b'{"type":"complete","subject":"createExecutor","message":"Successfully pushed w7qckiqy","payload": {"id":"w7qckiqy","secret":"f7386f9ef7ea238fd955f2de9fb254a0","visibility":"public"}}',
        ]

        if self.response_error == 'response_error':
            logs = [
                b'{"type":"error","message":"test error", "payload":{"readableMessage": "readableMessage"}}',
                '{"type":"start","subject":"extractZip"}',
                '{"type":"done","subject":"extractZip"}',
                '{"type":"start","subject":"pushImage"}',
                '{"type":"done","subject":"pushImage"}',
                '{"type":"console","subject":"pushImage","payload":"payload_test"}',
                b'{"type":"complete","subject":"createExecutor","message":"Successfully pushed w7qckiqy","payload":{"id":"w7qckiqy","secret":"f7386f9ef7ea238fd955f2de9fb254a0","visibility":"public"}}',
            ]

        if self.response_error == 'image_not_exits':
            logs = [
                '{"type":"error","message":"test error"}',
                '{"type":"start","subject":"extractZip"}',
                '{"type":"done","subject":"extractZip"}',
                '{"type":"start","subject":"pushImage"}',
                '{"type":"done","subject":"pushImage"}',
                '{"type":"console","subject":"pushImage","payload":"payload_test"}',
                b'{"type":"complete","subject":"createExecutor","message":"Successfully pushed w7qckiqy"}',
            ]

        return itertools.chain(logs)


class FetchMetaMockResponse:
    def __init__(
        self,
        response_code: int = 200,
        no_image=False,
        fail_count=0,
        add_build_env=False,
    ):
        self.response_code = response_code
        self.no_image = no_image
        self._tried_count = 0
        self._fail_count = fail_count
        self._build_env = add_build_env

    def json(self):
        if self._tried_count <= self._fail_count:
            return {'message': 'Internal server error'}

        commit_val = {'_id': 'commit_id', 'tags': ['v0']}
        if self._build_env:
            commit_val['commitParams'] = {'buildEnv': {'key1': 'val1', 'key2': 'val2'}}

        return {
            'data': {
                'keywords': [],
                'id': 'dummy_mwu_encoder',
                'name': 'alias_dummy',
                'visibility': 'public',
                'commit': commit_val,
                'package': {
                    'containers': []
                    if self.no_image
                    else ['jinahub/pod.dummy_mwu_encoder'],
                    'download': 'http://hubbleapi.jina.ai/files/dummy_mwu_encoder-v0.zip',
                    'md5': 'ecbe3fdd9cbe25dbb85abaaf6c54ec4f',
                },
            }
        }

    @property
    def text(self):
        return json.dumps(self.json())

    @property
    def status_code(self):
        self._tried_count += 1
        if self._tried_count <= self._fail_count:
            return 500

        return self.response_code


class LoggedInPostMockResponse:
    def __init__(self, response_code: int = 202):
        self.response_code = response_code

    def json(self):
        return {
            '_id': '6316ede56501',
            'topic': 'executor:buildAndCreateNewCommit',
            'data': {
                'executor': 'bebbf22d20',
                'visibility': 'private',
                'commitTags': ['v0'],
                'immutableCommitTags': [],
                'jinaEnv': {
                    'meta': {
                        'jina': '3.8.2',
                        'docarray': '0.16.1',
                        'jcloud': '0.0.35',
                        'jina-hubble-sdk': '0.16.1',
                        'jina-proto': '0.1.13',
                        'protobuf': '3.20.1',
                        'proto-backend': 'python',
                        'grpcio': '1.47.0',
                        'pyyaml': '6.0',
                        'python': '3.9.13',
                        'platform': 'Darwin',
                        'platform-release': '21.4.0',
                        'platform-version': 'Darwin Kernel Version 21.4.0: Mon Feb 21 20:36:53 PST 2022; root:xnu-8020.101.4~2/RELEASE_ARM64_T8101',
                        'architecture': 'arm64',
                        'processor': 'arm',
                        'uid': '86450951707024',
                        'session-id': '4c2810ea-2db0-11ed-9481-4ea06e445990',
                        'uptime': '2022-09-06T14:51:12.849445',
                        'ci-vendor': '(unset)',
                    },
                    'env': {
                        'default_host': '(unset)',
                        'default_timeout_ctrl': '500',
                        'deployment_name': '(unset)',
                        'disable_uvloop': '(unset)',
                        'early_stop': '(unset)',
                        'full_cli': '(unset)',
                        'gateway_image': '(unset)',
                        'grpc_recv_bytes': '(unset)',
                        'grpc_send_bytes': '(unset)',
                        'hub_no_image_rebuild': '(unset)',
                        'log_config': '(unset)',
                        'log_level': 'DEBUG',
                        'log_no_color': '(unset)',
                        'mp_start_method': '(unset)',
                        'optout_telemetry': 'True',
                        'random_port_max': '(unset)',
                        'random_port_min': '(unset)',
                    },
                    'clientIp': '58.152.48.222',
                },
                'buildParams': {
                    'noCache': True,
                    'buildArgs': {'ARG_BUILD_DATE': '2022-09-06T06:51:17.376Z'},
                    'buildSecrets': ['6316ede46501894889a8a36d'],
                },
                'normalizationResult': {
                    'executor': 'MyExecutor',
                    'docstring': None,
                    'init': {
                        'args': [{'arg': 'self', 'annotation': None}],
                        'kwargs': [],
                        'docstring': None,
                    },
                    'endpoints': [
                        {
                            'args': [{'arg': 'self', 'annotation': None}],
                            'kwargs': [],
                            'docstring': None,
                            'name': 'foo',
                            'requests': 'ALL',
                        }
                    ],
                    'hubble_score_metrics': {
                        'dockerfile_exists': False,
                        'manifest_exists': True,
                        'config_exists': False,
                        'readme_exists': False,
                        'requirements_exists': True,
                        'tests_exists': False,
                        'gpu_dockerfile_exists': False,
                    },
                    'filepath': '/data/jina-hubble-temp/4e34f1a0-2db0-11ed-a502-abf1ab488543/exec.py',
                },
                'normalizedZipFile': 'normalized.zip',
                'uploadedZipFile': 'uploaded.zip',
            },
            'owner': '62b49155b31010',
            'createdAt': '2022-09-06T06:51:17.456Z',
            'updatedAt': '2022-09-06T06:51:17.376Z',
            'status': 'created',
            'triesLeft': 1,
            'traceId': '4c2810ea-2db0-11ed-9481-4ea06e445990',
        }

    @property
    def text(self):
        return json.dumps(self.json())

    @property
    def status_code(self):
        return self.response_code

    def iter_lines(self):
        logs = [
            '{"code":202,"status":20200,"data":{"_id":"6316ede56501","topic":"executor:buildAndCreateNewCommit","data":{"executor":"bebbf22d20","visibility":"private","commitTags":["v0"],"immutableCommitTags":[], "jinaEnv":{"meta":{"jina":"3.8.2","docarray":"0.16.1","jcloud":"0.0.35","jina-hubble-sdk":"0.16.1","jina-proto":"0.1.13","protobuf":"3.20.1","proto-backend":"python","grpcio":"1.47.0","pyyaml":"6.0","python":"3.9.13","platform":"Darwin","platfor m-release":"21.4.0","platform-version":"Darwin Kernel Version 21.4.0: Mon Feb 21 20:36:53 PST 2022; root:xnu-8020.101.4~2/RELEASE_ARM64_T8101","architecture":"arm64","processor":"arm","uid":"86450951707024","session-id":"4c2810ea-2db0-11ed-9481- 4ea06e445990","uptime":"2022-09-06T14:51:12.849445","ci-vendor":"(unset)"},"env":{"default_host":"(unset)","default_timeout_ctrl":"500","deployment_name":"(unset)","disable_uvloop":"(unset)","early_stop":"(unset)","full_cli":"(unset)","gateway_i mage":"(unset)","grpc_recv_bytes":"(unset)","grpc_send_bytes":"(unset)","hub_no_image_rebuild":"(unset)","log_config":"(unset)","log_level":"DEBUG","log_no_color":"(unset)","mp_start_method":"(unset)","optout_telemetry":"True","random_port_max": "(unset)","random_port_min":"(unset)"},"clientIp":"58.152.48.222"},"buildParams":{"noCache":true,"buildArgs":{"ARG_BUILD_DATE":"2022-09-06T06:51:17.376Z"},"buildSecrets":["6316ede46501894889a8a36d"]},"normalizationResult":{"executor":"MyExecutor ","docstring":null,"init":{"args":[{"arg":"self","annotation":null}],"kwargs":[],"docstring":null},"endpoints":[{"args":[{"arg":"self","annotation":null}],"kwargs":[],"docstring":null,"name":"foo","requests":"ALL"}],"hubble_score_metrics":{"dock erfile_exists":false,"manifest_exists":true,"config_exists":false,"readme_exists":false,"requirements_exists":true,"tests_exists":false,"gpu_dockerfile_exists":false},"filepath":"/data/jina-hubble-temp/4e34f1a0-2db0-11ed-a502-abf1ab488543/exec.p y"},"normalizedZipFile":"normalized.zip","uploadedZipFile":"uploaded.zip"},"owner":"62b49155b31010","createdAt":"2022-09-06T06:51:17.456Z","updatedAt":"2022-09-06T06:51:17.376Z","status":"created","triesLeft":1,"traceId":"4c2810ea-2db0 -11ed-9481-4ea06e445990"}}'
        ]

        return itertools.chain(logs)


class StatusPostMockResponse:
    def __init__(self, response_code: int = 202, response_error: bool = False):
        self.response_code = response_code
        self.response_error = response_error

    def json(self):
        return {
            "_id": "1e4bebbf22d20",
            "id": "w7qckiqy",
            "ownerUserId": "01044af02b79a",
            "name": "dummy_executor",
            "identifiers": ["w7qckiqy", "dummy_executor"],
            "visibility": "private",
        }

    @property
    def text(self):
        return json.dumps(self.json())

    @property
    def status_code(self):
        return self.response_code

    def iter_lines(self):
        logs = [
            b'{"type":"progress","data":{"sn":212,"dt":28165,"data":{"type":"console","subject":"buildWorkspace","payload":"#11 pushing layer 9a3c20c4fe55","source":"stderr"}}}',
            b'{"type":"progress","data":{"sn":212,"dt":28165,"data":{"type":"console","subject":"buildWorkspace","payload":"#11 pushing layer 9a3c20c4fe55","source":"stderr"}}}',
            b'{"type":"progress","data":{"sn":213,"dt":28165,"data":{"type":"console","subject":"buildWorkspace","payload":"#11 pushing layer 3c7441d381a3","source":"stderr"}}}',
            b'{"type":"report","status":"pending"}',
            b'{"type":"report","status":"waiting","task":{"_id":"6316e9ac8e"}}',
            b'{"type":"test","status":"test","task":{"_id":"6316e9ac8e"}}',
            b'{"type":"progress","data":{"sn":213,"dt":28165,"data":{"type":"done","subject":"buildWorkspace","payload":"Done","source":"stderr"}}}',
            b'{"type":"report","status":"succeeded","task":{"_id":"6316e9ac8e"}}',
            b'{"type":"report","status":"succeeded","task":{"_id":"6316e9ac8e"}, "result":{"_id":"1e4bebbf22d20","id":"w7qckiqy","ownerUserId":"01044af02b79a","name":"dummy_executor","identifiers":["w7qckiqy","dummy_executor"],"visibility":"private"}}',
        ]
        if self.response_error:
            logs = [
                b'{"type":"report","status":"failed","message":"async upload error"}',
                b'{"type":"progress","data":{"sn":212,"dt":28165,"data":{"type":"console","subject":"buildWorkspace","payload":"#11 pushing layer 9a3c20c4fe55","source":"stderr"}}}',
                b'{"type":"progress","data":{"sn":213,"dt":28165,"data":{"type":"console","subject":"buildWorkspace","payload":"#11 pushing layer 3c7441d381a3","source":"stderr"}}}',
                b'{"type":"error","message":"async upload error"}',
                b'{"type":"progress","data":{"sn":213,"dt":28165,"data":{"type":"done","subject":"buildWorkspace","payload":"Done","source":"stderr"}}}',
                b'{"type":"report","status":"succeeded","task":{"_id":"6316e9ac8e"}, "result":{"_id":"1e4bebbf22d20","id":"w7qckiqy","ownerUserId":"01044af02b79a","name":"dummy_executor","identifiers":["w7qckiqy","dummy_executor"],"visibility":"private"}}',
                b'{"type":"report","status":"succeeded","task":{"_id":"6316e9ac8e"}}',
            ]

        if self.response_code >= 400:
            logs = [
                b'{"type":"report","status":"failed","message":"async upload error"}',
                b'{"type":"progress","data":{"sn":212,"dt":28165,"data":{"type":"console","subject":"buildWorkspace","payload":"#11 pushing layer 9a3c20c4fe55","source":"stderr"}}}',
                b'{"type":"progress","data":{"sn":213,"dt":28165,"data":{"type":"console","subject":"buildWorkspace","payload":"#11 pushing layer 3c7441d381a3","source":"stderr"}}}',
                b'{"type":"code","message":"AuthenticationRequiredError"}',
                b'{"type":"progress","data":{"sn":213,"dt":28165,"data":{"type":"done","subject":"buildWorkspace","payload":"Done","source":"stderr"}}}',
                b'{"type":"report","status":"succeeded","task":{"_id":"6316e9ac8e"}, "result":{"_id":"1e4bebbf22d20","id":"w7qckiqy","ownerUserId":"01044af02b79a","name":"dummy_executor","identifiers":["w7qckiqy","dummy_executor"],"visibility":"private"}}',
                b'{"type":"report","status":"succeeded","task":{"_id":"6316e9ac8e"}}',
            ]

        return itertools.chain(logs)


@pytest.mark.parametrize('no_cache', [True, False])
@pytest.mark.parametrize('tag', ['v0', None])
@pytest.mark.parametrize('force', [None, 'UUID8'])
@pytest.mark.parametrize('path', ['dummy_executor'])
@pytest.mark.parametrize('mode', ['--public', '--private'])
@pytest.mark.parametrize('build_env', ['DOMAIN=github.com DOWNLOAD=download'])
@pytest.mark.parametrize('is_login', [True, False])
@pytest.mark.parametrize('verbose', [False, True])
def test_push(
    mocker,
    monkeypatch,
    path,
    mode,
    tmpdir,
    force,
    tag,
    no_cache,
    build_env,
    is_login,
    verbose,
):
    mock = mocker.Mock()

    if is_login:

        def _mock_logged_post(url, data, headers=None, stream=True):
            mock(url=url, data=data, headers=headers)
            return LoggedInPostMockResponse(response_code=requests.codes.created)

        monkeypatch.setattr(requests, 'post', _mock_logged_post)
        # Second push will use --force --secret because of .jina/secret.key
        # Then it will use put method
        monkeypatch.setattr(requests, 'put', _mock_logged_post)

        def _mock_status_post(self, console, st, task_id, verbose, replay):
            mock(self, console, st, task_id, verbose, replay)
            return StatusPostMockResponse(response_code=requests.codes.created).json()

        monkeypatch.setattr(HubIO, '_status_with_progress', _mock_status_post)

    else:

        def _mock_post(url, data, headers=None, stream=True):
            mock(url=url, data=data, headers=headers)
            return PostMockResponse(response_code=requests.codes.created)

        monkeypatch.setattr(requests, 'post', _mock_post)
        # Second push will use --force --secret because of .jina/secret.key
        # Then it will use put method
        monkeypatch.setattr(requests, 'put', _mock_post)

    exec_path = os.path.join(cur_dir, path)
    _args_list = [exec_path, mode]

    if force:
        _args_list.extend(['--force', force])

    if tag:
        _args_list.extend(['-t', tag])

    if no_cache:
        _args_list.append('--no-cache')

    if build_env:
        _args_list.extend(['--build-env', build_env])

    if verbose:
        _args_list.append('--verbose')

    args = set_hub_push_parser().parse_args(_args_list)

    with monkeypatch.context() as m:
        m.setattr(hubble, 'is_logged_in', lambda: is_login)
        HubIO(args).push()

    exec_config_path = get_secret_path(os.stat(exec_path).st_ino)
    shutil.rmtree(exec_config_path)

    _, mock_kwargs = mock.call_args_list[0]
    c_type, c_data = cgi.parse_header(mock_kwargs['headers']['Content-Type'])

    assert c_type == 'multipart/form-data'

    form_data = cgi.parse_multipart(
        BytesIO(mock_kwargs['data']), {'boundary': c_data['boundary'].encode()}
    )

    assert 'file' in form_data
    assert 'md5sum' in form_data

    if force:
        assert form_data['id'] == ['UUID8']
    else:
        assert form_data.get('id') is None

    if build_env:
        assert form_data['buildEnv'] == [
            '{"DOMAIN": "github.com", "DOWNLOAD": "download"}'
        ]
    else:
        assert form_data.get('buildEnv') is None

    if mode == '--private':
        assert form_data['private'] == ['True']
        assert form_data['public'] == ['False']
    else:
        assert form_data['private'] == ['False']
        assert form_data['public'] == ['True']

    if tag:
        assert form_data['tags'] == ['v0']
    else:
        assert form_data.get('tags') is None

    if no_cache:
        assert form_data['buildWithNoCache'] == ['True']
    else:
        assert form_data.get('buildWithNoCache') is None


@pytest.mark.parametrize(
    'env_variable_consist_error',
    [
        'The `--build-env` parameter key:`{build_env_key}` can only consist of uppercase letter and number and underline.'
    ],
)
@pytest.mark.parametrize(
    'env_variable_format_error',
    [
        'The `--build-env` parameter: `{build_env}` is wrong format. you can use: `--build-env {build_env}=YOUR_VALUE`.'
    ],
)
@pytest.mark.parametrize('path', ['dummy_executor_fail'])
@pytest.mark.parametrize('mode', ['--public', '--private'])
@pytest.mark.parametrize('build_env', ['TEST_TOKEN_ccc=ghp_I1cCzUY', 'NO123123'])
def test_push_wrong_build_env(
    mocker,
    monkeypatch,
    path,
    mode,
    tmpdir,
    env_variable_format_error,
    env_variable_consist_error,
    build_env,
):
    mock = mocker.Mock()

    def _mock_post(url, data, headers=None, stream=True):
        mock(url=url, data=data, headers=headers)
        return PostMockResponse(response_code=requests.codes.created)

    monkeypatch.setattr(requests, 'post', _mock_post)
    # Second push will use --force --secret because of .jina/secret.key
    # Then it will use put method
    monkeypatch.setattr(requests, 'put', _mock_post)

    exec_path = os.path.join(cur_dir, path)
    _args_list = [exec_path, mode]

    if build_env:
        _args_list.extend(['--build-env', build_env])

    args = set_hub_push_parser().parse_args(_args_list)

    with pytest.raises(Exception) as info:
        result = HubIO(args).push()

    assert env_variable_format_error.format(build_env=build_env) in str(
        info.value
    ) or env_variable_consist_error.format(
        build_env_key=build_env.split('=')[0]
    ) in str(
        info.value
    )


@pytest.mark.parametrize(
    'requirements_file_need_build_env_error',
    [
        'The requirements.txt set environment variables as follows:`{env_variables_str}` should use `--build-env'
    ],
)
@pytest.mark.parametrize('path', ['dummy_executor_fail'])
@pytest.mark.parametrize('mode', ['--public', '--private'])
@pytest.mark.parametrize('requirements_file', ['requirements.txt'])
def test_push_requirements_file_require_set_env_variables(
    mocker,
    monkeypatch,
    path,
    mode,
    tmpdir,
    requirements_file_need_build_env_error,
    requirements_file,
):
    mock = mocker.Mock()

    def _mock_post(url, data, headers=None, stream=True):
        mock(url=url, data=data, headers=headers)
        return PostMockResponse(response_code=requests.codes.created)

    monkeypatch.setattr(requests, 'post', _mock_post)
    # Second push will use --force --secret because of .jina/secret.key
    # Then it will use put method
    monkeypatch.setattr(requests, 'put', _mock_post)

    exec_path = os.path.join(cur_dir, path)
    _args_list = [exec_path, mode]

    args = set_hub_push_parser().parse_args(_args_list)

    requirements_file = os.path.join(exec_path, requirements_file)
    requirements_file_env_variables = get_requirements_env_variables(
        Path(requirements_file)
    )

    with pytest.raises(Exception) as info:
        result = HubIO(args).push()

    assert requirements_file_need_build_env_error.format(
        env_variables_str=','.join(requirements_file_env_variables)
    ) in str(info.value)


@pytest.mark.parametrize(
    'diff_env_variables_error',
    [
        'The requirements.txt set environment variables as follows:`{env_variables_str}` should use `--build-env'
    ],
)
@pytest.mark.parametrize('path', ['dummy_executor_fail'])
@pytest.mark.parametrize('mode', ['--public', '--private'])
@pytest.mark.parametrize('build_env', ['TOKEN=ghp_I1cCzUY'])
def test_push_diff_env_variables(
    mocker, monkeypatch, path, mode, tmpdir, diff_env_variables_error, build_env
):
    mock = mocker.Mock()

    def _mock_post(url, data, headers=None, stream=True):
        mock(url=url, data=data, headers=headers)
        return PostMockResponse(response_code=requests.codes.created)

    monkeypatch.setattr(requests, 'post', _mock_post)
    # Second push will use --force --secret because of .jina/secret.key
    # Then it will use put method
    monkeypatch.setattr(requests, 'put', _mock_post)

    exec_path = os.path.join(cur_dir, path)
    _args_list = [exec_path, mode]
    if build_env:
        _args_list.extend(['--build-env', build_env])

    args = set_hub_push_parser().parse_args(_args_list)

    requirements_file = os.path.join(exec_path, 'requirements.txt')
    requirements_file_env_variables = get_requirements_env_variables(
        Path(requirements_file)
    )
    diff_env_variables = list(
        set(requirements_file_env_variables).difference(set([build_env]))
    )

    with pytest.raises(Exception) as info:
        result = HubIO(args).push()

    assert diff_env_variables_error.format(
        env_variables_str=','.join(diff_env_variables)
    ) in str(info.value)


@pytest.mark.parametrize(
    'dockerfile, expected_error',
    [
        ('Dockerfile', 'The given Dockerfile `{dockerfile}` does not exist!'),
        (
            '../Dockerfile',
            'The Dockerfile must be placed at the given folder `{work_path}`',
        ),
    ],
)
@pytest.mark.parametrize('path', ['dummy_executor'])
@pytest.mark.parametrize('mode', ['--public', '--private'])
def test_push_wrong_dockerfile(
    mocker, monkeypatch, path, mode, tmpdir, dockerfile, expected_error
):
    dockerfile = os.path.join(cur_dir, path, dockerfile)
    mock = mocker.Mock()

    def _mock_post(url, data, headers=None, stream=True):
        mock(url=url, data=data)
        return PostMockResponse(response_code=requests.codes.created)

    monkeypatch.setattr(requests, 'post', _mock_post)
    # Second push will use --force --secret because of .jina/secret.key
    # Then it will use put method
    monkeypatch.setattr(requests, 'put', _mock_post)

    exec_path = os.path.join(cur_dir, path)
    _args_list = [exec_path, mode]

    args = set_hub_push_parser().parse_args(_args_list)
    args.dockerfile = dockerfile

    with pytest.raises(Exception) as info:
        HubIO(args).push()

    assert expected_error.format(dockerfile=dockerfile, work_path=args.path) in str(
        info.value
    )


@pytest.mark.parametrize(
    'response_error',
    ['test error session_id'],
)
@pytest.mark.parametrize(
    'response_image_not_exits_error',
    ['Unknown Error, session_id'],
)
@pytest.mark.parametrize(
    'response_readableMessage_error',
    ['readableMessage session_id'],
)
@pytest.mark.parametrize('path', ['dummy_executor'])
@pytest.mark.parametrize('mode', ['--public', '--private'])
@pytest.mark.parametrize('build_env', ['DOMAIN=github.com DOWNLOAD=download'])
@pytest.mark.parametrize('response_error_status', ['image_not_exits', 'response_error'])
def test_push_with_error(
    mocker,
    monkeypatch,
    path,
    mode,
    tmpdir,
    build_env,
    response_error,
    response_image_not_exits_error,
    response_readableMessage_error,
    response_error_status,
):
    mock = mocker.Mock()

    def _mock_post(url, data, headers=None, stream=True):
        mock(url=url, data=data, headers=headers)
        return PostMockResponse(
            response_code=requests.codes.created, response_error=response_error_status
        )

    monkeypatch.setattr(requests, 'post', _mock_post)
    # Second push will use --force --secret because of .jina/secret.key
    # Then it will use put method
    monkeypatch.setattr(requests, 'put', _mock_post)

    exec_path = os.path.join(cur_dir, path)
    _args_list = [exec_path, mode]

    if build_env:
        _args_list.extend(['--build-env', build_env])

    args = set_hub_push_parser().parse_args(_args_list)

    with pytest.raises(Exception) as info:
        result = HubIO(args).push()

    assert (
        response_error in str(info.value)
        or response_image_not_exits_error in str(info.value)
        or response_readableMessage_error in str(info.value)
    )


@pytest.mark.parametrize('task_id', [None, '6316e9ac8e'])
@pytest.mark.parametrize('verbose', [False, True])
@pytest.mark.parametrize('replay', [False, True])
@pytest.mark.parametrize('is_login', [False, True])
@pytest.mark.parametrize('path', ['dummy_executor'])
def test_status(mocker, monkeypatch, path, verbose, replay, task_id, is_login):

    mock = mocker.Mock()

    def _mock_post(url, data, headers=None, stream=True):
        mock(url=url, data=data, headers=headers, stream=stream)
        return StatusPostMockResponse(response_code=requests.codes.created)

    monkeypatch.setattr(requests, 'post', _mock_post)

    exec_path = os.path.join(cur_dir, path)
    _args_list = [exec_path]

    if task_id:
        _args_list.extend(['--id', task_id])

    if verbose:
        _args_list.append('--verbose')

    if replay:
        _args_list.append('--replay')

    args = set_hub_status_parser().parse_args(_args_list)

    with monkeypatch.context() as m:
        m.setattr(hubble, 'is_logged_in', lambda: is_login)
        if not task_id:
            m.setattr(
                hubio,
                'load_secret',
                lambda exec_path: ('pathw7qckiqy', None, '6316e9ac8e'),
            )
        HubIO(args).status()

    _, mock_kwargs = mock.call_args_list[0]
    c_type, c_data = cgi.parse_header(mock_kwargs['headers']['Content-Type'])

    assert c_type == 'multipart/form-data'

    form_data = cgi.parse_multipart(
        BytesIO(mock_kwargs['data']), {'boundary': c_data['boundary'].encode()}
    )

    if task_id:
        form_data['id'] == task_id

    if verbose:
        form_data['verbose'] == True
    else:
        form_data['verbose'] == False

    if replay:
        form_data['replay'] == True
    else:
        form_data['replay'] == False


@pytest.mark.parametrize('task_id', [None, '6316e9ac8e'])
@pytest.mark.parametrize('verbose', [False, True])
@pytest.mark.parametrize('replay', [False, True])
@pytest.mark.parametrize('code', [200, 401])
@pytest.mark.parametrize('path', ['dummy_executor'])
@pytest.mark.parametrize(
    'response_error',
    [
        'async upload error',
    ],
)
@pytest.mark.parametrize(
    'response_code_error',
    [
        'AuthenticationRequiredError',
    ],
)
@pytest.mark.parametrize(
    'response_task_id_error',
    [
        'Error: can\'t get task_id',
    ],
)
def test_status_with_error(
    mocker,
    monkeypatch,
    verbose,
    replay,
    code,
    task_id,
    path,
    response_error,
    response_code_error,
    response_task_id_error,
):

    mock = mocker.Mock()

    def _mock_post(url, data, headers=None, stream=True):
        mock(url=url, data=data, headers=headers, stream=stream)
        return StatusPostMockResponse(response_code=code, response_error=True)

    monkeypatch.setattr(requests, 'post', _mock_post)

    monkeypatch.setattr(requests, 'get', _mock_post)

    exec_path = os.path.join(cur_dir, path)
    _args_list = [exec_path]

    if task_id:
        _args_list.extend(['--id', task_id])

    if verbose:
        _args_list.append('--verbose')

    if replay:
        _args_list.append('--replay')

    with pytest.raises(Exception) as info:
        args = set_hub_status_parser().parse_args(_args_list)
        HubIO(args).status()

    assert (
        response_error in str(info.value)
        or response_code_error in str(info.value)
        or response_task_id_error in str(info.value)
    )


@pytest.mark.parametrize('rebuild_image', [True, False])
def test_fetch(mocker, monkeypatch, rebuild_image):
    mock = mocker.Mock()

    def _mock_post(url, json, headers=None):
        mock(url=url, json=json)
        return FetchMetaMockResponse(response_code=200)

    monkeypatch.setattr(requests, 'post', _mock_post)
    args = set_hub_pull_parser().parse_args(['jinahub://dummy_mwu_encoder'])

    executor, _ = HubIO(args).fetch_meta(
        'dummy_mwu_encoder', None, rebuild_image=rebuild_image, force=True
    )

    assert executor.uuid == 'dummy_mwu_encoder'
    assert executor.name == 'alias_dummy'
    assert executor.tag == 'v0'
    assert executor.image_name == 'jinahub/pod.dummy_mwu_encoder'
    assert executor.md5sum == 'ecbe3fdd9cbe25dbb85abaaf6c54ec4f'

    _, mock_kwargs = mock.call_args_list[0]
    assert mock_kwargs['json']['rebuildImage'] is rebuild_image

    executor, _ = HubIO(args).fetch_meta('dummy_mwu_encoder', '', force=True)
    assert executor.tag == 'v0'

    _, mock_kwargs = mock.call_args_list[1]
    assert mock_kwargs['json']['rebuildImage'] is True  # default value must be True

    executor, _ = HubIO(args).fetch_meta('dummy_mwu_encoder', 'v0.1', force=True)
    assert executor.tag == 'v0.1'


@pytest.mark.parametrize('rebuild_image', [True, False])
def test_fetch_with_build_env(mocker, monkeypatch, rebuild_image):
    mock = mocker.Mock()

    def _mock_post(url, json, headers=None):
        mock(url=url, json=json)
        return FetchMetaMockResponse(response_code=200, add_build_env=True)

    monkeypatch.setattr(requests, 'post', _mock_post)
    args = set_hub_pull_parser().parse_args(['jinahub://dummy_mwu_encoder'])

    executor, _ = HubIO(args).fetch_meta(
        'dummy_mwu_encoder', None, rebuild_image=rebuild_image, force=True
    )

    assert executor.uuid == 'dummy_mwu_encoder'
    assert executor.name == 'alias_dummy'
    assert executor.tag == 'v0'
    assert executor.image_name == 'jinahub/pod.dummy_mwu_encoder'
    assert executor.md5sum == 'ecbe3fdd9cbe25dbb85abaaf6c54ec4f'
    assert executor.build_env == ['key1', 'key2']

    _, mock_kwargs = mock.call_args_list[0]
    assert mock_kwargs['json']['rebuildImage'] is rebuild_image

    executor, _ = HubIO(args).fetch_meta('dummy_mwu_encoder', '', force=True)
    assert executor.tag == 'v0'

    _, mock_kwargs = mock.call_args_list[1]
    assert mock_kwargs['json']['rebuildImage'] is True  # default value must be True

    executor, _ = HubIO(args).fetch_meta('dummy_mwu_encoder', 'v0.1', force=True)
    assert executor.tag == 'v0.1'


def test_fetch_with_no_image(mocker, monkeypatch):
    mock = mocker.Mock()

    def _mock_post(url, json, headers=None):
        mock(url=url, json=json)
        return FetchMetaMockResponse(response_code=200, no_image=True)

    monkeypatch.setattr(requests, 'post', _mock_post)

    with pytest.raises(Exception) as exc_info:
        HubIO.fetch_meta('dummy_mwu_encoder', tag=None, force=True)

    assert exc_info.match('No image found for executor "dummy_mwu_encoder"')

    executor, _ = HubIO.fetch_meta(
        'dummy_mwu_encoder', tag=None, image_required=False, force=True
    )

    assert executor.image_name is None
    assert mock.call_count == 2


def test_fetch_with_retry(mocker, monkeypatch):
    mock = mocker.Mock()
    mock_response = FetchMetaMockResponse(response_code=200, fail_count=3)

    def _mock_post(url, json, headers=None):
        mock(url=url, json=json)
        return mock_response

    monkeypatch.setattr(requests, 'post', _mock_post)

    with pytest.raises(Exception) as exc_info:
        # failing 3 times, so it should raise an error
        HubIO.fetch_meta('dummy_mwu_encoder', tag=None, force=True)

    assert exc_info.match('{"message": "Internal server error"}')

    mock_response = FetchMetaMockResponse(response_code=200, fail_count=2)

    # failing 2 times, it must succeed on 3rd time
    executor, _ = HubIO.fetch_meta('dummy_mwu_encoder', tag=None, force=True)
    assert executor.uuid == 'dummy_mwu_encoder'

    assert mock.call_count == 6  # mock must be called 3+3


def test_fetch_with_authorization(mocker, monkeypatch):
    mock = mocker.Mock()

    def _mock_post(url, json, headers):
        mock(url=url, json=json, headers=headers)
        return FetchMetaMockResponse(response_code=200)

    monkeypatch.setattr(requests, 'post', _mock_post)

    HubIO.fetch_meta('dummy_mwu_encoder', tag=None, force=True)

    assert mock.call_count == 1

    _, kwargs = mock.call_args_list[0]

    assert kwargs['headers'].get('Authorization').startswith('token ')


class DownloadMockResponse:
    def __init__(self, response_code: int = 200):
        self.response_code = response_code

    def iter_content(self, buffer=32 * 1024):
        zip_file = Path(__file__).parent / 'dummy_executor.zip'
        with zip_file.open('rb') as f:
            yield f.read(buffer)

    @property
    def status_code(self):
        return self.response_code


@pytest.mark.parametrize('executor_name', ['alias_dummy', None])
@pytest.mark.parametrize('build_env', [['DOWNLOAD', 'DOMAIN'], None])
def test_pull(mocker, monkeypatch, executor_name, build_env):
    mock = mocker.Mock()

    def _mock_fetch(
        name,
        tag=None,
        secret=None,
        image_required=True,
        rebuild_image=True,
        force=False,
        build_env=build_env,
    ):
        mock(name=name)
        return (
            HubExecutor(
                uuid='dummy_mwu_encoder',
                name=executor_name,
                tag='v0',
                image_name='jinahub/pod.dummy_mwu_encoder',
                md5sum=None,
                visibility=True,
                archive_url=None,
                build_env=build_env,
            ),
            False,
        )

    monkeypatch.setattr(HubIO, 'fetch_meta', _mock_fetch)

    def _mock_download(url, stream=True, headers=None):
        mock(url=url)
        return DownloadMockResponse(response_code=200)

    def _mock_head(url):
        from collections import namedtuple

        HeadInfo = namedtuple('HeadInfo', ['headers'])
        return HeadInfo(headers={})

    monkeypatch.setattr(requests, 'get', _mock_download)
    monkeypatch.setattr(requests, 'head', _mock_head)

    def _mock_get_prettyprint_usage(self, console, executor_name, usage_kind=None):
        mock(console=console)
        mock(usage_kind=usage_kind)
        print('_mock_get_prettyprint_usage executor_name:', executor_name)
        assert executor_name != 'None'

    monkeypatch.setattr(HubIO, '_get_prettyprint_usage', _mock_get_prettyprint_usage)

    monkeypatch.setenv('DOWNLOAD', 'download')
    monkeypatch.setenv('DOMAIN', 'github.com')
    args = set_hub_pull_parser().parse_args(['jinahub://dummy_mwu_encoder'])
    HubIO(args).pull()

    args = set_hub_pull_parser().parse_args(['jinahub://dummy_mwu_encoder:secret'])
    HubIO(args).pull()


class MockDockerClient:
    def __init__(self, fail_pull: bool = True):
        self.fail_pull = fail_pull
        if not self.fail_pull:
            self.images = {}

    def pull(self, repository: str, stream: bool = True, decode: bool = True):
        if self.fail_pull:
            raise docker.errors.APIError('Failed pulling docker image')
        else:
            yield {}


def test_offline_pull(mocker, monkeypatch, tmpfile):
    mock = mocker.Mock()

    fail_meta_fetch = True
    version = 'v0'

    @disk_cache_offline(cache_file=str(tmpfile))
    def _mock_fetch(
        name,
        tag=None,
        secret=None,
        image_required=True,
        rebuild_image=True,
        force=False,
    ):
        mock(name=name)
        if fail_meta_fetch:
            raise urllib.error.URLError('Failed fetching meta')
        else:
            return HubExecutor(
                uuid='dummy_mwu_encoder',
                name='alias_dummy',
                tag='v0',
                image_name=f'jinahub/pod.dummy_mwu_encoder:{version}',
                md5sum=None,
                visibility=True,
                archive_url=None,
            )

    def _gen_load_docker_client(fail_pull: bool):
        def _load_docker_client(obj):
            obj._raw_client = MockDockerClient(fail_pull=fail_pull)
            obj._client = MockDockerClient(fail_pull=fail_pull)

        return _load_docker_client

    args = set_hub_pull_parser().parse_args(
        ['--force', 'jinahub+docker://dummy_mwu_encoder']
    )
    monkeypatch.setattr(
        HubIO, '_load_docker_client', _gen_load_docker_client(fail_pull=True)
    )
    monkeypatch.setattr(HubIO, 'fetch_meta', _mock_fetch)

    # Expect failure due to fetch_meta
    with pytest.raises(urllib.error.URLError):
        HubIO(args).pull()

    fail_meta_fetch = False
    # Expect failure due to image pull
    with pytest.raises(AttributeError):
        HubIO(args).pull()

    # expect successful pull
    monkeypatch.setattr(
        HubIO, '_load_docker_client', _gen_load_docker_client(fail_pull=False)
    )
    assert HubIO(args).pull() == 'docker://jinahub/pod.dummy_mwu_encoder:v0'

    version = 'v1'
    # expect successful forced pull because force == True
    assert HubIO(args).pull() == 'docker://jinahub/pod.dummy_mwu_encoder:v1'

    # expect successful pull using cached fetch_meta response and saved image
    fail_meta_fetch = True
    monkeypatch.setattr(
        HubIO, '_load_docker_client', _gen_load_docker_client(fail_pull=False)
    )
    assert HubIO(args).pull() == 'docker://jinahub/pod.dummy_mwu_encoder:v1'

    args.force_update = False
    fail_meta_fetch = False
    version = 'v2'
    # expect successful but outdated pull because force == False
    assert HubIO(args).pull() == 'docker://jinahub/pod.dummy_mwu_encoder:v1'


def test_pull_with_progress():
    import json

    args = set_hub_pull_parser().parse_args(['jinahub+docker://dummy_mwu_encoder'])

    def _log_stream_generator():
        with open(os.path.join(cur_dir, 'docker_pull.logs')) as fin:
            for line in fin:
                if line.strip():
                    yield json.loads(line)

    from rich.console import Console

    console = Console()
    HubIO(args)._pull_with_progress(_log_stream_generator(), console)


@pytest.mark.parametrize('add_dockerfile', ['cpu', 'torch-gpu', 'tf-gpu', 'jax-gpu'])
def test_new_without_arguments(monkeypatch, tmpdir, add_dockerfile):
    from rich.prompt import Confirm, Prompt

    prompts = iter(
        [
            'DummyExecutor',
            tmpdir / 'DummyExecutor',
            add_dockerfile,
            'dummy description',
            'dummy author',
            'dummy tags',
        ]
    )

    def _mock_prompt_ask(*args, **kwargs):
        return next(prompts)

    def _mock_confirm_ask(*args, **kwargs):
        return True

    monkeypatch.setattr(Confirm, 'ask', _mock_confirm_ask)
    monkeypatch.setattr(Prompt, 'ask', _mock_prompt_ask)

    args = set_hub_new_parser().parse_args([])
    HubIO(args).new()
    path = tmpdir / 'DummyExecutor'

    pkg_files = [
        'executor.py',
        'README.md',
        'requirements.txt',
        'config.yml',
    ]

    if add_dockerfile != 'none':
        pkg_files.append('Dockerfile')

    for file in pkg_files:
        assert (path / file).exists()
    for file in [
        'executor.py',
        'README.md',
        'config.yml',
    ]:
        with open(path / file, 'r') as fp:
            assert 'DummyExecutor' in fp.read()


@pytest.mark.parametrize('add_dockerfile', ['cpu', 'torch-gpu', 'tf-gpu', 'jax-gpu'])
@pytest.mark.parametrize('advance_configuration', [True, False])
@pytest.mark.parametrize('confirm_advance_configuration', [True, False])
@pytest.mark.parametrize('confirm_add_docker', [True, False])
def test_new_with_arguments(
    monkeypatch,
    tmpdir,
    add_dockerfile,
    advance_configuration,
    confirm_advance_configuration,
    confirm_add_docker,
):
    from rich.prompt import Confirm

    path = os.path.join(tmpdir, 'DummyExecutor')

    _args_list = [
        '--name',
        'argsExecutor',
        '--dockerfile',
        add_dockerfile,
        '--description',
        'args description',
        '--keywords',
        'args,keywords',
        '--url',
        'args url',
    ]
    temp = []
    _args_list.extend(['--path', path])
    if advance_configuration:
        _args_list.append('--advance-configuration')
    else:
        temp.append(confirm_advance_configuration)

    def _mock_confirm_ask(*args, **kwargs):
        return True

    monkeypatch.setattr(Confirm, 'ask', _mock_confirm_ask)

    args = set_hub_new_parser().parse_args(_args_list)

    HubIO(args).new()
    # path = tmpdir / 'argsExecutor'

    pkg_files = [
        'executor.py',
        'README.md',
        'requirements.txt',
        'config.yml',
    ]

    path = tmpdir / 'DummyExecutor'
    if (advance_configuration or confirm_advance_configuration) and (
        add_dockerfile or confirm_add_docker
    ):
        pkg_files.append('Dockerfile')

    for file in pkg_files:
        assert (path / file).exists()

    for file in ['executor.py', 'README.md', 'config.yml']:
        with open(path / file, 'r') as fp:
            assert 'argsExecutor' in fp.read()

    if advance_configuration or confirm_advance_configuration:
        with open(path / 'config.yml') as fp:
            temp = yaml.load(fp, Loader=yaml.FullLoader)
            assert temp['metas']['name'] == 'argsExecutor'
            assert temp['metas']['description'] == 'args description'
            assert temp['metas']['keywords'] == ['args', 'keywords']
            assert temp['metas']['url'] == 'args url'


class SandboxGetMockResponse:
    def __init__(self, response_code: int = 200):
        self.response_code = response_code

    def json(self):
        if self.response_code == 200:
            return {
                'code': self.response_code,
                'data': {'host': 'http://test_existing_deployment.com', 'port': 4321},
            }
        else:
            return {'code': self.response_code}

    @property
    def text(self):
        return json.dumps(self.json())

    @property
    def status_code(self):
        return self.response_code


class SandboxCreateMockResponse:
    def __init__(self, response_code: int = 200):
        self.response_code = response_code

    def json(self):
        return {
            'code': self.response_code,
            'data': {'host': 'http://test_new_deployment.com', 'port': 4322},
        }

    @property
    def text(self):
        return json.dumps(self.json())

    @property
    def status_code(self):
        return self.response_code


def test_deploy_public_sandbox_existing(mocker, monkeypatch):
    mock = mocker.Mock()

    def _mock_post(url, json, headers=None):
        mock(url=url, json=json)
        return SandboxGetMockResponse(response_code=200)

    monkeypatch.setattr(requests, "post", _mock_post)

    args = Namespace(
        uses='jinahub+sandbox://dummy_mwu_encoder:dummy_secret',
        uses_with={'foo': 'bar'},
        test_string='text',
        test_number=1,
    )
    host, port = HubIO.deploy_public_sandbox(args)
    assert host == 'http://test_existing_deployment.com'
    assert port == 4321

    _, kwargs = mock.call_args
    assert kwargs['json']['args'] == {
        'uses_with': {'foo': 'bar'},
        'test_number': 1,
        'test_string': 'text',
    }
    assert kwargs['json']['secret'] == 'dummy_secret'


def test_deploy_public_sandbox_create_new(mocker, monkeypatch):
    mock = mocker.Mock()

    def _mock_post(url, json, headers=None):
        mock(url=url, json=json)
        if url.endswith('/sandbox.get'):
            return SandboxGetMockResponse(response_code=404)
        else:
            return SandboxCreateMockResponse(response_code=requests.codes.created)

    monkeypatch.setattr(requests, 'post', _mock_post)

    args = Namespace(uses='jinahub+sandbox://dummy_mwu_encoder')
    host, port = HubIO.deploy_public_sandbox(args)
    assert host == 'http://test_new_deployment.com'
    assert port == 4322
