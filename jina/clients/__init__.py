def py_client(**kwargs):
    from ..main.parser import set_client_cli_parser
    from ..helper import get_parsed_args
    from .python import PyClient
    _, args, _ = get_parsed_args(kwargs, set_client_cli_parser(), 'Client')
    return PyClient(args)
