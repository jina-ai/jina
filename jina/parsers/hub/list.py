from ..helper import add_arg_group


def mixin_hub_list_parser(parser):
    gp = add_arg_group(parser, title='List')
    gp.add_argument('--name', type=str,
                    help='name of hub image')
    gp.add_argument('--kind', type=str,
                    help='kind of hub image')
    gp.add_argument('--keywords', type=str, nargs='+', metavar='KEYWORD',
                    help='keywords for searching')
    gp.add_argument('--type', type=str, default='pod', choices=['pod', 'app'],
                    help='type of the hub image')
    gp.add_argument('--local-only', action='store_true', default=False,
                    help='list all local hub images on the current machine')
