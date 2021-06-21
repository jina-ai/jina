import pydantic
import pytest
from jina.peapods.runtimes.asyncio.http.models import (
    PROTO_TO_PYDANTIC_MODELS,
    JinaRequestModel,
)
from jina.types.document import Document
from tests import random_docs


def test_schema_invocation():
    for k, v in vars(PROTO_TO_PYDANTIC_MODELS).items():
        v.schema()
        v.schema_json()


def test_existing_definitions():
    """This tests: all internal schema definitions are part of parent"""
    for i in [
        'QuantizationMode',
        'DenseNdArrayProto',
        'SparseNdArrayProto',
        'NdArrayProto',
        'NamedScoreProto',
        'DocumentProto',
    ]:
        assert (
            i in PROTO_TO_PYDANTIC_MODELS.DocumentProto().schema()['definitions'].keys()
        )


def test_enum_definitions():
    """This tests: all enums are defined properly as different levels"""
    quantization_enum_definition = PROTO_TO_PYDANTIC_MODELS.DocumentProto().schema()[
        'definitions'
    ]['QuantizationMode']
    assert quantization_enum_definition['enum'] == [0, 1, 2]

    status_code_enum_definition = PROTO_TO_PYDANTIC_MODELS.StatusProto().schema()[
        'definitions'
    ]['StatusCode']
    assert status_code_enum_definition['enum'] == [0, 1, 2, 3, 4, 5, 6]

    command_enum_definition = PROTO_TO_PYDANTIC_MODELS.RequestProto().schema()[
        'definitions'
    ]['Command']
    assert command_enum_definition['enum'] == [0, 1, 2, 3, 4, 5, 6]


def test_all_fields_in_document_proto():
    """This tests: all fields are picked from the proto definition"""
    document_proto_properties = PROTO_TO_PYDANTIC_MODELS.DocumentProto().schema(
        by_alias=False
    )['definitions']['DocumentProto']['properties']
    for i in [
        'id',
        'content_hash',
        'granularity',
        'adjacency',
        'parent_id',
        'chunks',
        'weight',
        'matches',
        'mime_type',
        'uri',
        'tags',
        'location',
        'offset',
        'embedding',
        'scores',
        'modality',
        'evaluations',
    ]:
        assert i in document_proto_properties

    document_proto_properties_alias = PROTO_TO_PYDANTIC_MODELS.DocumentProto().schema()[
        'definitions'
    ]['DocumentProto']['properties']
    for i in ['contentHash', 'parentId', 'mimeType']:
        assert i in document_proto_properties_alias


def test_oneof_text():
    """This tests: oneof field is correctly represented as `anyOf`"""

    doc = PROTO_TO_PYDANTIC_MODELS.DocumentProto(text='abc')
    assert doc.text == 'abc'
    assert 'blob' not in doc.dict()
    assert 'buffer' not in doc.dict()


def test_oneof_buffer():
    """This tests: oneof field is correctly represented as `anyOf`"""

    doc = PROTO_TO_PYDANTIC_MODELS.DocumentProto(buffer=b'abc')
    assert doc.buffer == b'abc'
    assert 'text' not in doc.dict()
    assert 'blob' not in doc.dict()


def test_oneof_blob():
    """This tests: oneof field is correctly represented as `anyOf`"""

    doc = PROTO_TO_PYDANTIC_MODELS.DocumentProto(
        blob=PROTO_TO_PYDANTIC_MODELS.NdArrayProto()
    )
    assert doc.blob == PROTO_TO_PYDANTIC_MODELS.NdArrayProto()
    assert 'text' not in doc.dict()
    assert 'buffer' not in doc.dict()


