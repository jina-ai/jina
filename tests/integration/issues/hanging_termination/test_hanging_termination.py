import os
from pathlib import Path

import numpy as np
import pytest

from jina import Flow, Document
from jina.clients import Client
from jina.logging.profile import TimeContext
from jina.parsers import set_client_cli_parser
from typing import Dict
from jina import DocumentArray, Executor, requests


class DumpExecutor(Executor):
    def __init__(self, dump_path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dump_path = dump_path

    @requests
    def dump(self, docs: DocumentArray, parameters: Dict, **kwargs):
        shards = int(parameters['shards'])
        dump_path = parameters.get('dump_path', self.dump_path)
        shard_size = len(docs) / shards
        os.makedirs(dump_path, exist_ok=True)
        for i in range(shards):
            dump_file = f'{dump_path}/{i}.ndjson'
            docs_to_be_dumped = docs[int(i * shard_size) : int((i + 1) * shard_size)]
            docs_to_be_dumped.save(dump_file)


class ErrorExecutor(Executor):
    @requests
    def dump(self, docs: DocumentArray, **kwargs):
        if len(docs) > 0:
            assert False


class ReloadExecutor(Executor):
    def __init__(self, dump_path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # backwards compatibility
        if dump_path is not None:
            shard_id = getattr(self.runtime_args, 'pea_id', None)
            shard_dump_path = os.path.join(dump_path, f'{shard_id}.ndjson')
            self._docs = DocumentArray.load(shard_dump_path)
        else:
            self._docs = DocumentArray()

    @requests
    def search(self, docs: DocumentArray, **kwargs):
        docs.clear()
        docs.extend(self._docs)


class MergeExecutor(Executor):
    @requests
    def merge(self, docs_matrix: DocumentArray, **kwargs):
        merged_docs = DocumentArray()
        for docs in docs_matrix:
            merged_docs.extend(docs)
        return merged_docs


def get_client(port):
    args = set_client_cli_parser().parse_args(
        ['--host', 'localhost', '--port', str(port)]
    )

    return Client(args)


def get_documents(count=10, emb_size=7):
    for i in range(count):
        yield Document(
            id=i,
            text=f'hello world {i}',
            embedding=np.random.random(emb_size),
            tags={'tag_field': f'tag data {i}'},
        )


def path_size(dump_path):
    dir_size = (
        sum(f.stat().st_size for f in Path(dump_path).glob('**/*') if f.is_file()) / 1e6
    )
    return dir_size


@pytest.mark.parametrize('shards', [5, 3, 1])
@pytest.mark.parametrize('nr_docs', [7])
@pytest.mark.parametrize('emb_size', [10])
def test_dump_reload(tmpdir, shards, nr_docs, emb_size, times_to_index=2):
    """showcases using replicas + dump + rolling update with independent clients"""

    with Flow().add(uses=DumpExecutor, name='dump_exec').add(
        uses=ErrorExecutor, name='error_exec'
    ) as flow_dump:
        merge_executor = MergeExecutor if shards > 1 else None
        with Flow().add(
            uses=ReloadExecutor,
            name='reload_exec',
            replicas=2,
            shards=shards,
            uses_after=merge_executor,
        ) as flow_reload:
            for run_number in range(times_to_index):
                dump_path = os.path.join(tmpdir, f'dump-{str(run_number)}')
                client_dbms = get_client(flow_dump.port_expose)
                client_query = get_client(flow_reload.port_expose)
                docs = list(
                    get_documents(
                        count=nr_docs * (run_number + 1),
                        emb_size=emb_size,
                    )
                )

                with TimeContext(f'### dumping {len(docs)} docs'):
                    client_dbms.post(
                        on='/dump',
                        inputs=docs,
                        target_executor='dump_exec',
                        parameters={'dump_path': dump_path, 'shards': shards},
                    )

                print(f'### dump path size: {path_size(dump_path)} MBs')

                with TimeContext(f'### rolling update on {len(docs)}'):
                    # flow object is used for ctrl requests
                    flow_reload.rolling_update(
                        'reload_exec', uses_with={'dump_path': dump_path}
                    )

                for i in range(5):
                    result = client_query.post(
                        on='/search', inputs=[Document()], return_results=True
                    )

                    assert len(docs) == len(result[0].docs)
