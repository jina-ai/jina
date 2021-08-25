DEPRECATED_ARGS_MAPPING = {
    'override_with': 'uses_with',
    'override_metas': 'uses_metas',
    'override_requests': 'uses_requests',
    'port_expose': 'One of "port" (when starting JinaD or when starting a Client) or "port_jinad" (for a remote Pod)',
}


def get_deprecated_replacement(dep_arg: str) -> str:
    """Get the replacement of a deprecated argument

    :param dep_arg: the old dep arg
    :return: the new argument
    """
    normalized_arg = dep_arg.replace('--', '').replace('-', '_')
    if normalized_arg in DEPRECATED_ARGS_MAPPING:
        new_argument = DEPRECATED_ARGS_MAPPING[normalized_arg]
        if '-' in dep_arg:
            new_argument = new_argument.replace('_', '-')
        if dep_arg.startswith('--'):
            new_argument = '--' + new_argument
        elif dep_arg.startswith('-'):
            new_argument = '-' + new_argument
        return new_argument
