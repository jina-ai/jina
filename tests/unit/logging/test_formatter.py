import json
from logging import LogRecord
import pytest

from jina.logging.formatter import JsonFormatter, ProfileFormatter


def test_json_formatter():
    json_formatter = JsonFormatter()
    record = LogRecord(
        name='record',
        level='level',
        pathname='pathname',
        lineno=1,
        msg='text message',
        args=None,
        exc_info=None,
    )
    format_dict = json.loads(json_formatter.format(record))
    assert format_dict['pathname'] == 'pathname'
    assert format_dict['lineno'] == 1
    assert format_dict['levelname'] == 'Level level'
    assert format_dict['msg'] == 'text message'


@pytest.mark.parametrize('msg', ['not a dict', {}])
def test_profile_formatter(msg):
    profile_formatter = ProfileFormatter()
    record = LogRecord(
        name='record',
        level='level',
        pathname='pathname',
        lineno=1,
        msg=msg,
        args=None,
        exc_info=None,
    )
    format_msg = profile_formatter.format(record)
    if isinstance(msg, str):
        assert format_msg == ''
    else:
        format_dict = json.loads(format_msg)
        assert 'created' in format_dict
        assert 'process' in format_dict
        assert 'module' in format_dict
        assert 'thread' in format_dict
        assert 'memory' in format_dict
