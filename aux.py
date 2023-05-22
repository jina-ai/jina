from typing import List, Dict, Any, Union, Type

from docarray import BaseDoc, DocList
from docarray.typing import AnyTensor
from jina.serve.runtimes.helper import _create_pydantic_model_from_schema


def _create_aux_model_doc_list_to_list(model):
    from pydantic import create_model
    fields = {}
    for field_name, field in model.__annotations__.items():
        print(f'{field_name} => {field}')
        try:
            if issubclass(field, DocList):
                fields[field_name] = (List[field.doc_type], {})
            else:
                fields[field_name] = (field, {})
        except TypeError as exc:
            print(f' TYPE ERROR: {exc}')
            fields[field_name] = (field, {})
    return create_model(model.__name__, __base__=model, __validators__=model.__validators__,
                        **fields)


def main():
    import numpy as np
    from typing import Type, Optional
    from docarray import BaseDoc, DocList
    from docarray.typing import AnyTensor, ImageUrl
    from docarray.documents import TextDoc, ImageDoc
    from docarray.documents.legacy import LegacyDocument

    class TextDocWithId(BaseDoc):
        ia: str

    class ResultTestDoc(BaseDoc):
        matches: DocList[TextDocWithId]

    class CustomDoc(BaseDoc):
        tensor: Optional[AnyTensor]
        url: ImageUrl
        lll: List[List[List[int]]] = [[[5]]]
        fff: List[List[List[float]]] = [[[5.2]]]
        single_text: TextDoc
        texts: DocList[TextDoc]
        d: Dict[str, str] = {'a': 'b'}
        u: Union[str, int]
        lu: List[Union[str, int]] = [0, 1, 2]
        # ud: Union[TextDoc, ImageDoc] = TextDoc(text='I am in union')

    TextDocWithIdCopy = _create_aux_model_doc_list_to_list(TextDocWithId)
    new_textdoc_with_id_model = _create_pydantic_model_from_schema(TextDocWithIdCopy.schema(), 'TextDocWithId', {})

    ResultTestDocCopy = _create_aux_model_doc_list_to_list(ResultTestDoc)
    new_result_test_doc_with_id_model = _create_pydantic_model_from_schema(ResultTestDocCopy.schema(), 'ResultTestDoc',
                                                                           {})

    CustomDocCopy = _create_aux_model_doc_list_to_list(CustomDoc)
    new_custom_doc_model = _create_pydantic_model_from_schema(CustomDocCopy.schema(), 'CustomDoc', {})

    original_custom_docs = DocList[CustomDoc]([CustomDoc(url='photo.jpg', lll=[[[40]]], fff=[[[40.2]]], d={'b': 'a'},
                                                         texts=DocList[TextDoc]
                                                         ([TextDoc(text='hey ha', embedding=np.zeros(3))]),
                                                         single_text=TextDoc(text='single hey ha',
                                                                             embedding=np.zeros(2)),
                                                         u='a',
                                                         lu=[3, 4], ud=TextDoc(text='I am in union'))])
    for doc in original_custom_docs:
        doc.tensor = np.zeros((10, 10, 10))
    print(DocList[new_custom_doc_model].from_protobuf(original_custom_docs.to_protobuf()).to_json())

    index_da = DocList[TextDocWithId](
        [TextDocWithId(ia=f'ID {i}') for i in range(10)]
    )

    print(DocList[new_textdoc_with_id_model].from_protobuf(index_da.to_protobuf()).to_json())

    result_test_docs = DocList[ResultTestDoc]([ResultTestDoc(matches=index_da)])
    print(DocList[new_result_test_doc_with_id_model].from_protobuf(result_test_docs.to_protobuf()).to_json())

    LegacyDocumentCopy = _create_aux_model_doc_list_to_list(LegacyDocument)
    legacy_document_model = _create_pydantic_model_from_schema(LegacyDocumentCopy.schema(), 'LegacyDocument', {})
    legacy = LegacyDocument(text='I am a chunk')
    legacy2 = LegacyDocument(text=' I am match')
    legacy_doclist = DocList[LegacyDocument]([LegacyDocument(text='ikhakah', chunks=DocList[LegacyDocument]([legacy]),
                                                             matches=DocList[LegacyDocument]([legacy2]))])
    print(DocList[legacy_document_model].from_protobuf(legacy_doclist.to_protobuf()).to_json())


if __name__ == '__main__':
    main()
