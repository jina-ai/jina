def get_full_schema() -> dict:
    """
    Return the full schema for Jina core as a dict.
    """
    from .. import __version__
    from ..importer import IMPORTED
    from .driver import schema_all_drivers
    from .executor import schema_all_executors
    from .flow import schema_flow
    from .meta import schema_metas
    from .request import schema_requests
    from .pod import schema_pod

    definitions = {}
    for s in [
        schema_all_drivers,
        schema_all_executors,
        schema_flow,
        schema_metas,
        schema_requests,
        schema_pod,
        IMPORTED.schema_executors,
        IMPORTED.schema_drivers,
    ]:
        definitions.update(s)

    # fix CompoundExecutor
    definitions['Jina::Executors::CompoundExecutor']['properties']['components'] = {
        '$ref': '#/definitions/Jina::Executors::All'
    }

    return {
        '$id': f'https://api.jina.ai/schemas/{__version__}.json',
        '$schema': 'http://json-schema.org/draft-07/schema#',
        'description': 'The YAML schema of Jina objects (Flow, Executor, Drivers).',
        'type': 'object',
        'oneOf': [{'$ref': '#/definitions/Jina::Flow'}]
        + [{"$ref": f"#/definitions/{k}"} for k in IMPORTED.schema_executors.keys()],
        'definitions': definitions,
    }
