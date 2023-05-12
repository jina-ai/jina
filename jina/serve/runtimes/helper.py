import copy
from typing import Dict, Tuple
from jina._docarray import docarray_v2

_SPECIFIC_EXECUTOR_SEPARATOR = '__'


def _spit_key_and_executor_name(key_name: str) -> Tuple[str]:
    """Split a specific key into a key, name pair

    ex: 'key__my_executor' will be split into 'key', 'my_executor'

    :param key_name: key name of the param
    :return: return the split 'key', 'executor_name' for the key_name
    """
    key_split = key_name.split(_SPECIFIC_EXECUTOR_SEPARATOR)

    new_key_name = key_split.pop(-1)
    executor_name = ''.join(key_split)

    return new_key_name, executor_name


def _get_name_from_replicas_name(name: str) -> Tuple[str]:
    """return the original name without the replicas

    ex: 'exec1/rep-0' will be transform into 'exec1'

    :param name: name of the DataRequest
    :return: return the original name without the replicas
    """
    return name.split('/')[0]


def _is_param_for_specific_executor(key_name: str) -> bool:
    """Tell if a key is for a specific Executor

    ex: 'key' is for every Executor whereas 'my_executor__key' is only for 'my_executor'

    :param key_name: key name of the param
    :return: return True if key_name is for specific Executor, False otherwise
    """
    if _SPECIFIC_EXECUTOR_SEPARATOR in key_name:
        if key_name.startswith(_SPECIFIC_EXECUTOR_SEPARATOR) or key_name.endswith(
            _SPECIFIC_EXECUTOR_SEPARATOR
        ):
            return False
        return True
    else:
        return False


def _parse_specific_params(parameters: Dict, executor_name: str):
    """Parse the parameters dictionary to filter executor specific parameters

    :param parameters: dictionary container the parameters
    :param executor_name: name of the Executor
    :returns: the parsed parameters after applying filtering for the specific Executor
    """
    parsed_params = copy.deepcopy(parameters)

    for key in parameters:
        if _is_param_for_specific_executor(key):
            (
                key_name,
                key_executor_name,
            ) = _spit_key_and_executor_name(key)

            if key_executor_name == executor_name:
                parsed_params[key_name] = parameters[key]

            del parsed_params[key]

    specific_parameters = parameters.get(executor_name, None)
    if specific_parameters:
        parsed_params.update(**specific_parameters)

    return parsed_params


if docarray_v2:
    from docarray.base_doc import AnyDoc
    from jina._docarray import docarray_v2
    from docarray import DocList, BaseDoc

    def _create_pydantic_model_from_schema(schema: Dict[str, any], model_name: str) -> type:
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
                        field_type = DocList[_create_pydantic_model_from_schema(schema['definitions'][ref_name], ref_name)]
                    else:
                        field_type = DocList[_create_pydantic_model_from_schema(field_schema.get('items', {}), field_name)]
                else:
                    raise ValueError(f"Unknown array item type: {field_item_type} for field_name {field_name}")
            elif field_type == 'object' or field_type is None:
                # Check if object is a reference to definitions
                if 'additionalProperties' in field_schema:
                    additional_props = field_schema['additionalProperties']
                    if additional_props.get('type') == 'object':
                        field_type = Dict[str, _create_pydantic_model_from_schema(additional_props, field_name)]
                    else:
                        field_type = Dict[str, Any]
                else:
                    obj_ref = field_schema.get('$ref')
                    if obj_ref:
                        ref_name = obj_ref.split('/')[-1]
                        field_type = _create_pydantic_model_from_schema(schema['definitions'][ref_name], ref_name)
                    else:
                        field_type = _create_pydantic_model_from_schema(field_schema, field_name)
            else:
                raise ValueError(f"Unknown field type: {field_type} for field_name {field_name}")
            fields[field_name] = (field_type, field_schema.get('description'))
        return create_model(model_name, __base__=BaseDoc, **fields)