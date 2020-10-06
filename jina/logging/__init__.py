__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from pkg_resources import resource_filename

from .logger import JinaLogger

default_logger = JinaLogger('JINA')  #: a logger at the global-level
profile_logger = JinaLogger('PROFILE', log_config=resource_filename('jina',
                                                                    '/'.join(('resources', 'logging.profile.yml'))))
