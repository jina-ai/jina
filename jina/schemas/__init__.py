def get_full_schema() -> dict:
    """Get full schema
    :return: the full schema for Jina core as a dict.
    """
    from .. import __version__
    from ..importer import IMPORTED
    from .executor import schema_all_executors
    from .flow import schema_flow
    from .meta import schema_metas
    from .pod import schema_pod

    definitions = {}
    for s in [
        schema_all_executors,
        schema_flow,
        schema_metas,
        schema_pod,
        IMPORTED.schema_executors,
    ]:
        definitions.update(s)

    return {
        '$id': f'https://api.jina.ai/schemas/{__version__}.json',
        '$schema': 'http://json-schema.org/draft-07/schema#',
        'description': 'The YAML schema of Jina objects (Flow, Executor).',
        'type': 'object',
        'oneOf': [{'$ref': '#/definitions/Jina::Flow'}]
        + [{"$ref": f"#/definitions/{k}"} for k in IMPORTED.schema_executors.keys()],
        'definitions': definitions,
    }
