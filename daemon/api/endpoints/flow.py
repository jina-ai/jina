import uuid
from typing import List, Union, Dict

from fastapi import status, APIRouter, Body, Response, File, UploadFile
from fastapi.exceptions import HTTPException

from ...models import SinglePodModel, FlowModel
from ...stores import flow_store as store

router = APIRouter(prefix='/flow', tags=['flow'])


@router.get(
    path='/arguments',
    summary='Get all accept arguments of a Flow'
)
async def _fetch_flow_params():
    return FlowModel.schema()['properties']


@router.put(
    path='/from_pods',
    summary='Create a Flow from list of Pods',
    status_code=201
)
async def _create_from_pods(
        pods: Union[List[Dict]] = Body(..., example=[SinglePodModel()])
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
    try:
        return store.add(config=pods)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'{e!r}')


@router.put(
    path='/from_yaml',
    summary='Creat a Flow from a YAML config',
    status_code=201,
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
    try:
        return store.add(config=yamlspec.file, files=list(uses_files) + list(pymodules_files))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'{e!r}')


@router.delete(
    path='/{id}',
    summary='Terminate a running Flow',
    description='Terminate a running Flow and release its resources'
)
async def _delete(id: 'uuid.UUID'):
    try:
        del store[id]
    except KeyError:
        raise HTTPException(status_code=404, detail=f'{id} not found in {store!r}')


@router.on_event('shutdown')
def _shutdown():
    store.clear()


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
        with flow_store.session():
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
