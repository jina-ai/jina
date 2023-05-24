from typing import Any, Dict, List, Optional, Tuple, Union
from unittest.mock import Mock

import pytest

from jina.serve.helper import get_default_grpc_options
from jina.serve.runtimes.helper import (
    _get_name_from_replicas_name,
    _is_param_for_specific_executor,
    _parse_specific_params,
    _spit_key_and_executor_name,
)
from jina._docarray import docarray_v2


@pytest.mark.parametrize(
    'key_name,is_specific',
    [
        ('key', False),
        ('key_1', False),
        ('executor__key', True),
        ('exec2__key_2', True),
        ('__results__', False),
        ('__banana__', False),
    ],
)
def test_is_specific_executor(key_name, is_specific):
    assert _is_param_for_specific_executor(key_name) == is_specific


@pytest.mark.parametrize(
    'full_key,key , executor',
    [
        ('executor__key', 'key', 'executor'),
        ('executor__key_1', 'key_1', 'executor'),
        ('executor_1__key', 'key', 'executor_1'),
    ],
)
def test_split_key_executor_name(full_key, key, executor):
    assert _spit_key_and_executor_name(full_key) == (key, executor)


@pytest.mark.parametrize(
    'param, parsed_param, executor_name',
    [
        (
                {'key': 1, 'executor__key': 2, 'wrong_executor__key': 3},
                {'key': 2},
                'executor',
        ),
        ({'executor__key': 2, 'wrong_executor__key': 3}, {'key': 2}, 'executor'),
        (
                {'a': 1, 'executor__key': 2, 'wrong_executor__key': 3},
                {'key': 2, 'a': 1},
                'executor',
        ),
        ({'key_1': 0, 'exec2__key_2': 1}, {'key_1': 0}, 'executor'),
    ],
)
def test_parse_specific_param(param, parsed_param, executor_name):
    assert _parse_specific_params(param, executor_name) == parsed_param


@pytest.mark.parametrize(
    'name_w_replicas,name', [('exec1/rep-0', 'exec1'), ('exec1', 'exec1')]
)
def test_get_name_from_replicas(name_w_replicas, name):
    assert _get_name_from_replicas_name(name_w_replicas) == name


def _custom_grpc_options(
        call_recording_mock: Mock,
        additional_options: Optional[Union[list, Dict[str, Any]]] = None,
) -> List[Tuple[str, Any]]:
    call_recording_mock()
    expected_grpc_option_keys = [
        'grpc.max_send_message_length',
        'grpc.keepalive_time_ms',
    ]

    if not additional_options:
        raise RuntimeError()
    if all([key not in additional_options.keys() for key in expected_grpc_option_keys]):
        raise RuntimeError()

    return get_default_grpc_options()


