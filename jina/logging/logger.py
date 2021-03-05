__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import logging
import logging.handlers
import os
import platform
import re
import sys
from typing import Optional

from pkg_resources import resource_filename

from . import formatter
from ..enums import LogVerbosity
from ..jaml import JAML


class NTLogger:
    """A compatible logger for Windows system, colors are all removed to keep compatible."""

    def __init__(self, context: str, log_level: 'LogVerbosity' = LogVerbosity.INFO):
        """
        Create a compatible logger for Windows system, colors are all removed to keep compatible.

        :param context: The name prefix of each log.
        :param log_level: Level of log.
        """
        self.context = self._planify(context)
        self.log_level = log_level

    @staticmethod
    def _planify(msg):
        return re.sub(r'\u001b\[.*?[@-~]', '', msg)

    def info(self, msg: str, **kwargs):
        """
        Log info-level message.

        :param kwargs: Keyword arguments.
        :param msg: Context of log.
        """
        if self.log_level <= LogVerbosity.INFO:
            sys.stdout.write(f'{self.context}[I]:{self._planify(msg)}')

    def critical(self, msg: str, **kwargs):
        """
        Log critical-level message.

        :param kwargs: Keyword arguments.
        :param msg: Context of log.
        """
        if self.log_level <= LogVerbosity.CRITICAL:
            sys.stdout.write(f'{self.context}[C]:{self._planify(msg)}')

    def debug(self, msg: str, **kwargs):
        """
        Log debug-level message.

        :param kwargs: Keyword arguments.
        :param msg: Content of log.
        """
        if self.log_level <= LogVerbosity.DEBUG:
            sys.stdout.write(f'{self.context}[D]:{self._planify(msg)}')

    def error(self, msg: str, **kwargs):
        """
        Log error-level message.

        :param kwargs: Keyword arguments.
        :param msg: Context of log.
        """
        if self.log_level <= LogVerbosity.ERROR:
            sys.stdout.write(f'{self.context}[E]:{self._planify(msg)}')

    def warning(self, msg: str, **kwargs):
        """
        Log warning-level message.

        :param kwargs: Keyword arguments.
        :param msg: Context of log.
        """
        if self.log_level <= LogVerbosity.WARNING:
            sys.stdout.write(f'{self.context}[W]:{self._planify(msg)}')

    def success(self, msg: str, **kwargs):
        """
        Log success-level message.

        :param msg: Context of log.
        :param kwargs: Keyword arguments.
        """
        if self.log_level <= LogVerbosity.SUCCESS:
            sys.stdout.write(f'{self.context}[S]:{self._planify(msg)}')


class PrintLogger(NTLogger):
    """Print the message."""

    @staticmethod
    def _planify(msg):
        return msg


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
        'SUCCESS': 'notice',
    }


class JinaLogger:
    """
    Build a logger for a context.

    :param context: The context identifier of the class, module or method.
    :param log_config: The configuration file for the logger.
    :param identity: The id of the group the messages from this logger will belong, used by fluentd default
    configuration to group logs by pod.
    :param workspace_path: The workspace path where the log will be stored at (only apply to fluentd)
    :returns: an executor object.
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
        from .. import __uptime__

        if not log_config:
            log_config = os.getenv(
                'JINA_LOG_CONFIG',
                resource_filename(
                    'jina', '/'.join(('resources', 'logging.default.yml'))
                ),
            )

        if quiet or os.getenv('JINA_LOG_CONFIG', None) == 'QUIET':
            log_config = resource_filename(
                'jina', '/'.join(('resources', 'logging.quiet.yml'))
            )

        if not identity:
            identity = os.getenv('JINA_LOG_ID', None)

        if not name:
            name = os.getenv('JINA_POD_NAME', context)

        # Remove all handlers associated with the root logger object.
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        self.logger = logging.getLogger(context)
        self.logger.propagate = False

        if workspace_path is None:
            workspace_path = os.getenv('JINA_LOG_WORKSPACE', '/tmp/jina/')

        context_vars = {
            'name': name,
            'uptime': __uptime__,
            'context': context,
            'workspace_path': workspace_path,
        }
        if identity:
            context_vars['log_id'] = identity

        self.add_handlers(log_config, **context_vars)

        # note logger.success isn't default there
        success_level = LogVerbosity.SUCCESS.value  # between WARNING and INFO
        logging.addLevelName(success_level, 'SUCCESS')
        setattr(
            self.logger,
            'success',
            lambda message: self.logger.log(success_level, message),
        )

        self.info = self.logger.info
        self.critical = self.logger.critical
        self.debug = self.logger.debug
        self.error = self.logger.error
        self.warning = self.logger.warning
        self.success = self.logger.success

    @property
    def handlers(self):
        """
        Get the handlers of the logger.

        :returns: Handlers of logger.
        """
        return self.logger.handlers

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close all the handlers."""
        for handler in self.logger.handlers:
            handler.close()

    def add_handlers(self, config_path: str = None, **kwargs):
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
            fmt = getattr(formatter, cfg.get('formatter', 'PlainFormatter'))

            if h not in self.supported or not cfg:
                raise ValueError(
                    f'can not find configs for {h}, maybe it is not supported'
                )

            handler = None
            if h == 'StreamHandler':
                handler = logging.StreamHandler(sys.stdout)
                handler.setFormatter(fmt(cfg['format'].format_map(kwargs)))
            elif h == 'SysLogHandler':
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
                handler = logging.FileHandler(
                    cfg['output'].format_map(kwargs), delay=True
                )
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
