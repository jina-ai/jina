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
from ..helper import yaml, complete_path, typename


class NTLogger:
    def __init__(self, context: str, log_level: 'LogVerbosity'=LogVerbosity.INFO):
        """A compatible logger for Windows system, colors are all removed to keep compat.

        :param context: the name prefix of each log
        :param verbose: show debug level info
        """
        self.context = self._planify(context)
        self.log_level = log_level

    @staticmethod
    def _planify(msg):
        return re.sub(r'\u001b\[.*?[@-~]', '', msg)

    def info(self, msg: str, **kwargs):
        """log info-level message"""
        if self.log_level <= LogVerbosity.INFO:
            sys.stdout.write(f'{self.context}[I]:{self._planify(msg)}')

    def critical(self, msg: str, **kwargs):
        """log critical-level message"""
        if self.log_level <= LogVerbosity.CRITICAL:
            sys.stdout.write(f'{self.context}[C]:{self._planify(msg)}')

    def debug(self, msg: str, **kwargs):
        """log debug-level message"""
        if self.log_level <= LogVerbosity.DEBUG:
            sys.stdout.write(f'{self.context}[D]:{self._planify(msg)}')

    def error(self, msg: str, **kwargs):
        """log error-level message"""
        if self.log_level <= LogVerbosity.ERROR:
            sys.stdout.write(f'{self.context}[E]:{self._planify(msg)}')

    def warning(self, msg: str, **kwargs):
        """log warn-level message"""
        if self.log_level <= LogVerbosity.WARNING:
            sys.stdout.write(f'{self.context}[W]:{self._planify(msg)}')

    def success(self, msg: str, **kwargs):
        """log success-level message"""
        if self.log_level <= LogVerbosity.SUCCESS:
            sys.stdout.write(f'{self.context}[S]:{self._planify(msg)}')


class PrintLogger(NTLogger):

    @staticmethod
    def _planify(msg):
        return msg


class SysLogHandlerWrapper(logging.handlers.SysLogHandler):
    """ Override the priority_map :class:`SysLogHandler`

    .. warning::
        This messages at DEBUG and INFO are therefore not stored by ASL, (ASL = Apple System Log)
        which in turn means they can't be printed by syslog after the fact. You can confirm it via :command:`syslog` or
        :command:`tail -f /var/log/system.log`
    """
    priority_map = {
        'DEBUG': 'debug',
        'INFO': 'info',
        'WARNING': 'warning',
        'ERROR': 'error',
        'CRITICAL': 'critical',
        'SUCCESS': 'notice'
    }


class JinaLogger:
    supported = {'FileHandler', 'StreamHandler', 'SysLogHandler', 'FluentHandler'}

    def __init__(self,
                 context: str,
                 name: Optional[str] = None,
                 log_config: Optional[str] = None,
                 log_id: Optional[str] = None, **kwargs):
        """Build a logger for a context
        :param context: The context identifier of the class, module or method
        :param log_config: the configuration file for the logger
        :param log_id: the id of the group the messages from this logger will belong, used by fluentd default configuration
        to group logs by pod
        :return: an executor object
        """
        from .. import __uptime__
        if log_config is None:
            log_config = os.getenv('JINA_LOG_CONFIG',
                                   resource_filename('jina', '/'.join(
                                       ('resources', 'logging.default.yml'))))
        log_config = complete_path(log_config)

        if log_id is None:
            log_id = os.getenv('JINA_LOG_ID', None)

        if name is None:
            name = os.getenv('JINA_POD_NAME', context)

        # Remove all handlers associated with the root logger object.
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        self.logger = logging.getLogger(context)
        self.logger.propagate = False

        context_vars = {'name': name,
                        'uptime': __uptime__,
                        'context': context}
        if log_id:
            context_vars['log_id'] = log_id
        self.add_handlers(log_config, **context_vars)

        # note logger.success isn't default there
        success_level = LogVerbosity.SUCCESS.value  # between WARNING and INFO
        logging.addLevelName(success_level, 'SUCCESS')
        setattr(self.logger, 'success', lambda message: self.logger.log(success_level, message))

        self.info = self.logger.info
        self.critical = self.logger.critical
        self.debug = self.logger.debug
        self.error = self.logger.error
        self.warning = self.logger.warning
        self.success = self.logger.success

    @property
    def handlers(self):
        return self.logger.handlers

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        for handler in self.logger.handlers:
            handler.close()

    def add_handlers(self, config_path: str = None, **kwargs):
        self.logger.handlers = []

        with open(config_path) as fp:
            config = yaml.load(fp)

        for h in config['handlers']:
            cfg = config['configs'].get(h, None)
            fmt = getattr(formatter, cfg.get('formatter', 'PlainFormatter'))

            if h not in self.supported or not cfg:
                raise ValueError(f'can not find configs for {h}, maybe it is not supported')

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
                handler = logging.FileHandler(cfg['output'].format_map(kwargs), delay=True)
                handler.setFormatter(fmt(cfg['format'].format_map(kwargs)))
            elif h == 'FluentHandler':
                from ..importer import ImportExtensions
                with ImportExtensions(required=False):
                    from fluent import asynchandler as fluentasynchandler
                    from fluent.handler import FluentRecordFormatter

                    handler = fluentasynchandler.FluentHandler(cfg['tag'],
                                                               host=cfg['host'],
                                                               port=cfg['port'], queue_circular=True)

                    cfg['format'].update(kwargs)
                    fmt = FluentRecordFormatter(cfg['format'])
                    handler.setFormatter(fmt)

            if handler:
                self.logger.addHandler(handler)

        verbose_level = LogVerbosity.from_string(config['level'])
        self.logger.setLevel(verbose_level.value)
