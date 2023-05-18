from typing import Optional, List, Dict, Any
import numpy as np
from docarray import BaseDoc, DocList
from docarray.typing import AnyTensor, ImageUrl
from docarray.documents import TextDoc


def _get_field_from_type(field_schema, field_name, root_schema, cached_models, num_recursions=0):
    field_type = field_schema.get('type', None)
    if field_type == 'string':
        ret = str
        for rec in range(num_recursions):
            ret = List[ret]
    elif field_type == 'integer':
        ret = int
        for rec in range(num_recursions):
            ret = List[ret]
    elif field_type == 'number':
        if num_recursions <= 1:
            # This is a hack because AnyTensor is more generic than a simple List and it comes as simple List
            ret = AnyTensor
        else:
            ret = float
            for rec in range(num_recursions):
                ret = List[ret]
    elif field_type == 'boolean':
        ret = bool
        for rec in range(num_recursions):
            ret = List[ret]
    elif field_type == 'object' or field_type is None:
        if 'additionalProperties' in field_schema:  # handle Dictionaries
            additional_props = field_schema['additionalProperties']
            if additional_props.get('type') == 'object':
                ret = Dict[str, _create_pydantic_model_from_schema(additional_props, field_name, cached_models=cached_models)]
            else:
                ret = Dict[str, Any]
        else:
            obj_ref = field_schema.get('$ref')
            if num_recursions == 0:  # single object reference
                if obj_ref:
                    ref_name = obj_ref.split('/')[-1]
                    ret = _create_pydantic_model_from_schema(root_schema['definitions'][ref_name], ref_name, cached_models=cached_models)
                else:
                    ret = _create_pydantic_model_from_schema(field_schema, field_name, cached_models=cached_models)
            else:  # object reference in definitions
                if obj_ref:
                    ref_name = obj_ref.split('/')[-1]
                    ret = DocList[_create_pydantic_model_from_schema(root_schema['definitions'][ref_name], ref_name, cached_models=cached_models)]
                else:
                    ret = DocList[_create_pydantic_model_from_schema(field_schema, field_name, cached_models=cached_models)]
    elif field_type == 'array':
        ret = _get_field_from_type(field_schema=field_schema.get('items', {}), field_name=field_name,
                                   root_schema=root_schema, cached_models=cached_models, num_recursions=num_recursions + 1)
    else:
        if num_recursions > 0:
            raise ValueError(f"Unknown array item type: {field_type} for field_name {field_name}")
        else:
            raise ValueError(f"Unknown field type: {field_type} for field_name {field_name}")
    return ret


def _create_pydantic_model_from_schema(schema: Dict[str, any], model_name: str, cached_models: Dict) -> type:
    from pydantic import create_model
    fields = {}
    if model_name in cached_models:
        return cached_models[model_name]
    for field_name, field_schema in schema.get('properties', {}).items():
        field_type = _get_field_from_type(field_schema=field_schema, field_name=field_name, root_schema=schema, cached_models=cached_models, num_recursions=0)
        fields[field_name] = (field_type, field_schema.get('description'))

    model = create_model(model_name, __base__=BaseDoc, **fields)
    cached_models[model_name] = model
    return model


class CustomDoc(BaseDoc):
    tensor: Optional[AnyTensor]
    url: ImageUrl
    lll: List[List[List[int]]] = [[[5]]]
    fff: List[List[List[float]]] = [[[5.2]]]
    single_text: TextDoc
    texts: DocList[TextDoc]
    d: Dict[str, str] = {'a': 'b'}


#
original_docs = DocList[CustomDoc]([CustomDoc(url='photo.jpg', lll=[[[40]]], fff=[[[40.2]]], d={'b': 'a'},
                                              texts=DocList[TextDoc]([TextDoc(text='hey ha', embedding=np.zeros(3))]),
                                              single_text=TextDoc(text='single hey ha', embedding=np.zeros(2)))])

new_model = _create_pydantic_model_from_schema(CustomDoc.schema(), 'CustomDoc', {})

for doc in original_docs:
    doc.tensor = np.zeros((10, 10, 10))

b = DocList[CustomDoc].from_protobuf(original_docs.to_protobuf())
#
print(b.to_json())
c = DocList[new_model].from_protobuf(original_docs.to_protobuf())
print(c.to_json())
#
