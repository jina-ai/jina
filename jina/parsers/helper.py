"""Module for helper functions in the parser"""

import argparse
import os
from typing import Tuple

from jina.enums import GatewayProtocolType
from jina.logging.predefined import default_logger

_SHOW_ALL_ARGS = 'JINA_FULL_CLI' in os.environ


def add_arg_group(parser, title):
    """Add the arguments for a specific group to the parser

    :param parser: the parser configure
    :param title: the group name
    :return: the new parser
    """
    return parser.add_argument_group(f'{title} arguments')


class KVAppendAction(argparse.Action):
    """argparse action to split an argument into KEY=VALUE form
    on the first = and append to a dictionary.
    This is used for setting up --env
    """

    def __call__(self, parser, args, values, option_string=None):
        """
        call the KVAppendAction


        .. # noqa: DAR401
        :param parser: the parser
        :param args: args to initialize the values
        :param values: the values to add to the parser
        :param option_string: inherited, not used
        """
        import json
        import re

        from jina.helper import parse_arg

        d = getattr(args, self.dest) or {}
        for value in values:
            try:
                d.update(json.loads(value))
            except json.JSONDecodeError:
                try:
                    k, v = re.split(r'[:=]\s*', value, maxsplit=1)
                except ValueError:
                    raise argparse.ArgumentTypeError(
                        f'could not parse argument \"{values[0]}\" as k=v format'
                    )
                d[k] = parse_arg(v)
        setattr(args, self.dest, d)


class _ColoredHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    class _Section(object):
        def __init__(self, formatter, parent, heading=None):
            self.formatter = formatter
            self.parent = parent
            self.heading = heading
            self.items = []

        def format_help(self):
            # format the indented section
            if self.parent is not None:
                self.formatter._indent()
            join = self.formatter._join_parts
            item_help = join([func(*args) for func, args in self.items])
            if self.parent is not None:
                self.formatter._dedent()

            # return nothing if the section was empty
            if not item_help.strip():
                return ''

            # add the heading if the section was non-empty
            if self.heading is not argparse.SUPPRESS and self.heading is not None:
                from jina.helper import colored

                current_indent = self.formatter._current_indent
                captial_heading = ' '.join(
                    v[0].upper() + v[1:] for v in self.heading.split(' ')
                )
                heading = '%*s%s\n' % (
                    current_indent,
                    '',
                    colored(f'▮ {captial_heading}', 'cyan', attrs=['bold']),
                )
            else:
                heading = ''

            # join the section-initial newline, the heading and the help
            return join(['\n', heading, item_help, '\n'])

    def start_section(self, heading):
        self._indent()
        section = self._Section(self, self._current_section, heading)
        self._add_item(section.format_help, [])
        self._current_section = section

    def _get_help_string(self, action):
        help_string = ''
        if '%(default)' not in action.help:
            if action.default is not argparse.SUPPRESS:
                from jina.helper import colored

                defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
                if isinstance(action, argparse._StoreTrueAction):

                    help_string = colored(
                        'default: %s'
                        % (
                            'enabled'
                            if action.default
                            else f'disabled, use "{action.option_strings[0]}" to enable it'
                        ),
                        attrs=['dark'],
                    )
                elif action.choices:
                    choices_str = f'{{{", ".join([str(c) for c in action.choices])}}}'
                    help_string = colored(
                        'choose from: ' + choices_str + '; default: %(default)s',
                        attrs=['dark'],
                    )
                elif action.option_strings or action.nargs in defaulting_nargs:
                    help_string = colored(
                        'type: %(type)s; default: %(default)s', attrs=['dark']
                    )
        return f'''
        
        {help_string}
        
        {action.help}
        
        '''

    def _join_parts(self, part_strings):
        return '\n' + ''.join(
            [part for part in part_strings if part and part is not argparse.SUPPRESS]
        )

    def _get_default_metavar_for_optional(self, action):
        return ''

    def _expand_help(self, action):
        params = dict(vars(action), prog=self._prog)
        for name in list(params):
            if params[name] is argparse.SUPPRESS:
                del params[name]
        for name in list(params):
            if hasattr(params[name], '__name__'):
                params[name] = params[name].__name__
        return self._get_help_string(action) % params

    def _metavar_formatter(self, action, default_metavar):
        if action.metavar is not None:
            result = action.metavar
        elif action.choices is not None:

            if len(action.choices) > 4:
                choice_strs = ', '.join([str(c) for c in action.choices][:4])
                result = f'{{{choice_strs} ... {len(action.choices) - 4} more choices}}'
            else:
                choice_strs = ', '.join([str(c) for c in action.choices])
                result = f'{{{choice_strs}}}'
        else:
            result = default_metavar

        def formatter(tuple_size):
            if isinstance(result, tuple):
                return result
            else:
                return (result,) * tuple_size

        return formatter

    def _split_lines(self, text, width):
        return self._para_reformat(text, width)

    def _fill_text(self, text, width, indent):
        lines = self._para_reformat(text, width)
        return '\n'.join(lines)

    def _indents(self, line) -> Tuple[int, int]:
        """Return line indent level and "sub_indent" for bullet list text.

        :param line: the line to check
        :return: indentation of line and indentation of sub-items
        """
        import re

        indent = len(re.match(r'( *)', line).group(1))
        list_match = re.match(r'( *)(([*\-+>]+|\w+\)|\w+\.) +)', line)
        if list_match:
            sub_indent = indent + len(list_match.group(2))
        else:
            sub_indent = indent

        return indent, sub_indent

    def _split_paragraphs(self, text):
        """Split text into paragraphs of like-indented lines.

        :param text: the text input
        :return: list of paragraphs
        """

        import re
        import textwrap

        text = textwrap.dedent(text).strip()
        text = re.sub('\n\n[\n]+', '\n\n', text)

        last_sub_indent = None
        paragraphs = list()
        for line in text.splitlines():
            (indent, sub_indent) = self._indents(line)
            is_text = len(line.strip()) > 0

            if is_text and indent == sub_indent == last_sub_indent:
                paragraphs[-1] += ' ' + line
            else:
                paragraphs.append(line)

            if is_text:
                last_sub_indent = sub_indent
            else:
                last_sub_indent = None

        return paragraphs

    def _para_reformat(self, text, width):
        """Format text, by paragraph.

        :param text: the text to format
        :param width: the width to apply
        :return: the new text
        """

        import textwrap

        lines = list()
        for paragraph in self._split_paragraphs(text):
            (indent, sub_indent) = self._indents(paragraph)

            paragraph = self._whitespace_matcher.sub(' ', paragraph).strip()
            new_lines = textwrap.wrap(
                text=paragraph,
                width=width,
                initial_indent=' ' * indent,
                subsequent_indent=' ' * sub_indent,
            )

            # Blank lines get eaten by textwrap, put it back
            lines.extend(new_lines or [''])

        return lines


