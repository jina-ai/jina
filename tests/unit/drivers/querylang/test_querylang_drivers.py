from jina.executors.crafters import BaseSegmenter
from jina.flow import Flow
from jina.proto import jina_pb2
from google.protobuf import json_format


def random_docs(num_docs):
    for j in range(num_docs):
        d = jina_pb2.Document()
        d.id = j
        d.text = 'hello world'
        d.uri = 'doc://'
        for m in range(10):
            dm = d.matches.add()
            dm.text = 'match to other world'
            dm.uri = 'doc://match'
            dm.id = m
            dm.score.ref_id = d.id
        yield d


def random_docs_to_chunk():
    d1 = jina_pb2.Document()
    d1.id = 1
    d1.text = 'chunk1 chunk2'
    yield d1
    d2 = jina_pb2.Document()
    d2.id = 1
    d2.text = 'chunk3'
    yield d2


def random_docs_with_tags():
    d1 = jina_pb2.Document()
    d1.id = 1
    d1.text = 'a'
    d1.tags.update({'id': 1})
    yield d1
    d2 = jina_pb2.Document()
    d2.id = 2
    d2.tags.update({'id': 2})
    d2.text = 'b'
    yield d2


class DummySegmenter(BaseSegmenter):

    def craft(self, text, *args, **kwargs):
        return [{'text': 'adasd' * (j + 1)} for j in range(10)]


class DummyModeIdSegmenter(BaseSegmenter):

    def craft(self, text, *args, **kwargs):
        if 'chunk3' not in text:
            return [{'text': f'chunk{j + 1}', 'modality': f'mode{j + 1}'} for j in range(2)]
        elif 'chunk3' in text:
            return [{'text': f'chunk3', 'modality': 'mode3'}]


def test_select_ql():
    def validate(req):
        assert req.docs[0].text == ''
        assert req.docs[-1].text == ''
        assert req.docs[0].matches[0].text == ''
        assert req.docs[0].chunks[0].text == ''

    f = (Flow().add(uses='DummySegmenter')
        .add(
        uses='- !SelectQL | {fields: [uri, matches, chunks], granularity_range: [0, 2], adjacency_range: [0, 2]}'))

    with f:
        f.index(random_docs(10), output_fn=validate, callback_on_body=True)

    f = (Flow().add(uses='DummySegmenter')
         .add(uses='- !ExcludeQL | {fields: [text], granularity_range: [0, 2], adjacency_range: [0, 2]}'))

    with f:
        f.index(random_docs(10), output_fn=validate, callback_on_body=True)


def test_sort_ql():
    def validate(req):
        assert req.docs[-1].id < req.docs[0].id
        assert req.docs[0].matches[-1].id < req.docs[0].matches[0].id
        assert req.docs[0].chunks[-1].id < req.docs[0].chunks[0].id

    f = (Flow().add(uses='DummySegmenter')
        .add(
        uses='- !SortQL | {field: id, reverse: true, granularity_range: [0, 2], adjacency_range: [0, 2]}'))

    with f:
        f.index(random_docs(10), output_fn=validate, callback_on_body=True)

    f = (Flow().add(uses='DummySegmenter')
         .add(
        uses='- !SortQL | {field: id, reverse: false, granularity_range: [0, 2], adjacency_range: [0, 2]}')
         .add(uses='- !ReverseQL | {granularity_range: [0, 2], adjacency_range: [0, 2]}'))

    with f:
        f.index(random_docs(10), output_fn=validate, callback_on_body=True)


def test_filter_ql():
    def validate(req):
        assert len(req.docs) == 1
        assert req.docs[0].id == 2
        assert len(req.docs[0].matches) == 1
        assert req.docs[0].matches[0].id == 2

    f = (Flow().add(uses='DummySegmenter')
        .add(
        uses='- !FilterQL | {lookups: {id: 2}, granularity_range: [0, 1], adjacency_range: [0, 1]}'))

    with f:
        f.index(random_docs(10), output_fn=validate, callback_on_body=True)


def test_filter_ql_in_tags():
    def validate(req):
        assert len(req.docs) == 1
        assert req.docs[0].id == 2
        assert json_format.MessageToDict(req.docs[0].tags)['id'] == 2

    f = (Flow().add(
        uses='- !FilterQL | {lookups: {tags__id: 2}}'))

    with f:
        f.index(random_docs_with_tags(), output_fn=validate, callback_on_body=True)


def test_filter_ql_modality_wrong_depth():
    def validate(req):
        # since no doc has modality mode2 they are all erased from the list of docs
        assert len(req.docs) == 0

    f = (Flow().add(uses='DummyModeIdSegmenter')
        .add(
        uses='- !FilterQL | {lookups: {modality: mode2}, granularity_range: [0, 1]}'))

    with f:
        f.index(random_docs_to_chunk(), output_fn=validate, callback_on_body=True)


def test_filter_ql_modality():
    def validate(req):
        # docs are not filtered, so 2 docs are returned, but only the chunk at depth1 with modality mode2 is returned
        assert len(req.docs) == 2
        assert len(req.docs[0].chunks) == 1
        assert len(req.docs[1].chunks) == 0

    f = (Flow().add(uses='DummyModeIdSegmenter')
        .add(
        uses='- !FilterQL | {lookups: {modality: mode2}, granularity_range: [1, 2]}'))

    with f:
        f.index(random_docs_to_chunk(), output_fn=validate, callback_on_body=True)


def test_filter_compose_ql():
    def validate(req):
        assert len(req.docs) == 1
        assert req.docs[0].id == 2
        assert len(req.docs[0].matches) == 0  # matches do not contain "hello"

    f = (Flow().add(uses='DummySegmenter')
        .add(
        uses='- !FilterQL | {lookups: {id: 2, text__contains: hello}, granularity_range: [0, 1], adjacency_range: [0, 1]}'))

    with f:
        f.index(random_docs(10), output_fn=validate, callback_on_body=True)
