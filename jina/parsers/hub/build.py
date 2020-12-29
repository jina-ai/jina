from ..helper import add_arg_group
from ...enums import BuildTestLevel


def mixin_hub_build_parser(parser):
    gp = add_arg_group(parser, title='Build')
    gp.add_argument('path', type=str, help='path to the directory containing '
                                           'Dockerfile, manifest.yml, README.md '
                                           'zero or more yaml config, '
                                           'zero or more Python file. '
                                           'All files in this directory will be shipped into a Docker image')
    gp.add_argument('--pull', action='store_true', default=False,
                    help='downloads any updates to the FROM image in Dockerfiles')
    gp.add_argument('--push', action='store_true', default=False,
                    help='push the built image to the registry')
    gp.add_argument('--dry-run', action='store_true', default=False,
                    help='only check path and validility, no real building')
    gp.add_argument('--prune-images', action='store_true', default=False,
                    help='prune unused images after building, this often saves disk space')
    gp.add_argument('--raise-error', action='store_true', default=False,
                    help='raise any error and exit with code 1')
    gp.add_argument('--test-uses', action='store_true', default=False,
                    help='after the build, test the image in "uses" with different level')
    gp.add_argument('--test-level', type=BuildTestLevel.from_string,
                    choices=list(BuildTestLevel), default=BuildTestLevel.FLOW,
                    help='the test level when "test-uses" is set, "NONE" means no test')
    gp.add_argument('--timeout-ready', type=int, default=10000,
                    help='timeout (ms) to give for the Pod to start before considering a test failed')
    gp.add_argument('--host-info', action='store_true', default=False,
                    help='store the host information during bookkeeping')
    gp.add_argument('--daemon', action='store_true', default=False,
                    help='run the test Pea/Pod as a daemon process, see "jina pea --help" for details')
    gp.add_argument('--no-overwrite', action='store_true', default=False,
                    help='Do not allow overwriting existing images (based on module version and jina version)')
