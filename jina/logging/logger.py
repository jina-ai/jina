__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import json
import logging
import os
import platform
import re
import sys
from copy import copy
from logging import Formatter
from logging.handlers import SysLogHandler

from pkg_resources import resource_filename

from .profile import used_memory
from ..enums import LogVerbosity
from ..helper import colored, yaml, complete_path


class ColorFormatter(Formatter):
    """Format the log into colored logs based on the log-level. """

    MAPPING = {
        'DEBUG': dict(color='white', on_color=None),  # white
        'INFO': dict(color='white', on_color=None),  # cyan
        'WARNING': dict(color='yellow', on_color='on_grey'),  # yellow
        'ERROR': dict(color='red', on_color=None),  # 31 for red
        'CRITICAL': dict(color='white', on_color='on_red'),  # white on red bg
        'SUCCESS': dict(color='green', on_color=None),  # white on red bg
    }  #: log-level to color mapping

    def format(self, record):
        cr = copy(record)
        seq = self.MAPPING.get(cr.levelname, self.MAPPING['INFO'])  # default white
        cr.msg = colored(cr.msg, **seq)
        return super().format(cr)


class PlainFormatter(Formatter):
    """Remove all control chars from the log and format it as plain text """

    def format(self, record):
        cr = copy(record)
        if isinstance(cr.msg, str):
            cr.msg = re.sub(u'\u001b\[.*?[@-~]', '', str(cr.msg))
        return super().format(cr)


class JsonFormatter(Formatter):
    """Format the log message as a JSON object so that it can be later used/parsed in browser with javascript. """

    KEYS = {'created', 'filename', 'funcName', 'levelname', 'lineno', 'msg',
            'module', 'name', 'pathname', 'process', 'thread', 'processName',
            'threadName'}  #: keys to extract from the log

    def format(self, record):
        cr = copy(record)
        cr.msg = re.sub(u'\u001b\[.*?[@-~]', '', str(cr.msg))
        return json.dumps(
            {k: getattr(cr, k) for k in self.KEYS},
            sort_keys=True)


class ProfileFormatter(Formatter):
    """Format the log message as JSON object and add the current used memory into it"""

    def format(self, record):
        cr = copy(record)
        if isinstance(cr.msg, dict):
            cr.msg.update({k: getattr(cr, k) for k in ['created', 'module', 'process', 'thread']})
            cr.msg['memory'] = used_memory(unit=1)
            return json.dumps(cr.msg, sort_keys=True)
        else:
            return ''


class NTLogger:
    def __init__(self, context: str, log_level: 'LogVerbosity'):
        """A compatible logger for Windows system, colors are all removed to keep compat.

        :param context: the name prefix of each log
        :param verbose: show debug level info
        """
        self.context = self._planify(context)
        self.log_level = log_level

    @staticmethod
    def _planify(msg):
        return re.sub(u'\u001b\[.*?[@-~]', '', msg)

    def info(self, msg: str, **kwargs):
        """log info-level message"""
        if self.log_level <= LogVerbosity.INFO:
            sys.stdout.write(f'I:{self.context}:{self._planify(msg)}')

    def critical(self, msg: str, **kwargs):
        """log critical-level message"""
        if self.log_level <= LogVerbosity.CRITICAL:
            sys.stdout.write(f'C:{self.context}:{self._planify(msg)}')

    def debug(self, msg: str, **kwargs):
        """log debug-level message"""
        if self.log_level <= LogVerbosity.DEBUG:
            sys.stdout.write(f'D:{self.context}:{self._planify(msg)}')

    def error(self, msg: str, **kwargs):
        """log error-level message"""
        if self.log_level <= LogVerbosity.ERROR:
            sys.stdout.write(f'E:{self.context}:{self._planify(msg)}')

    def warning(self, msg: str, **kwargs):
        """log warn-level message"""
        if self.log_level <= LogVerbosity.WARNING:
            sys.stdout.write(f'W:{self.context}:{self._planify(msg)}')

    def success(self, msg: str, **kwargs):
        """log success-level message"""
        if self.log_level <= LogVerbosity.SUCCESS:
            sys.stdout.write(f'W:{self.context}:{self._planify(msg)}')


class MySysLogHandler(SysLogHandler):
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

    def __init__(self, context: str, config_path: str = None):
        from .. import __uptime__

        if not config_path:
            config_path = resource_filename('jina', '/'.join(('resources', 'logging.yml')))
        else:
            config_path = complete_path(config_path)

        # Remove all handlers associated with the root logger object.
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        self.logger = logging.getLogger(context)
        self.logger.propagate = False

        context_vars = {'name': os.environ.get('JINA_POD_NAME', context),
                        'uptime': __uptime__,
                        'context': context}
        self.add_handlers(config_path, **context_vars)

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

            if h not in self.supported or not cfg:
                raise ValueError(f'can not find configs for {h}, maybe it is not supported')

            handler = None
            if h == 'StreamHandler':
                handler = logging.StreamHandler(sys.stdout)
                if cfg['colored']:
                    handler.setFormatter(ColorFormatter(cfg['format'].format_map(kwargs)))
                else:
                    handler.setFormatter(PlainFormatter(cfg['format'].format_map(kwargs)))
            elif h == 'SysLogHandler':
                if cfg['host'] and cfg['port']:
                    handler = MySysLogHandler(address=(cfg['host'], cfg['port']))
                else:
                    # a UNIX socket is used
                    if platform.system() == 'Darwin':
                        handler = MySysLogHandler(address='/var/run/syslog')
                    else:
                        handler = MySysLogHandler(address='/dev/log')
                if handler:
                    handler.setFormatter(PlainFormatter(cfg['format'].format_map(kwargs)))
            elif h == 'FileHandler':
                handler = logging.FileHandler(cfg['output'].format_map(kwargs), delay=True)
                handler.setFormatter(PlainFormatter(cfg['format'].format_map(kwargs)))
            elif h == 'FluentHandler':
                try:
                    from fluent import asynchandler as fluentasynchandler
                    from fluent.handler import FluentRecordFormatter

                    handler = fluentasynchandler.FluentHandler(config['tag'],
                                                               host=config['host'],
                                                               port=config['port'], queue_circular=True)

                    config['format'].update(kwargs)
                    formatter = FluentRecordFormatter(config['format'])
                    handler.setFormatter(formatter)
                except (ModuleNotFoundError, ImportError):
                    pass

            if handler:
                self.logger.addHandler(handler)

        verbose_level = LogVerbosity.from_string(config['level'])
        self.logger.setLevel(verbose_level.value)
