from .helper import add_arg_group
from ..enums import RequestType


def mixin_client_cli_parser(parser):
    gp = add_arg_group(parser, title='Client')

    gp.add_argument('--request-size', type=int, default=100,
                    help='The number of Documents in each Request.')

    gp.add_argument('--mode', choices=list(RequestType), type=RequestType.from_string,
                    # required=True,
                    help='''
The Request mode. This applies to all Requests sent from this client.

* INDEX: store new Documents into the system
* SEARCH: query Documents from an indexed system
* UPDATE: update existing Documents in an indexed system
* DELETE: delete existing Documents from an indexed system
* CONTROL: (advance) control Pea/Pod such as shutdown, status
* TRAIN: (experimental) train the system
                    ''')
    gp.add_argument('--top-k', type=int,
                    help='The number of results will be returned. Sorted by their scores descendingly.')
    gp.add_argument('--mime-type', type=str,
                    help='MIME type of the input Documents.')
    gp.add_argument('--continue-on-error', action='store_true', default=False,
                    help='If set, a Request that causes error will be logged only without blocking the further requests.')
    gp.add_argument('--return-results', action='store_true', default=False,
                    help='''
This feature is only used for AsyncClient.

If set, the results of all Requests will be returned as a list. This is useful when one wants 
process Responses in bulk instead of using callback. 
                    ''')
