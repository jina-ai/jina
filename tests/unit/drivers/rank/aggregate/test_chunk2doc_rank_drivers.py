import pytest

from jina import Document
from jina.drivers.rank.aggregate import Chunk2DocRankDriver
from jina.executors.rankers import Chunk2DocRanker
from jina.types.score import NamedScore
from jina.types.arrays import DocumentArray

DISCOUNT_VAL = 0.5


class MockMaxRanker(Chunk2DocRanker):
    def score(self, match_idx, query_chunk_meta, match_chunk_meta, *args, **kwargs):
        return match_idx[self.COL_SCORE].max()


class MockMinRanker(Chunk2DocRanker):
    def score(self, match_idx, query_chunk_meta, match_chunk_meta, *args, **kwargs):
        return 1.0 / (1.0 + match_idx[self.COL_SCORE].min())


class MockLengthRanker(Chunk2DocRanker):
    def __init__(self, *args, **kwargs):
        super().__init__(
            query_required_keys=['weight'],
            match_required_keys=['weight'],
            *args,
            **kwargs,
        )

    def score(self, match_idx, query_chunk_meta, match_chunk_meta, *args, **kwargs):
        return match_chunk_meta[match_idx[0][self.COL_DOC_CHUNK_ID]]['weight']


class MockPriceDiscountRanker(Chunk2DocRanker):
    def __init__(self, *args, **kwargs):
        super().__init__(
            query_required_keys=('tags__price', 'tags__discount'),
            match_required_keys=('tags__price', 'tags__discount'),
            *args,
            **kwargs,
        )

    def score(self, match_idx, query_chunk_meta, match_chunk_meta, *args, **kwargs):
        price = match_chunk_meta[match_idx[0][self.COL_DOC_CHUNK_ID]]['tags__price']
        discount = match_chunk_meta[match_idx[0][self.COL_DOC_CHUNK_ID]][
            'tags__discount'
        ]
        return price - price * discount


