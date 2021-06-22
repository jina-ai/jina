from jina.types.document.generators import from_ndarray, from_ndjson

import numpy as np
import pytest


@pytest.mark.parametrize(
    'input_ndarray, shuffle',
    [(np.arange(12).reshape((3, 4)), True), (np.arange(1).reshape((1, 1)), True)],
)
def test_from_ndarray(input_ndarray, shuffle):
    docs = list(from_ndarray(input_ndarray, shuffle=shuffle))
    if shuffle:
        docs = sorted(docs, key=lambda x: x.blob[0])

    assert len(docs) == len(input_ndarray)
    for idx, doc in enumerate(docs):
        assert doc.content_type == 'blob'
        np.testing.assert_array_equal(doc.blob, input_ndarray[idx])
        np.testing.assert_array_equal(doc.content, input_ndarray[idx])

    docs = list(from_ndarray(input_ndarray, size=1))
    assert len(docs) == 1


@pytest.mark.parametrize(
    'input_dicts, field_resolver, content_types, content_keys, tags_list',
    [
        ([{'text': 'text'}], None, ['text'], ['text'], [[]]),
        (
            [{'text': 'text', 'text2': 'text2'}],
            {'text2': 'text'},
            ['text'],
            ['text2'],
            [[]],
        ),
        ([{'uri': 'https://github.com/jina-ai'}], None, ['uri'], ['uri'], [[]]),
        (
            [{'blob': np.arange(4).reshape((2, 2)).tolist()}],
            None,
            ['blob'],
            ['blob'],
            [[]],
        ),
        (
            [
                {
                    'text': 'text',
                    'tag_label_1': 'tag1',
                },
                {'uri': 'https://github.com/jina-ai', 'tag_label_2': 'tag2'},
                {'blob': np.arange(4).reshape((2, 2)).tolist(), 'tag_label_3': 'tag3'},
            ],
            None,
            ['text', 'uri', 'blob'],
            ['text', 'uri', 'blob'],
            [
                ['tag_label_1'],
                ['tag_label_2'],
                ['tag_label_3'],
            ],
        ),
    ],
)
def test_from_ndjson(
    input_dicts, field_resolver, content_types, content_keys, tags_list
):
    import json

    input_ndjson = [json.dumps(dict) for dict in input_dicts]
    docs = list(from_ndjson(input_ndjson, field_resolver=field_resolver))

    assert len(docs) == len(input_ndjson)
    for idx, doc in enumerate(docs):
        content_type = content_types[idx]
        content_key = content_keys[idx]
        np.testing.assert_equal(
            getattr(doc, content_type), input_dicts[idx][content_key]
        )
        np.testing.assert_equal(doc.content, input_dicts[idx][content_key])
        for tag_field in tags_list[idx]:
            assert doc.tags[tag_field] == input_dicts[idx][tag_field]
        assert doc.content_type == content_type

    docs = list(from_ndjson(input_ndjson, size=1))
    assert len(docs) == 1