def _get_gateway_class(protocol):
    from jina.serve.runtimes.gateway.grpc import GRPCGateway
    from jina.serve.runtimes.gateway.http import HTTPGateway
    from jina.serve.runtimes.gateway.websocket import WebSocketGateway

    gateway_dict = {
        GatewayProtocolType.GRPC: GRPCGateway,
        GatewayProtocolType.WEBSOCKET: WebSocketGateway,
        GatewayProtocolType.HTTP: HTTPGateway,
    }
    return gateway_dict[protocol]


def _set_gateway_uses(args: 'argparse.Namespace'):
    if not args.uses:
        if len(args.protocol) == 1 and len(args.port) == 1:
            args.uses = _get_gateway_class(args.protocol[0]).__name__
        elif len(args.protocol) == len(args.port):
            from jina.serve.runtimes.gateway.composite import CompositeGateway

            args.uses = CompositeGateway.__name__
        else:
            raise ValueError(
                'You need to specify as much protocols as ports if you want to use a jina built-in gateway'
            )


def _update_gateway_args(args: 'argparse.Namespace'):
    from jina.helper import random_ports

    if not args.port:
        args.port = random_ports(len(args.protocol))
    _set_gateway_uses(args)


class CastToIntAction(argparse.Action):
    """argparse action to cast a list of values to int"""

    def __call__(self, parser, args, values, option_string=None):
        """
        call the CastToIntAction


        .. # noqa: DAR401
        :param parser: the parser
        :param args: args to initialize the values
        :param values: the values to add to the parser
        :param option_string: inherited, not used
        """
        d = []
        for value in values:
            value = value.split(',')
            d.extend([_port_to_int(port) for port in value])
        setattr(args, self.dest, d)


def _port_to_int(port):
    try:
        return int(port)
    except ValueError:
        default_logger.warning(
            f'port {port} is not an integer and cannot be cast to one'
        )
        return port


class CastHostAction(argparse.Action):
    """argparse action to cast a list of values to int"""

    def __call__(self, parser, args, values, option_string=None):
        """
        call the CastHostAction


        .. # noqa: DAR401
        :param parser: the parser
        :param args: args to initialize the values
        :param values: the values to add to the parser
        :param option_string: inherited, not used
        """
        d = []
        for value in values:
            d.extend(value.split(','))
        setattr(args, self.dest, d)

_chf = _ColoredHelpFormatter
