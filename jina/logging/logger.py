import logging
import logging.handlers
import os
import platform
import sys
from typing import Optional

from . import formatter
from .. import __uptime__, __resources_path__, __windows__
from ..enums import LogVerbosity
from ..jaml import JAML


class SysLogHandlerWrapper(logging.handlers.SysLogHandler):
    """
    Override the priority_map :class:`SysLogHandler`.

    .. warning::
        This messages at DEBUG and INFO are therefore not stored by ASL, (ASL = Apple System Log)
        which in turn means they can't be printed by syslog after the fact. You can confirm it via :command:`syslog` or
        :command:`tail -f /var/log/system.log`.
    """

    priority_map = {
        'DEBUG': 'debug',
        'INFO': 'info',
        'WARNING': 'warning',
        'ERROR': 'error',
        'CRITICAL': 'critical',
    }


class JinaLogger:
    """
    Build a logger for a context.

    :param context: The context identifier of the class, module or method.
    :param log_config: The configuration file for the logger.
    :param identity: The id of the group the messages from this logger will belong, used by fluentd default
    configuration to group logs by pod.
    :param workspace_path: The workspace path where the log will be stored at (only apply to fluentd)
    :return:: an executor object.
    """

    supported = {'FileHandler', 'StreamHandler', 'SysLogHandler', 'FluentHandler'}

    def __init__(
        self,
        context: str,
        name: Optional[str] = None,
        log_config: Optional[str] = None,
        identity: Optional[str] = None,
        workspace_path: Optional[str] = None,
        quiet: bool = False,
        **kwargs,
    ):

        if not log_config:
            log_config = os.getenv(
                'JINA_LOG_CONFIG',
                os.path.join(__resources_path__, 'logging.default.yml'),
            )

        if quiet or os.getenv('JINA_LOG_CONFIG', None) == 'QUIET':
            log_config = os.path.join(__resources_path__, 'logging.quiet.yml')

        if not identity:
            identity = os.getenv('JINA_LOG_ID', None)

        if not name:
            name = os.getenv('JINA_POD_NAME', context)

        # Remove all handlers associated with the root logger object.
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        self.logger = logging.getLogger(context)
        self.logger.propagate = False

        context_vars = {
            'name': name,
            'uptime': __uptime__,
            'context': context,
            'workspace_path': workspace_path
            or os.getenv('JINA_LOG_WORKSPACE', '/tmp/jina/'),
        }
        if identity:
            context_vars['log_id'] = identity

        self.add_handlers(log_config, **context_vars)
        self.success = lambda *x: self.logger.log(LogVerbosity.SUCCESS, *x)
        self.debug = self.logger.debug
        self.warning = self.logger.warning
        self.critical = self.logger.critical
        self.error = self.logger.error
        self.info = self.logger.info
        self._is_closed = False
        self.debug_enabled = self.logger.isEnabledFor(logging.DEBUG)

    @property
    def handlers(self):
        """
        Get the handlers of the logger.

        :return:: Handlers of logger.
        """
        return self.logger.handlers

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close all the handlers."""
        if not self._is_closed:
            for handler in self.logger.handlers:
                handler.close()
            self._is_closed = True

    def add_handlers(self, config_path: Optional[str] = None, **kwargs):
        """
        Add handlers from config file.

        :param config_path: Path of config file.
        :param kwargs: Extra parameters.
        """
        self.logger.handlers = []

        with open(config_path) as fp:
            config = JAML.load(fp)

        for h in config['handlers']:
            cfg = config['configs'].get(h, None)
            fmt = getattr(formatter, cfg.get('formatter', 'Formatter'))

            if h not in self.supported or not cfg:
                raise ValueError(
                    f'can not find configs for {h}, maybe it is not supported'
                )

            handler = None
            if h == 'StreamHandler':
                handler = logging.StreamHandler(sys.stdout)
                handler.setFormatter(fmt(cfg['format'].format_map(kwargs)))
            elif h == 'SysLogHandler' and not __windows__:
                if cfg['host'] and cfg['port']:
                    handler = SysLogHandlerWrapper(address=(cfg['host'], cfg['port']))
                else:
                    # a UNIX socket is used
                    if platform.system() == 'Darwin':
                        handler = SysLogHandlerWrapper(address='/var/run/syslog')
                    else:
                        handler = SysLogHandlerWrapper(address='/dev/log')
                if handler:
                    handler.ident = cfg.get('ident', '')
                    handler.setFormatter(fmt(cfg['format'].format_map(kwargs)))

                try:
                    handler._connect_unixsocket(handler.address)
                except OSError:
                    handler = None
                    pass
            elif h == 'FileHandler':
                filename = cfg['output'].format_map(kwargs)
                if __windows__:
                    # colons are not allowed in filenames
                    filename = filename.replace(':', '.')
                handler = logging.FileHandler(filename, delay=True)
                handler.setFormatter(fmt(cfg['format'].format_map(kwargs)))
            elif h == 'FluentHandler':
                from ..importer import ImportExtensions

                with ImportExtensions(required=False, verbose=False):
                    from fluent import asynchandler as fluentasynchandler
                    from fluent.handler import FluentRecordFormatter

                    handler = fluentasynchandler.FluentHandler(
                        cfg['tag'],
                        host=cfg['host'],
                        port=cfg['port'],
                        queue_circular=True,
                    )

                    cfg['format'].update(kwargs)
                    fmt = FluentRecordFormatter(cfg['format'])
                    handler.setFormatter(fmt)

            if handler:
                self.logger.addHandler(handler)

        verbose_level = LogVerbosity.from_string(config['level'])
        if 'JINA_LOG_LEVEL' in os.environ:
            verbose_level = LogVerbosity.from_string(os.environ['JINA_LOG_LEVEL'])
        self.logger.setLevel(verbose_level.value)
