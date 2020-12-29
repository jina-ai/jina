from .login import set_hub_login_parser
from ..base import set_base_parser
from ...enums import BuildTestLevel


def set_hub_build_parser(parser=None):
    if not parser:
        parser = set_base_parser()

    set_hub_login_parser(parser)

    parser.add_argument('path', type=str, help='path to the directory containing '
                                               'Dockerfile, manifest.yml, README.md '
                                               'zero or more yaml config, '
                                               'zero or more Python file. '
                                               'All files in this directory will be shipped into a Docker image')
    parser.add_argument('--pull', action='store_true', default=False,
                        help='downloads any updates to the FROM image in Dockerfiles')
    parser.add_argument('--push', action='store_true', default=False,
                        help='push the built image to the registry')
    parser.add_argument('--dry-run', action='store_true', default=False,
                        help='only check path and validility, no real building')
    parser.add_argument('--prune-images', action='store_true', default=False,
                        help='prune unused images after building, this often saves disk space')
    parser.add_argument('--raise-error', action='store_true', default=False,
                        help='raise any error and exit with code 1')
    parser.add_argument('--test-uses', action='store_true', default=False,
                        help='after the build, test the image in "uses" with different level')
    parser.add_argument('--test-level', type=BuildTestLevel.from_string,
                        choices=list(BuildTestLevel), default=BuildTestLevel.FLOW,
                        help='the test level when "test-uses" is set, "NONE" means no test')
    parser.add_argument('--timeout-ready', type=int, default=10000,
                        help='timeout (ms) to give for the Pod to start before considering a test failed')
    parser.add_argument('--host-info', action='store_true', default=False,
                        help='store the host information during bookkeeping')
    parser.add_argument('--daemon', action='store_true', default=False,
                        help='run the test Pea/Pod as a daemon process, see "jina pea --help" for details')
    parser.add_argument('--no-overwrite', action='store_true', default=False,
                        help='Do not allow overwriting existing images (based on module version and jina version)')
    return parser
