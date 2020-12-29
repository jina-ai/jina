from ..base import set_base_parser


def set_hub_new_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    parser.add_argument('--output-dir', type=str, default='.',
                        help='where to output the generated project dir into.')
    parser.add_argument('--template', type=str, default='https://github.com/jina-ai/cookiecutter-jina-hub.git',
                        help='cookiecutter template directory containing a project template directory, or a URL to a git repository. Only used when "--type template"')
    parser.add_argument('--type', type=str, default='pod', choices=['pod', 'app', 'template'],
                        help='create a template for executor hub pod or app using cookiecutter.')
    parser.add_argument('--overwrite', action='store_true', default=False,
                        help='overwrite the contents of output directory if it exists')
    return parser