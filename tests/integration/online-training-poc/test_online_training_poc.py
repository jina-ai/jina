import os
import time

import pytest

import numpy as np

from typing import Sequence, Dict, Optional

from jina.jaml import JAMLCompatible
from jina.logging import JinaLogger
from jina.executors.rankers import Match2DocRanker
from jina.drivers import BaseExecutableDriver
from jina.flow import Flow
from jina import Document
from tests import validate_callback

cur_dir = os.path.dirname(os.path.abspath(__file__))


class TrainDriver(BaseExecutableDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(method='train', *args, **kwargs)

    def __call__(self, *args, **kwargs) -> None:
        self.exec_fn()


class DumpTrainDriver(BaseExecutableDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(method='dump', *args, **kwargs)

    def __call__(self, *args, **kwargs) -> None:
        self.exec_fn(path=self.req.path)


class LoadFromTrainDriver(BaseExecutableDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(method='load_from_dump', *args, **kwargs)

    def __call__(self, *args, **kwargs) -> None:
        self.exec_fn(path=self.req.path)


# it only inherits BaseExecutor to guarantee is discovered by jina
class RankerTrainer(JAMLCompatible):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = JinaLogger(self.__class__.__name__)
        self.current_output = 0

    def train(self, *args, **kwargs):
        self.logger.warning('f I am being trained')
        time.sleep(1)
        self.current_output += 1

    def dump(self, path, *args, **kwargs):
        self.logger.warning(f'dumping in path {path}')
        with open(path, 'w') as f:
            f.write(str(self.current_output))


class TrainableRanker(Match2DocRanker):
    def __init__(
        self,
        score_output: float,
        trainer: Optional[RankerTrainer] = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.trainer = trainer
        self.score_output = score_output
        self.match_required_keys = ['text']
        self.query_required_keys = ['text']

    def train(self, *args, **kwargs) -> None:
        self.trainer.train()

    def load_from_dump(self, path, *args, **kwargs):
        self.logger.warning(f'reloading from path {path}')
        with open(path, 'r') as f:
            self.score_output = float(f.read())

    def dump(self, path, *args, **kwargs):
        self.trainer.dump(path=path)

    def score(
        self,
        old_matches_scores: Sequence[Sequence[float]],
        queries_metas: Sequence[Dict],
        matches_metas: Sequence[Sequence[Dict]],
    ) -> Sequence[Sequence[float]]:
        ret = []
        for queries, matches in zip(queries_metas, matches_metas):
            r = []
            if matches:
                for _ in matches:
                    r.append(self.score_output)
            else:
                r.append(self.score_output)
            ret.append(r)
        return ret


@pytest.fixture
def tmp_workspace(tmpdir):
    os.environ['JINA_ONLINE_TRAINING_POC'] = str(tmpdir)
    yield
    del os.environ['JINA_ONLINE_TRAINING_POC']


@pytest.fixture
def dump_path(tmpdir):
    path = os.path.join(str(tmpdir), 'training_dump.txt')
    return path


def test_poc_online_training(tmp_workspace, dump_path, mocker):
    index_docs = [
        Document(text=f'text-{i}', embedding=np.array([i] * 5)) for i in range(100)
    ]
    with Flow.load_config(os.path.join(cur_dir, 'flow-index.yml')) as f:
        f.index(inputs=index_docs)

    def validate_evaluation_before_training(resp):
        assert len(resp.search.docs) == 1
        for doc in resp.search.docs:
            assert len(doc.matches) == 2
            for match in doc.matches:
                assert match.score.value == 0

    def validate_evaluation_after_training(resp):
        assert len(resp.search.docs) == 1
        for doc in resp.search.docs:
            assert len(doc.matches) == 2
            for match in doc.matches:
                assert match.score.value == 2

    mock_pre_train = mocker.Mock()
    mock_after_train = mocker.Mock()

    with Flow.load_config(os.path.join(cur_dir, 'flow-query.yml')) as f:
        f.search(inputs=index_docs[0:1], on_done=mock_pre_train, top_k=2)
        f.train(inputs=index_docs[0:1], top_k=2)
        f.train(inputs=index_docs[0:1], top_k=2)
        f.end_training(path=dump_path)
        # f.load_from_training(path=dump_path)
        f.search(inputs=index_docs[0:1], on_done=mock_after_train, top_k=2)

    mock_pre_train.assert_called_once()
    mock_after_train.assert_called_once()
    validate_callback(mock_pre_train, validate_evaluation_before_training)
    validate_callback(mock_after_train, validate_evaluation_after_training)
