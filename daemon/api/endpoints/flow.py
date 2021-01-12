import json
import uuid
from typing import List, Union, Dict

from fastapi import status, APIRouter, Body, Response, File, UploadFile
from fastapi.exceptions import HTTPException

from jina.clients import Client
from jina.helper import ArgNamespace
from jina.parsers import set_client_cli_parser
from ...excepts import FlowYamlParseException, FlowCreationException, FlowStartException
from ...models import SinglePodModel
from ...store import flow_store

router = APIRouter()


@router.put(
    path='/flow/pods',
    summary='Start a Flow from list of Pods',
)
async def _create_from_pods(
        pods: Union[List[Dict]] = Body(..., example=json.loads(SinglePodModel().json()))
):
    """
    Build a Flow using a list of `SinglePodModel`

        [
            {
                "name": "pod1",
                "uses": "_pass"
            },
            {
                "name": "pod2",
                "uses": "_pass",
                "host": "10.18.3.127",
                "port_expose": 8000
            }
        ]
    """
    with flow_store._session():
        try:
            flow_id, host, port_expose = flow_store._create(config=pods)
        except FlowCreationException:
            raise HTTPException(status_code=404,
                                detail=f'Bad pods args')
        except FlowStartException:
            raise HTTPException(status_code=404,
                                detail=f'Flow couldn\'t get started')
    return {
        'status_code': status.HTTP_200_OK,
        'flow_id': flow_id,
        'host': host,
        'port': port_expose,
        'status': 'started'
    }


@router.put(
    path='/flow/yaml',
    summary='Start a Flow from a YAML config',
)
async def _create_from_yaml(
        yamlspec: UploadFile = File(...),
        uses_files: List[UploadFile] = File(()),
        pymodules_files: List[UploadFile] = File(())
):
    """
    Build a flow using [Flow YAML](https://docs.jina.ai/chapters/yaml/yaml.html#flow-yaml-sytanx)

    - Upload Flow yamlspec (`yamlspec`)
    - Yamls that Pods use (`uses_files`) (Optional)
    - Python modules (`pymodules_files`) that the Pods use (Optional)

    **yamlspec**:

        !Flow
        version: 1.0
        with:
            restful: true
        pods:
            - name: encode
              uses: helloworld.encoder.yml
              parallel: 2
            - name: index
              uses: helloworld.indexer.yml
              shards: 2
              separated_workspace: true

    **uses_files**: `helloworld.encoder.yml`

        !MyEncoder
        metas:
            name: myenc
            workspace: /tmp/blah
            py_modules: components.py
        requests:
            on:
                [IndexRequest, SearchRequest]:
                - !Blob2PngURI {}
                - !EncodeDriver {}
                - !ExcludeQL
                with:
                    fields:
                        - buffer
                        - chunks

    **uses_files**: `helloworld.indexer.yml`

        !CompoundIndexer
        components:
        - !NumpyIndexer
            with:
                index_filename: vec.gz
            metas:
                name: vecidx
                workspace: /tmp/blah
        - !BinaryPbIndexer
            with:
                index_filename: chunk.gz
            metas:
                name: chunkidx
                workspace: /tmp/blah
        metas:
            name: chunk_indexer
            workspace: /tmp/blah

    **pymodules_files**: `components.py`

        class MyEncoder(BaseImageEncoder):
            def __init__(self):
                ...

    """

    with flow_store._session():
        try:
            flow_id, host, port_expose = flow_store._create(config=yamlspec.file,
                                                            files=list(uses_files) + list(pymodules_files))
        except FlowYamlParseException:
            raise HTTPException(status_code=404,
                                detail=f'Invalid yaml file.')
        except FlowStartException as e:
            raise HTTPException(status_code=404,
                                detail=f'Flow couldn\'t get started:  {e!r}')

    return {
        'status_code': status.HTTP_200_OK,
        'flow_id': flow_id,
        'host': host,
        'port': port_expose,
        'status': 'started'
    }


@router.get(
    path='/flow/{flow_id}',
    summary='Get the status of a running Flow',
)
async def _fetch(
        flow_id: uuid.UUID,
        yaml_only: bool = False
):
    """
    Get Flow information using `flow_id`.

    Following details are sent:
    - Flow YAML
    - Gateway host
    - Gateway port
    """
    try:
        with flow_store._session():
            host, port_expose, yaml_spec = flow_store._get(flow_id=flow_id)

        if yaml_only:
            return Response(content=yaml_spec,
                            media_type='application/yaml')

        return {
            'status_code': status.HTTP_200_OK,
            'yaml': yaml_spec,
            'host': host,
            'port': port_expose
        }
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Flow ID {flow_id} not found! Please create a new Flow')


@router.get(
    path='/ping',
    summary='Check if the Flow is alive',
)
async def _ping(
        host: str,
        port: int
):
    """
    Ping to check if we can connect to gateway via gRPC `host:port`

    Note: Make sure Flow is running
    """
    kwargs = {'port_expose': port, 'host': host}
    _, args, _ = ArgNamespace.get_parsed_args(kwargs, set_client_cli_parser())
    client = Client(args)
    try:
        # TODO: this introduces side-effect, need to be refactored. (2020.01.10)
        client.index(input_fn=['abc'])
        return {
            'status_code': status.HTTP_200_OK,
            'detail': 'connected'
        }
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Cannot connect to GRPC Server on {host}:{port}')


@router.delete(
    path='/flow',
    summary='Terminate a running Flow',
)
async def _delete(
        flow_id: uuid.UUID
):
    """
    Close Flow Context
    """
    with flow_store._session():
        try:
            flow_store._delete(flow_id=flow_id)
            return {
                'status_code': status.HTTP_200_OK
            }
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Flow ID {flow_id} not found! Please create a new Flow')


@router.on_event('shutdown')
def _shutdown():
    with flow_store._session():
        flow_store._delete_all()
