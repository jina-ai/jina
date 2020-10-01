__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import json
import logging
import os
import re
import sys
from copy import copy
from pkg_resources import resource_filename
from logging import Formatter

from .profile import used_memory
from ..enums import LogVerbosity
from ..helper import colored


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


class EventHandler(logging.StreamHandler):
    """
    A cross-thread/process logger that allows fetching via iterator

    .. warning::

        Some logs may be missing, no clear reason why.
    """

    def __init__(self, event):
        super().__init__()
        self._event = event

    def emit(self, record):
        if record.levelno >= self.level:
            self._event.record = self.format(record)
            self._event.set()


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


class LoggerWrapper:
    def info(self, msg: str, **kwargs):
        self.logger.info(msg, **kwargs)

    def critical(self, msg: str, **kwargs):
        """log critical-level message"""
        self.logger.critical(msg, **kwargs)

    def debug(self, msg: str, **kwargs):
        """log debug-level message"""
        self.logger.debug(msg, **kwargs)

    def error(self, msg: str, **kwargs):
        """log error-level message"""
        self.logger.error(msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        """log warn-level message"""
        self.logger.warning(msg, **kwargs)

    def success(self, msg: str, **kwargs):
        """log success-level message"""
        self.logger.success(msg, **kwargs)


def get_fluentd_handler(context: str, log_fluentd_config_path: str, profile: bool):
    custom_format = {
        'host': '%(hostname)s',
        'name': f'{context}',
        'process': '%(process)s',
        'type': '%(levelname)s',
    }
    from fluent import asynchandler as fluentasynchandler
    from fluent.handler import FluentRecordFormatter
    import yaml
    with open(log_fluentd_config_path) as fp:
        config = yaml.load(fp)

    tag_key = 'tag' if not profile else 'profile-tag'
    tag = config[tag_key] if tag_key in config else context
    handler = fluentasynchandler.FluentHandler(f'{tag}', host=config['host'],
                                               port=config['port'], queue_circular=True)
    formatter = FluentRecordFormatter(custom_format)
    handler.setFormatter(formatter)
    return handler


class JinaLogger(LoggerWrapper):

    def __init__(self, context: str, context_len: int = 15, log_sse: bool = False,
                 fmt_str: str = None, event_trigger=None,
                 log_fluentd_config_path: str = resource_filename('jina',
                                                                  '/'.join(('resources', 'logging.fluentd.yml'))),
                 **kwargs):
        """Get a logger with configurations

            :param context: the name prefix of the log
            :param context_len: length of the context, i.e. module, function, line number
            :param log_profile: is this logger for profiling, profile logger takes dict and output to json
            :param log_sse: is this logger used for server-side event
            :param fmt_str: use customized logging format, otherwise respect the ``JINA_LOG_LONG`` environment variable
            :param event_trigger: a ``threading.Event`` or ``multiprocessing.Event`` for event-based logger
            :return: the configured logger

            .. note::
                One can change the verbosity of jina logger via the environment variable ``JINA_LOG_VERBOSITY``

        """
        super().__init__()
        from .. import __uptime__
        if not fmt_str:
            title = os.environ.get('JINA_POD_NAME', context)
            if 'JINA_LOG_LONG' in os.environ:
                fmt_str = f'{title[:context_len]:>{context_len}}@%(process)2d' \
                          f'[%(levelname).1s][%(filename).3s:%(funcName).3s:%(lineno)3d]:%(message)s'
            else:
                fmt_str = f'{title[:context_len]:>{context_len}}@%(process)2d' \
                          f'[%(levelname).1s]:%(message)s'

        timed_fmt_str = f'%(asctime)s:' + fmt_str

        verbose_level = LogVerbosity.from_string(os.environ.get('JINA_LOG_VERBOSITY', 'INFO'))

        # Remove all handlers associated with the root logger object.
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        self.logger = logging.getLogger(context)
        self.logger.propagate = False
        self.logger.handlers = []
        self.logger.setLevel(verbose_level.value)

        if event_trigger is not None:
            h = EventHandler(event_trigger)
            h.setFormatter(ColorFormatter(fmt_str))
            self.logger.addHandler(h)

        if ('JINA_LOG_SSE' in os.environ) or log_sse:
            self.logger.addHandler(get_fluentd_handler(context, log_fluentd_config_path, False))

        if os.environ.get('JINA_LOG_FILE') == 'TXT':
            h = logging.FileHandler(f'jina-{__uptime__}.log', delay=True)
            h.setFormatter(PlainFormatter(timed_fmt_str))
            self.logger.addHandler(h)
        elif os.environ.get('JINA_LOG_FILE') == 'JSON':
            h = logging.FileHandler(f'jina-{__uptime__}.json', delay=True)
            h.setFormatter(JsonFormatter(timed_fmt_str))
            self.logger.addHandler(h)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColorFormatter(fmt_str))
        self.logger.addHandler(console_handler)

        success_level = LogVerbosity.SUCCESS.value  # between WARNING and INFO
        logging.addLevelName(success_level, 'SUCCESS')
        setattr(self.logger, 'success', lambda message: self.logger.log(success_level, message))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        for handler in self.logger.handlers:
            handler.close()


class ProfileLogger(LoggerWrapper):

    def __init__(self, context: str, context_len: int = 15,
                 fmt_str: str = None, log_fluentd_config_path: str = resource_filename('jina',
                                                                                       '/'.join(
                ('resources', 'logging.fluentd.yml'))), **kwargs):
        if not fmt_str:
            title = os.environ.get('JINA_POD_NAME', context)
            if 'JINA_LOG_LONG' in os.environ:
                fmt_str = f'{title[:context_len]:>{context_len}}@%(process)2d' \
                          f'[%(levelname).1s][%(filename).3s:%(funcName).3s:%(lineno)3d]:%(message)s'
            else:
                fmt_str = f'{title[:context_len]:>{context_len}}@%(process)2d' \
                          f'[%(levelname).1s]:%(message)s'

        verbose_level = LogVerbosity.from_string(os.environ.get('JINA_LOG_VERBOSITY', 'INFO'))

        # Remove all handlers associated with the root logger object.
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        self.logger = logging.getLogger(context)
        self.logger.propagate = False
        self.logger.handlers = []
        self.logger.setLevel(verbose_level.value)
        self.logger.addHandler(get_fluentd_handler(context, log_fluentd_config_path, True))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        for handler in self.logger.handlers:
            handler.close()