@pytest.mark.parametrize('transformation', ['proto', 'json'])
@pytest.mark.skipif(not docarray_v2, reason='Test only working with docarray v2')
def test_create_pydantic_model_from_schema(transformation):
    from jina.serve.runtimes.helper import _create_aux_model_doc_list_to_list, _create_pydantic_model_from_schema
    import numpy as np
    from typing import Optional
    from docarray import BaseDoc, DocList
    from docarray.typing import AnyTensor, ImageUrl
    from docarray.documents import TextDoc

    class CustomDoc(BaseDoc):
        tensor: Optional[AnyTensor]
        url: ImageUrl
        lll: List[List[List[int]]] = [[[5]]]
        fff: List[List[List[float]]] = [[[5.2]]]
        single_text: TextDoc
        texts: DocList[TextDoc]
        d: Dict[str, str] = {'a': 'b'}
        di: Optional[Dict[str, int]] = None
        u: Union[str, int]
        lu: List[Union[str, int]] = [0, 1, 2]
        tags: Optional[Dict[str, Any]] = None

    CustomDocCopy = _create_aux_model_doc_list_to_list(CustomDoc)
    new_custom_doc_model = _create_pydantic_model_from_schema(CustomDocCopy.schema(), 'CustomDoc', {})

    original_custom_docs = DocList[CustomDoc]([CustomDoc(url='photo.jpg', lll=[[[40]]], fff=[[[40.2]]], d={'b': 'a'},
                                                         texts=DocList[TextDoc]
                                                         ([TextDoc(text='hey ha', embedding=np.zeros(3))]),
                                                         single_text=TextDoc(text='single hey ha',
                                                                             embedding=np.zeros(2)),
                                                         u='a',
                                                         lu=[3, 4])])
    for doc in original_custom_docs:
        doc.tensor = np.zeros((10, 10, 10))
        doc.di = {'a': 2}

    if transformation == 'proto':
        custom_partial_da = DocList[new_custom_doc_model].from_protobuf(original_custom_docs.to_protobuf())
        original_back = DocList[CustomDoc].from_protobuf(custom_partial_da.to_protobuf())
    elif transformation == 'json':
        custom_partial_da = DocList[new_custom_doc_model].from_json(original_custom_docs.to_json())
        original_back = DocList[CustomDoc].from_json(custom_partial_da.to_json())

    assert len(custom_partial_da) == 1
    assert custom_partial_da[0].url == 'photo.jpg'
    assert custom_partial_da[0].lll == [[[40]]]
    assert custom_partial_da[0].lu == ['3', '4']  # Union validates back to string
    assert custom_partial_da[0].fff == [[[40.2]]]
    assert custom_partial_da[0].di == {'a': 2}
    assert custom_partial_da[0].d == {'b': 'a'}
    assert len(custom_partial_da[0].texts) == 1
    assert custom_partial_da[0].texts[0].text == 'hey ha'
    assert custom_partial_da[0].texts[0].embedding.shape == (3,)
    assert custom_partial_da[0].tensor.shape == (10, 10, 10)
    assert custom_partial_da[0].u == 'a'
    assert custom_partial_da[0].single_text.text == 'single hey ha'
    assert custom_partial_da[0].single_text.embedding.shape == (2,)

    assert len(original_back) == 1
    assert original_back[0].url == 'photo.jpg'
    assert original_back[0].lll == [[[40]]]
    assert original_back[0].lu == ['3', '4']  # Union validates back to string
    assert original_back[0].fff == [[[40.2]]]
    assert original_back[0].di == {'a': 2}
    assert original_back[0].d == {'b': 'a'}
    assert len(original_back[0].texts) == 1
    assert original_back[0].texts[0].text == 'hey ha'
    assert original_back[0].texts[0].embedding.shape == (3,)
    assert original_back[0].tensor.shape == (10, 10, 10)
    assert original_back[0].u == 'a'
    assert original_back[0].single_text.text == 'single hey ha'
    assert original_back[0].single_text.embedding.shape == (2,)

    class TextDocWithId(BaseDoc):
        ia: str

    TextDocWithIdCopy = _create_aux_model_doc_list_to_list(TextDocWithId)
    new_textdoc_with_id_model = _create_pydantic_model_from_schema(TextDocWithIdCopy.schema(), 'TextDocWithId', {})

    original_text_doc_with_id = DocList[TextDocWithId](
        [TextDocWithId(ia=f'ID {i}') for i in range(10)]
    )
    if transformation == 'proto':
        custom_da = DocList[new_textdoc_with_id_model].from_protobuf(original_text_doc_with_id.to_protobuf())
        original_back = DocList[TextDocWithId].from_protobuf(custom_da.to_protobuf())
    elif transformation == 'json':
        custom_da = DocList[new_textdoc_with_id_model].from_json(original_text_doc_with_id.to_json())
        original_back = DocList[TextDocWithId].from_json(custom_da.to_json())

    assert len(custom_da) == 10
    for i, doc in enumerate(custom_da):
        assert doc.ia == f'ID {i}'

    assert len(original_back) == 10
    for i, doc in enumerate(original_back):
        assert doc.ia == f'ID {i}'

    class ResultTestDoc(BaseDoc):
        matches: DocList[TextDocWithId]

    ResultTestDocCopy = _create_aux_model_doc_list_to_list(ResultTestDoc)
    new_result_test_doc_with_id_model = _create_pydantic_model_from_schema(ResultTestDocCopy.schema(), 'ResultTestDoc',
                                                                           {})
    result_test_docs = DocList[ResultTestDoc]([ResultTestDoc(matches=original_text_doc_with_id)])

    if transformation == 'proto':
        custom_da = DocList[new_result_test_doc_with_id_model].from_protobuf(result_test_docs.to_protobuf())
        original_back = DocList[ResultTestDoc].from_protobuf(custom_da.to_protobuf())
    elif transformation == 'json':
        custom_da = DocList[new_result_test_doc_with_id_model].from_json(result_test_docs.to_json())
        original_back = DocList[ResultTestDoc].from_json(custom_da.to_json())

    assert len(custom_da) == 1
    assert len(custom_da[0].matches) == 10
    for i, doc in enumerate(custom_da[0].matches):
        assert doc.ia == f'ID {i}'

    assert len(original_back) == 1
    assert len(original_back[0].matches) == 10
    for i, doc in enumerate(original_back[0].matches):
        assert doc.ia == f'ID {i}'


