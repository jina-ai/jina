from jina._docarray import docarray_v2

if docarray_v2:

    from typing import Dict, List, Optional
    from typing_inspect import get_origin, get_args

    from docarray import DocList, BaseDoc


    def create_pydantic_model_from_schema(schema: Dict[str, any], model_name: str) -> type:
        from pydantic import create_model
        fields = {}
        for field_name, field_schema in schema.get('properties', {}).items():
            field_type = field_schema.get('type', None)
            if field_type == 'string':
                field_type = str
            elif field_type == 'integer':
                field_type = int
            elif field_type == 'number':
                field_type = float
            elif field_type == 'boolean':
                field_type = bool
            elif field_type == 'array':
                field_item_type = field_schema.get('items', {}).get('type', None)
                if field_item_type == 'string':
                    field_type = List[str]
                elif field_item_type == 'integer':
                    field_type = List[int]
                elif field_item_type == 'number':
                    field_type = List[float]
                elif field_item_type == 'boolean':
                    field_type = List[bool]
                elif field_item_type == 'object' or field_item_type is None:
                    # Check if array items are references to definitions
                    items_ref = field_schema.get('items', {}).get('$ref')
                    if items_ref:
                        ref_name = items_ref.split('/')[-1]
                        field_type = DocList[create_pydantic_model_from_schema(schema['definitions'][ref_name], ref_name)]
                    else:
                        field_type = DocList[create_pydantic_model_from_schema(field_schema.get('items', {}), field_name)]
                else:
                    raise ValueError(f"Unknown array item type: {field_item_type} for field_name {field_name}")
            elif field_type == 'object' or field_type is None:
                # Check if object is a reference to definitions
                obj_ref = field_schema.get('$ref')
                if obj_ref:
                    ref_name = obj_ref.split('/')[-1]
                    field_type = create_pydantic_model_from_schema(schema['definitions'][ref_name], ref_name)
                else:
                    field_type = create_pydantic_model_from_schema(field_schema, field_name)
            else:
                raise ValueError(f"Unknown field type: {field_type} for field_name {field_name}")
            fields[field_name] = (field_type, field_schema.get('description'))
        return create_model(model_name, __base__=BaseDoc, **fields)


    def merge(doc1, doc2, model):
        """
        merge doc1 with the content of doc2. Changes are applied to doc1.
        Updating one Document with another consists in the following:

         - Setting data properties of the second Document to the first Document
         if they are not None
         - Concatenating lists and updating sets
         - Updating recursively Documents and DocLists
         - Updating Dictionaries of the left with the right

        It behaves as an update operation for Dictionaries, except that since
        it is applied to a static schema type, the presence of the field is
        given by the field not having a None value and that DocLists,
        lists and sets are concatenated. It is worth mentioning that Tuples
        are not merged together since they are meant to be immutable,
        so they behave as regular types and the value of `self` is updated
        with the value of `other`.

        :param doc1: The Document with which to update the contents of this
        :param doc2: The Document with which to update the contents of this
        """
        if type(doc1) != type(doc2):
            raise Exception(
                f'Update operation can only be applied to '
                f'Documents of the same type. '
                f'Trying to update Document of type '
                f'{type(doc1)} with Document of type '
                f'{type(doc2)}'
            )
        from collections import namedtuple

        from docarray import DocList
        from docarray.utils.reduce import reduce

        # Declaring namedtuple()
        _FieldGroups = namedtuple(
            '_FieldGroups',
            [
                'simple_non_empty_fields',
                'list_fields',
                'set_fields',
                'dict_fields',
                'nested_docarray_fields',
                'nested_docs_fields',
            ],
        )

        FORBIDDEN_FIELDS_TO_UPDATE = ['ID', 'id']

        def _group_fields(doc) -> _FieldGroups:
            simple_non_empty_fields: List[str] = []
            list_fields: List[str] = []
            set_fields: List[str] = []
            dict_fields: List[str] = []
            nested_docs_fields: List[str] = []
            nested_docarray_fields: List[str] = []

            for field_name, field in model.__fields__.items():
                if field_name not in FORBIDDEN_FIELDS_TO_UPDATE:
                    field_type = field.type_
                    if get_origin(field_type) is type(None):
                        field_type = get_args(field_type)[0]

                    if isinstance(field_type, type) and issubclass(field_type, DocList):
                        nested_docarray_fields.append(field_name)
                    else:
                        origin = get_origin(field_type)
                        if origin is list:
                            list_fields.append(field_name)
                        elif origin is set:
                            set_fields.append(field_name)
                        elif origin is dict:
                            dict_fields.append(field_name)
                        else:
                            v = getattr(doc, field_name)
                            if v:
                                if isinstance(v, doc.__class__):
                                    nested_docs_fields.append(field_name)
                                else:
                                    simple_non_empty_fields.append(field_name)
            return _FieldGroups(
                simple_non_empty_fields,
                list_fields,
                set_fields,
                dict_fields,
                nested_docarray_fields,
                nested_docs_fields,
            )

        doc1_fields = _group_fields(doc1)
        doc2_fields = _group_fields(doc2)

        for field in doc2_fields.simple_non_empty_fields:
            setattr(doc1, field, getattr(doc2, field))

        for field in set(
                doc1_fields.nested_docs_fields + doc2_fields.nested_docs_fields
        ):
            sub_doc_1 = getattr(doc1, field)
            sub_doc_2 = getattr(doc2, field)
            sub_doc_1.update(sub_doc_2)
            setattr(doc1, field, sub_doc_1)

        for field in set(doc1_fields.list_fields + doc2_fields.list_fields):
            array1 = getattr(doc1, field)
            array2 = getattr(doc2, field)
            if array1 is None and array2 is not None:
                setattr(doc1, field, array2)
            elif array1 is not None and array2 is not None:
                array1.extend(array2)
                setattr(doc1, field, array1)

        for field in set(doc1_fields.set_fields + doc2_fields.set_fields):
            array1 = getattr(doc1, field)
            array2 = getattr(doc2, field)
            if array1 is None and array2 is not None:
                setattr(doc1, field, array2)
            elif array1 is not None and array2 is not None:
                array1.update(array2)
                setattr(doc1, field, array1)

        for field in set(
                doc1_fields.nested_docarray_fields + doc2_fields.nested_docarray_fields
        ):
            array1 = getattr(doc1, field)
            array2 = getattr(doc2, field)
            if array1 is None and array2 is not None:
                setattr(doc1, field, array2)
            elif array1 is not None and array2 is not None:
                reduce(array1, array2)

        for field in set(doc1_fields.dict_fields + doc2_fields.dict_fields):
            dict1 = getattr(doc1, field)
            dict2 = getattr(doc2, field)
            if dict1 is None and dict2 is not None:
                setattr(doc1, field, dict2)
            elif dict1 is not None and dict2 is not None:
                dict1.update(dict2)
                setattr(doc1, field, dict1)


    def reduce(
            left: DocList, right: DocList, model, left_id_map: Optional[Dict] = None
    ) -> 'DocList':
        """
        Reduces left and right DocList into one DocList in-place.
        Changes are applied to the left DocList.
        Reducing 2 DocLists consists in adding Documents in the second DocList
        to the first DocList if they do not exist.
        If a Document exists in both DocLists (identified by ID),
        the data properties are merged with priority to the left Document.

        Nested DocLists are also reduced in the same way.
        :param left: First DocList to be reduced. Changes will be applied to it
        in-place
        :param right: Second DocList to be reduced
        :param left_id_map: Optional parameter to be passed in repeated calls
        for optimizations, keeping a map of the Document ID to its offset
        in the DocList
        :return: Reduced DocList
        """
        left_id_map = left_id_map or {doc.id: i for i, doc in enumerate(left)}
        for doc in right:
            if doc.id in left_id_map:
                merge(left[left_id_map[doc.id]], doc, model)
            else:
                left.append(doc)

        return left


    def reduce_all(docs: List[DocList], model) -> DocList:
        """
        Reduces a list of DocLists into one DocList.
        Changes are applied to the first DocList in-place.

        The resulting DocList contains Documents of all DocLists.
        If a Document exists (identified by their ID) in many DocLists,
        data properties are merged with priority to the left-most
        DocLists (that is, if a data attribute is set in a Document
        belonging to many DocLists, the attribute value of the left-most
         DocList is kept).
        Nested DocLists belonging to many DocLists
         are also reduced in the same way.

        !!! note

            - Nested DocLists order does not follow any specific rule.
            You might want to re-sort them in a later step.
            - The final result depends on the order of DocLists
            when applying reduction.

        :param docs: List of DocLists to be reduced
        :return: the resulting DocList
        """
        if len(docs) <= 1:
            raise Exception(
                'In order to reduce DocLists' ' we should have more than one DocList'
            )
        left = docs[0]
        others = docs[1:]
        left_id_map = {doc.id: i for i, doc in enumerate(left)}
        for other_docs in others:
            reduce(left, other_docs, model, left_id_map)
        return left