def test_oneof_validation_error():
    """This tests validation error for invalid fields"""

    with pytest.raises(pydantic.error_wrappers.ValidationError) as error:
        doc = PROTO_TO_PYDANTIC_MODELS.DocumentProto(text='abc', buffer=b'abc')
    assert "only one field among ['buffer', 'blob', 'text', 'uri', 'graph']" in str(
        error.value
    )

    with pytest.raises(pydantic.error_wrappers.ValidationError) as error:
        doc = PROTO_TO_PYDANTIC_MODELS.DocumentProto(
            text='abc', buffer=b'abc', blob=PROTO_TO_PYDANTIC_MODELS.NdArrayProto()
        )
    assert "only one field among ['buffer', 'blob', 'text', 'uri', 'graph']" in str(
        error.value
    )


def test_tags_document():
    doc = PROTO_TO_PYDANTIC_MODELS.DocumentProto(hello='world')
    assert doc.tags == {'hello': 'world'}
    assert Document(doc.dict()).tags == {'hello': 'world'}

    doc = PROTO_TO_PYDANTIC_MODELS.DocumentProto(hello='world', tags={'key': 'value'})
    assert doc.tags == {'hello': 'world', 'key': 'value'}
    assert Document(doc.dict()).tags == {
        'hello': 'world',
        'key': 'value',
    }

    doc = PROTO_TO_PYDANTIC_MODELS.DocumentProto(
        hello='world', tags={'key': {'nested': 'value'}}
    )
    assert doc.tags == {'hello': 'world', 'key': {'nested': 'value'}}
    assert Document(doc.dict()).tags == {
        'hello': 'world',
        'key': {'nested': 'value'},
    }

    doc = PROTO_TO_PYDANTIC_MODELS.DocumentProto(hello='world', tags={'key': [1, 2, 3]})

    # TODO: Issue about having proper ListValueView, not really expected
    assert doc.tags != {'key': [1, 2, 3]}
    with pytest.raises(TypeError):
        assert Document(doc.dict()).tags != {{'key': [1, 2, 3]}}


def test_repeated():
    """This tests: repeated fields are represented as `array`"""
    assert (
        PROTO_TO_PYDANTIC_MODELS.DenseNdArrayProto().schema()['properties']['shape'][
            'type'
        ]
        == 'array'
    )
    assert (
        PROTO_TO_PYDANTIC_MODELS.NamedScoreProto().schema()['definitions'][
            'NamedScoreProto'
        ]['properties']['operands']['type']
        == 'array'
    )
    assert (
        PROTO_TO_PYDANTIC_MODELS.DocumentProto().schema()['definitions'][
            'DocumentProto'
        ]['properties']['chunks']['type']
        == 'array'
    )


def test_recursive_schema():
    """This tests: recursive schmea definions are represented properly"""
    assert PROTO_TO_PYDANTIC_MODELS.NamedScoreProto().schema()['definitions'][
        'NamedScoreProto'
    ]['properties']['operands']['items'] == {'$ref': '#/definitions/NamedScoreProto'}


def test_struct():
    """This tests: google.protobuf.Struct are represented as `object`"""
    assert (
        PROTO_TO_PYDANTIC_MODELS.DocumentProto().schema()['definitions'][
            'DocumentProto'
        ]['properties']['tags']['type']
        == 'object'
    )


def test_timestamp():
    """This tests: google.protobuf.Timestamp are represented as date-time"""
    assert (
        PROTO_TO_PYDANTIC_MODELS.RouteProto().schema(by_alias=False)['properties'][
            'start_time'
        ]['type']
        == 'string'
    )
    assert (
        PROTO_TO_PYDANTIC_MODELS.RouteProto().schema(by_alias=False)['properties'][
            'start_time'
        ]['format']
        == 'date-time'
    )


