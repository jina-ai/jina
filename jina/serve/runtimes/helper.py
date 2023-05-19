import copy
from typing import Dict, Tuple, List, Any, Union
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
    from jina._docarray import docarray_v2
    from docarray import DocList, BaseDoc
    from docarray.typing import AnyTensor


    def _get_field_from_type(field_schema, field_name, root_schema, cached_models, num_recursions=0):
        field_type = field_schema.get('type', None)
        if 'anyOf' in field_schema:
            any_of_types = []
            for any_of_schema in field_schema['anyOf']:
                if '$ref' in any_of_schema:
                    obj_ref = any_of_schema.get('$ref')
                    ref_name = obj_ref.split('/')[-1]
                    any_of_types.append(_create_pydantic_model_from_schema(root_schema['definitions'][ref_name], ref_name, cached_models=cached_models))
                else:
                    any_of_types.append(_get_field_from_type(any_of_schema, field_name, root_schema=root_schema, cached_models=cached_models, num_recursions=0)) # No Union of Lists
            ret = Union[tuple(any_of_types)]
            for rec in range(num_recursions):
                ret = List[ret]
        elif field_type == 'string':
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