@pytest.mark.parametrize('transformation', ['proto', 'json'])
@pytest.mark.skipif(not docarray_v2, reason='Test only working with docarray v2')
def test_create_empty_doc_list_from_schema(transformation):
    from jina.serve.runtimes.helper import _create_aux_model_doc_list_to_list, _create_pydantic_model_from_schema
    from typing import Optional
    from docarray import BaseDoc, DocList
    from docarray.typing import AnyTensor, ImageUrl
    from docarray.documents import TextDoc

    class CustomDoc(BaseDoc):
        tensor: Optional[AnyTensor]
        url: ImageUrl
        lll: List[List[List[int]]] = [[[5]]]
        fff: List[List[List[float]]] = [[[5.2]]]
        single_text: TextDoc
        texts: DocList[TextDoc]
        d: Dict[str, str] = {'a': 'b'}
        di: Optional[Dict[str, int]] = None
        u: Union[str, int]
        lu: List[Union[str, int]] = [0, 1, 2]
        tags: Optional[Dict[str, Any]] = None

    CustomDocCopy = _create_aux_model_doc_list_to_list(CustomDoc)
    new_custom_doc_model = _create_pydantic_model_from_schema(CustomDocCopy.schema(), 'CustomDoc', {})

    original_custom_docs = DocList[CustomDoc]()
    if transformation == 'proto':
        custom_partial_da = DocList[new_custom_doc_model].from_protobuf(original_custom_docs.to_protobuf())
        original_back = DocList[CustomDoc].from_protobuf(custom_partial_da.to_protobuf())
    elif transformation == 'json':
        custom_partial_da = DocList[new_custom_doc_model].from_json(original_custom_docs.to_json())
        original_back = DocList[CustomDoc].from_json(custom_partial_da.to_json())

    assert len(custom_partial_da) == 0
    assert len(original_back) == 0

    class TextDocWithId(BaseDoc):
        ia: str

    TextDocWithIdCopy = _create_aux_model_doc_list_to_list(TextDocWithId)
    new_textdoc_with_id_model = _create_pydantic_model_from_schema(TextDocWithIdCopy.schema(), 'TextDocWithId', {})

    original_text_doc_with_id = DocList[TextDocWithId]()
    if transformation == 'proto':
        custom_da = DocList[new_textdoc_with_id_model].from_protobuf(original_text_doc_with_id.to_protobuf())
        original_back = DocList[TextDocWithId].from_protobuf(custom_da.to_protobuf())
    elif transformation == 'json':
        custom_da = DocList[new_textdoc_with_id_model].from_json(original_text_doc_with_id.to_json())
        original_back = DocList[TextDocWithId].from_json(custom_da.to_json())

    assert len(original_back) == 0
    assert len(custom_da) == 0

    class ResultTestDoc(BaseDoc):
        matches: DocList[TextDocWithId]

    ResultTestDocCopy = _create_aux_model_doc_list_to_list(ResultTestDoc)
    new_result_test_doc_with_id_model = _create_pydantic_model_from_schema(ResultTestDocCopy.schema(), 'ResultTestDoc',
                                                                           {})
    result_test_docs = DocList[ResultTestDoc]()

    if transformation == 'proto':
        custom_da = DocList[new_result_test_doc_with_id_model].from_protobuf(result_test_docs.to_protobuf())
        original_back = DocList[ResultTestDoc].from_protobuf(custom_da.to_protobuf())
    elif transformation == 'json':
        custom_da = DocList[new_result_test_doc_with_id_model].from_json(result_test_docs.to_json())
        original_back = DocList[ResultTestDoc].from_json(custom_da.to_json())

    assert len(original_back) == 0
    assert len(custom_da) == 0
