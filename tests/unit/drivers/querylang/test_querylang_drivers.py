from google.protobuf import json_format

from jina.executors.crafters import BaseSegmenter
from jina.flow import Flow
from jina.proto import jina_pb2


def random_docs(num_docs):
    for j in range(num_docs):
        d = jina_pb2.DocumentProto()
        d.text = 'hello world'
        d.uri = 'doc://'
        d.tags['id'] = j
        for m in range(10):
            dm = d.matches.add()
            dm.text = 'match to other world'
            dm.uri = 'doc://match'
            dm.tags['id'] = m
        yield d


def random_docs_to_chunk():
    d1 = jina_pb2.DocumentProto()
    d1.tags['id'] = 1
    d1.text = 'chunk1 chunk2'
    yield d1
    d2 = jina_pb2.DocumentProto()
    d2.tags['id'] = 1
    d2.text = 'chunk3'
    yield d2


def random_docs_with_tags():
    d1 = jina_pb2.DocumentProto()
    d1.tags['id'] = 1
    d1.text = 'a'
    d1.tags.update({'id': 1})
    yield d1
    d2 = jina_pb2.DocumentProto()
    d2.tags['id'] = 2
    d2.tags.update({'id': 2})
    d2.text = 'b'
    yield d2


class DummySegmenter(BaseSegmenter):

    def craft(self, text, *args, **kwargs):
        return [{'text': 'adasd' * (j + 1), 'tags': {'id': j}} for j in range(10)]


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
        uses='- !SelectQL | {fields: [uri, matches, chunks], traversal_paths: [r, c, m]}'))

    with f:
        f.index(random_docs(10), output_fn=validate, callback_on='body')

    f = (Flow().add(uses='DummySegmenter')
         .add(uses='- !ExcludeQL | {fields: [text], traversal_paths: [r, c, m]}'))

    with f:
        f.index(random_docs(10), output_fn=validate, callback_on='body')


def test_sort_ql():
    def validate(req):
        assert req.docs[-1].tags['id'] < req.docs[0].tags['id']
        assert req.docs[0].matches[-1].tags['id'] < req.docs[0].matches[0].tags['id']
        assert req.docs[0].chunks[-1].tags['id'] < req.docs[0].chunks[0].tags['id']

    f = (Flow().add(uses='DummySegmenter')
        .add(
        uses='- !SortQL | {field: tags__id, reverse: true, traversal_paths: [r, c, m]}'))

    with f:
        f.index(random_docs(10), output_fn=validate, callback_on='body')

    f = (Flow().add(uses='DummySegmenter')
         .add(uses='- !SortQL | {field: tags__id, reverse: false, traversal_paths: [r, c, m]}')
         .add(uses='- !ReverseQL | {traversal_paths: [r, c, m]}'))

    with f:
        f.index(random_docs(10), output_fn=validate, callback_on='body')


def test_filter_ql():
    def validate(req):
        assert len(req.docs) == 1
        assert int(req.docs[0].tags['id']) == 2
        assert len(req.docs[0].matches) == 1
        assert int(req.docs[0].matches[0].tags['id']) == 2

    f = (Flow().add(uses='DummySegmenter')
        .add(
        uses='- !FilterQL | {lookups: {tags__id: 2}, traversal_paths: [r, c, m]}'))

    with f:
        f.index(random_docs(10), output_fn=validate, callback_on='body')


def test_filter_ql_in_tags():
    def validate(req):
        assert len(req.docs) == 1
        assert int(req.docs[0].tags['id']) == 2
        assert json_format.MessageToDict(req.docs[0].tags)['id'] == 2

    f = (Flow().add(
        uses='- !FilterQL | {lookups: {tags__id: 2}, traversal_paths: [r, c, m]}'))

    with f:
        f.index(random_docs_with_tags(), output_fn=validate, callback_on='body')


def test_filter_ql_modality_wrong_depth():
    def validate(req):
        # since no doc has modality mode2 they are all erased from the list of docs
        assert len(req.docs) == 0

    f = (Flow().add(uses='DummyModeIdSegmenter')
        .add(
        uses='- !FilterQL | {lookups: {modality: mode2}, traversal_paths: [r, c, m]}'))

    with f:
        f.index(random_docs_to_chunk(), output_fn=validate, callback_on='body')


def test_filter_ql_modality():
    def validate(req):
        # docs are not filtered, so 2 docs are returned, but only the chunk at depth1 with modality mode2 is returned
        assert len(req.docs) == 2
        assert len(req.docs[0].chunks) == 1
        assert len(req.docs[1].chunks) == 0

    f = (Flow().add(uses='DummyModeIdSegmenter')
        .add(
        uses='- !FilterQL | {lookups: {modality: mode2}, traversal_paths: [c]}'))

    with f:
        f.index(random_docs_to_chunk(), output_fn=validate, callback_on='body')


def test_filter_compose_ql():
    def validate(req):
        assert len(req.docs) == 1
        assert int(req.docs[0].tags['id']) == 2
        assert len(req.docs[0].matches) == 0  # matches do not contain "hello"

    f = (Flow().add(uses='DummySegmenter')
        .add(
        uses='- !FilterQL | {lookups: {tags__id: 2, text__contains: hello}, traversal_paths: [r, c, m]}'))

    with f:
        f.index(random_docs(10), output_fn=validate, callback_on='body')