class SimpleChunk2DocRankDriver(Chunk2DocRankDriver):
    def __init__(self, docs, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._docs = docs

    @property
    def exec_fn(self):
        return self._exec_fn

    @property
    def docs(self):
        return self._docs


def create_document_to_score():
    # doc: 1
    # |- chunk: 2
    # |  |- matches: (id: 4, parent_id: 40, score.value: 4),
    # |  |- matches: (id: 5, parent_id: 50, score.value: 5),
    # |
    # |- chunk: 3
    #    |- matches: (id: 6, parent_id: 60, score.value: 6),
    #    |- matches: (id: 7, parent_id: 70, score.value: 7)
    doc = Document()
    doc.id = '1'
    for c in range(2):
        chunk = Document()
        chunk_id = str(c + 2)
        chunk.id = chunk_id
        for m in range(2):
            match = Document()
            match_id = 2 * int(chunk_id) + m
            match.id = str(match_id)
            parent_id = 10 * int(match_id)
            match.parent_id = str(parent_id)
            # to be used by MaxRanker and MinRanker
            match.score = NamedScore(value=int(match_id), ref_id=chunk.id)
            match.tags['price'] = match.score.value
            match.tags['discount'] = DISCOUNT_VAL
            match.weight = 2 * int(chunk_id) + m
            chunk.matches.append(match)
        doc.chunks.append(chunk)
    return doc


def create_chunk_matches_to_score():
    # doc: (id: 100, granularity=0)
    # |- chunks: (id: 10)
    # |  |- matches: (id: 11, parent_id: 1, score.value: 2),
    # |  |- matches: (id: 12, parent_id: 1, score.value: 3),
    # |- chunks: (id: 20)
    #    |- matches: (id: 21, parent_id: 2, score.value: 4),
    #    |- matches: (id: 22, parent_id: 2, score.value: 5)
    doc = Document()
    doc.id = '1'
    doc.granularity = 0
    num_matches = 2
    for parent_id in range(1, 3):
        chunk = Document()
        chunk_id = parent_id * 10
        chunk.id = str(chunk_id)
        chunk.granularity = doc.granularity + 1
        for score_value in range(parent_id * 2, parent_id * 2 + num_matches):
            match = Document()
            match.granularity = chunk.granularity
            match.parent_id = str(parent_id)
            match.score = NamedScore(value=score_value, ref_id=chunk.id)
            match.id = str(10 * int(parent_id) + score_value)
            chunk.matches.append(match)
        doc.chunks.append(chunk)
    return doc


def create_chunk_chunk_matches_to_score():
    # doc: (id: 100, granularity=0)
    # |- chunk: (id: 101, granularity=1)
    #       |- chunks: (id: 10)
    #       |   |- matches: (id: 11, parent_id: 1, score.value: 2),
    #       |   |- matches: (id: 12, parent_id: 1, score.value: 3),
    #       |- chunks: (id: 20)
    #           |- matches: (id: 21, parent_id: 2, score.value: 4),
    #           |- matches: (id: 22, parent_id: 2, score.value: 5)
    doc = Document()
    doc.id = '100'
    doc.granularity = 0
    chunk = Document()
    chunk.id = '101'
    chunk.parent_id = doc.id
    chunk.granularity = doc.granularity + 1
    num_matches = 2
    for parent_id in range(1, 3):
        chunk_chunk = Document()
        chunk_chunk.id = str(parent_id * 10)
        chunk_chunk.parent_id = str(parent_id)
        chunk_chunk.granularity = chunk.granularity + 1
        for score_value in range(parent_id * 2, parent_id * 2 + num_matches):
            match = Document()
            match.parent_id = str(parent_id)
            match.score = NamedScore(value=score_value, ref_id=chunk_chunk.id)
            match.id = str(10 * parent_id + score_value)
            chunk_chunk.matches.append(match)
        chunk.chunks.append(chunk_chunk)
    doc.chunks.append(chunk)
    return Document(doc)


@pytest.mark.parametrize('keep_source_matches_as_chunks', [False, True])
def test_chunk2doc_ranker_driver_mock_ranker(keep_source_matches_as_chunks):
    doc = create_document_to_score()
    driver = SimpleChunk2DocRankDriver(
        docs=DocumentArray([doc]),
        keep_source_matches_as_chunks=keep_source_matches_as_chunks,
    )
    executor = MockLengthRanker()
    driver.attach(executor=executor, runtime=None)
    driver()
    assert len(doc.matches) == 4
    assert doc.matches[0].id == '70'
    assert doc.matches[0].score.value == 7
    assert doc.matches[1].id == '60'
    assert doc.matches[1].score.value == 6
    assert doc.matches[2].id == '50'
    assert doc.matches[2].score.value == 5
    assert doc.matches[3].id == '40'
    assert doc.matches[3].score.value == 4
    for match in doc.matches:
        # match score is computed w.r.t to doc.id
        assert match.score.ref_id == doc.id
        expected_chunk_matches_length = 1 if keep_source_matches_as_chunks else 0
        assert len(match.chunks) == expected_chunk_matches_length


@pytest.mark.parametrize('keep_source_matches_as_chunks', [False, True])
def test_chunk2doc_ranker_driver_max_ranker(keep_source_matches_as_chunks):
    doc = create_document_to_score()
    driver = SimpleChunk2DocRankDriver(
        docs=DocumentArray([doc]),
        keep_source_matches_as_chunks=keep_source_matches_as_chunks,
    )
    executor = MockMaxRanker()
    driver.attach(executor=executor, runtime=None)
    driver()
    scale = 1 if not isinstance(executor, MockPriceDiscountRanker) else DISCOUNT_VAL
    assert len(doc.matches) == 4
    assert doc.matches[0].id == '70'
    assert doc.matches[0].score.value == 7 * scale
    assert doc.matches[1].id == '60'
    assert doc.matches[1].score.value == 6 * scale
    assert doc.matches[2].id == '50'
    assert doc.matches[2].score.value == 5 * scale
    assert doc.matches[3].id == '40'
    assert doc.matches[3].score.value == 4 * scale
    for match in doc.matches:
        # match score is computed w.r.t to doc.id
        assert match.score.ref_id == doc.id
        expected_chunk_matches_length = 1 if keep_source_matches_as_chunks else 0
        assert len(match.chunks) == expected_chunk_matches_length


@pytest.mark.parametrize('keep_source_matches_as_chunks', [False, True])
def test_chunk2doc_ranker_driver_min_ranker(keep_source_matches_as_chunks):
    doc = create_document_to_score()
    driver = SimpleChunk2DocRankDriver(
        docs=DocumentArray([doc]),
        keep_source_matches_as_chunks=keep_source_matches_as_chunks,
    )
    executor = MockMinRanker()
    driver.attach(executor=executor, runtime=None)
    driver()
    assert len(doc.matches) == 4
    assert doc.matches[0].id == '40'
    assert doc.matches[0].score.value == pytest.approx(1 / (1 + 4), 0.0001)
    assert doc.matches[1].id == '50'
    assert doc.matches[1].score.value == pytest.approx(1 / (1 + 5), 0.0001)
    assert doc.matches[2].id == '60'
    assert doc.matches[2].score.value == pytest.approx(1 / (1 + 6), 0.0001)
    assert doc.matches[3].id == '70'
    assert doc.matches[3].score.value == pytest.approx(1 / (1 + 7), 0.0001)
    for match in doc.matches:
        # match score is computed w.r.t to doc.id
        assert match.score.ref_id == doc.id
        expected_chunk_matches_length = 1 if keep_source_matches_as_chunks else 0
        assert len(match.chunks) == expected_chunk_matches_length


@pytest.mark.parametrize('keep_source_matches_as_chunks', [False, True])
def test_chunk2doc_ranker_driver_traverse_apply(keep_source_matches_as_chunks):
    docs = [
        create_chunk_matches_to_score(),
    ]
    driver = SimpleChunk2DocRankDriver(
        docs=DocumentArray(docs),
        keep_source_matches_as_chunks=keep_source_matches_as_chunks,
    )
    executor = MockMinRanker()
    driver.attach(executor=executor, runtime=None)
    driver()
    for doc in docs:
        assert len(doc.matches) == 2
        for idx, match in enumerate(doc.matches):
            # the score should be 1 / (1 + id * 2)
            assert match.score.value == pytest.approx(
                1.0 / (1 + float(match.id[0]) * 2.0), 0.0001
            )
            expected_chunk_matches_length = 2 if keep_source_matches_as_chunks else 0
            assert len(match.chunks) == expected_chunk_matches_length


@pytest.mark.skip('TODO: https://github.com/jina-ai/jina/issues/1014')
def test_chunk2doc_ranker_driver_traverse_apply_larger_range():
    docs = [
        create_chunk_chunk_matches_to_score(),
    ]
    driver = SimpleChunk2DocRankDriver(
        traversal_paths=('cc', 'c'), docs=DocumentArray(docs)
    )
    executor = MockMinRanker()
    driver.attach(executor=executor, runtime=None)
    driver()
    for doc in docs:
        assert len(doc.matches) == 1
        assert len(doc.chunks) == 1
        chunk = doc.chunks[0]
        assert len(chunk.matches) == 2
        min_granularity_2 = chunk.matches[0].score.value
        for idx, m in enumerate(chunk.matches):
            # the score should be 1 / (1 + id * 2)
            if m.score.value < min_granularity_2:
                min_granularity_2 = m.score.value
            assert m.score.value == pytest.approx(1.0 / (1 + float(m.id) * 2.0), 0.0001)
            assert m.score.ref_id == 101
        match = doc.matches[0]
        assert match.score.ref_id == 100
        assert match.score.value == pytest.approx(1.0 / (1 + min_granularity_2), 0.0001)