def test_jina_document_to_pydantic_document():
    document_proto_model = PROTO_TO_PYDANTIC_MODELS.DocumentProto

    for jina_doc in random_docs(num_docs=10):
        jina_doc = jina_doc.dict()
        pydantic_doc = document_proto_model(**jina_doc)

        assert jina_doc['text'] == pydantic_doc.text
        assert jina_doc['mime_type'] == pydantic_doc.mime_type
        assert jina_doc['content_hash'] == pydantic_doc.content_hash
        assert (
            jina_doc['embedding']['dense']['shape']
            == pydantic_doc.embedding.dense.shape
        )
        assert (
            jina_doc['embedding']['dense']['dtype']
            == pydantic_doc.embedding.dense.dtype
        )

        for jina_doc_chunk, pydantic_doc_chunk in zip(
            jina_doc['chunks'], pydantic_doc.chunks
        ):
            assert jina_doc_chunk['id'] == pydantic_doc_chunk.id
            assert jina_doc_chunk['tags'] == pydantic_doc_chunk.tags
            assert jina_doc_chunk['text'] == pydantic_doc_chunk.text
            assert jina_doc_chunk['mime_type'] == pydantic_doc_chunk.mime_type
            assert jina_doc_chunk['parent_id'] == pydantic_doc_chunk.parent_id
            assert jina_doc_chunk['granularity'] == pydantic_doc_chunk.granularity
            assert jina_doc_chunk['content_hash'] == pydantic_doc_chunk.content_hash


def test_jina_document_to_pydantic_document_sparse():
    document_proto_model = PROTO_TO_PYDANTIC_MODELS.DocumentProto

    for jina_doc in random_docs(num_docs=10, sparse_embedding=True):
        jina_doc = jina_doc.dict()
        pydantic_doc = document_proto_model(**jina_doc)

        assert jina_doc['text'] == pydantic_doc.text
        assert jina_doc['mime_type'] == pydantic_doc.mime_type
        assert jina_doc['content_hash'] == pydantic_doc.content_hash
        assert (
            jina_doc['embedding']['sparse']['indices']['buffer']
            == pydantic_doc.embedding.sparse.indices.buffer.decode()
        )
        assert (
            jina_doc['embedding']['sparse']['indices']['shape']
            == pydantic_doc.embedding.sparse.indices.shape
        )
        assert (
            jina_doc['embedding']['sparse']['indices']['dtype']
            == pydantic_doc.embedding.sparse.indices.dtype
        )
        assert (
            jina_doc['embedding']['sparse']['values']['buffer']
            == pydantic_doc.embedding.sparse.values.buffer.decode()
        )
        assert (
            jina_doc['embedding']['sparse']['values']['shape']
            == pydantic_doc.embedding.sparse.values.shape
        )
        assert (
            jina_doc['embedding']['sparse']['values']['dtype']
            == pydantic_doc.embedding.sparse.values.dtype
        )

        for jina_doc_chunk, pydantic_doc_chunk in zip(
            jina_doc['chunks'], pydantic_doc.chunks
        ):
            assert jina_doc_chunk['id'] == pydantic_doc_chunk.id
            assert jina_doc_chunk['tags'] == pydantic_doc_chunk.tags
            assert jina_doc_chunk['text'] == pydantic_doc_chunk.text
            assert jina_doc_chunk['mime_type'] == pydantic_doc_chunk.mime_type
            assert jina_doc_chunk['parent_id'] == pydantic_doc_chunk.parent_id
            assert jina_doc_chunk['granularity'] == pydantic_doc_chunk.granularity
            assert jina_doc_chunk['content_hash'] == pydantic_doc_chunk.content_hash


def test_pydatic_document_to_jina_document():
    document_proto_model = PROTO_TO_PYDANTIC_MODELS.DocumentProto

    jina_doc = Document(document_proto_model(text='abc').json())
    assert jina_doc.text == 'abc'
    assert jina_doc.content == 'abc'

    jina_doc = Document(document_proto_model(text='abc').dict())
    assert jina_doc.text == 'abc'
    assert jina_doc.content == 'abc'


@pytest.mark.parametrize('top_k', [5, 10])
def test_model_with_top_k(top_k):
    m = JinaRequestModel(data=['abc'], parameters={'top_k': top_k})
    assert m.parameters['top_k'] == top_k

    m = JinaRequestModel(parameters={'top_k': top_k})
    assert m.parameters['top_k'] == top_k
