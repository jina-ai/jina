from ...base import set_base_parser
from ...helper import add_arg_group


def set_zed_runtime_parser(parser=None):
    if not parser:
        parser = set_base_parser()
    gp0 = add_arg_group(parser, 'ZEDRuntime arguments')
    gp0.add_argument('--uses', type=str, default='_pass',
                     help='the config of the executor, it could be '
                          '> a YAML file path, '
                          '> a supported executor\'s class name, '
                          '> one of "_clear", "_pass", "_logforward" '
                          '> the content of YAML config (must starts with "!")'
                          '> a docker image')  # pod(no use) -> pea
    gp0.add_argument('--py-modules', type=str, nargs='*', metavar='PATH',
                     help='the customized python modules need to be imported before loading the'
                          ' executor')