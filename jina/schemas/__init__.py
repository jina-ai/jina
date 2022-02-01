def get_full_schema() -> dict:
    """Get full schema
    :return: the full schema for Jina core as a dict.
    """
    from jina import __version__
    from jina.importer import IMPORTED
    from jina.schemas.executor import schema_all_executors
    from jina.schemas.flow import schema_flow
    from jina.schemas.meta import schema_metas
    from jina.schemas.deployment import schema_deployment

    definitions = {}
    for s in [
        schema_all_executors,
        schema_flow,
        schema_metas,
        schema_deployment,
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
