from ..helper import add_arg_group


def mixin_hub_new_parser(parser):
    gp = add_arg_group(parser, title='Create')

    gp.add_argument('--output-dir', type=str, default='.',
                    help='where to output the generated project dir into.')
    gp.add_argument('--template', type=str, default='https://github.com/jina-ai/cookiecutter-jina-hub.git',
                    help='The cookiecutter template directory containing a project template directory, or a URL to a git repository. Only used when "--type template"')
    gp.add_argument('--type', type=str, default='pod', choices=['pod', 'app', 'template'],
                    help='The template type for executor hub pod or app using cookiecutter.')
    gp.add_argument('--overwrite', action='store_true', default=False,
                    help='overwrite the contents of output directory if it exists')
