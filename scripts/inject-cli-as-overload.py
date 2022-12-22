import re

from jina_cli.export import api_to_dict


def _cli_to_schema(
    api_dict,
    target,
):
    deployment_api = None

    for d in api_dict['methods']:
        if d['name'] == target:
            deployment_api = d['options']
            break

    _schema = {
        'properties': {},
        'required': [],
    }

    for p in deployment_api:
        dtype = p['type']
        if dtype.startswith('typing.'):
            dtype = dtype.replace('typing.', '')
        pv = {'description': p['help'].strip(), 'type': dtype, 'default': p['default']}
        if p['choices']:
            pv['enum'] = p['choices']
        if p['required']:
            _schema['required'].append(p['name'])
        if dtype == 'array':
            _schema['items'] = {'type': 'string', 'minItems': 1, 'uniqueItems': True}

        pv['default_literal'] = pv['default']
        if isinstance(pv['default'], str):
            pv['default_literal'] = "'" + pv['default'] + "'"
        elif isinstance(pv['default'], list):
            pv['default_literal'] = [str(item) for item in pv['default']]
        if p['default_random']:
            pv['default_literal'] = None

        # special cases
        if p['name'] == 'log_config':
            pv['default_literal'] = None
        if p['name'] in {'uses', 'uses_before', 'uses_after'} and target != 'flow':
            pv['type'] = 'Union[str, Type[\'BaseExecutor\'], dict]'
        if p['name'] == 'protocol':
            pv['type'] = 'Union[str, List[str]]'
            print(_schema)

        pv['description'] = pv['description'].replace('\n', '\n' + ' ' * 10)

        _schema['properties'][p['name']] = pv

    return sorted(_schema['properties'].items(), key=lambda k: k[0])


def fill_overload(
    cli_entrypoint,
    doc_str_title,
    doc_str_return,
    return_type,
    filepath,
    overload_fn,
    class_method,
    indent=' ' * 4,
    regex_tag=None,
):
    a = _cli_to_schema(api_to_dict(), cli_entrypoint)
    if class_method:
        cli_args = [
            f'{indent}{indent}{k[0]}: Optional[{k[1]["type"]}] = {k[1]["default_literal"]}'
            for k in a
        ]
        args_str = ', \n'.join(cli_args + [f'{indent}{indent}**kwargs'])
        signature_str = f'def {overload_fn}(\n{indent}{indent}self,*,\n{args_str})'
        if return_type:
            signature_str += f' -> {return_type}:'
            return_str = f'\n{indent}{indent}:return: {doc_str_return}'
        else:
            signature_str += ':'
            return_str = ''
    else:
        cli_args = [
            f'{indent}{k[0]}: Optional[{k[1]["type"]}] = {k[1]["default_literal"]}'
            for k in a
        ]
        args_str = ', \n'.join(cli_args + [f'{indent}**kwargs'])
        signature_str = f'def {overload_fn}(*, \n{args_str})'
        if return_type:
            signature_str += f' -> {return_type}:'
            return_str = f'\n{indent}:return: {doc_str_return}'
        else:
            signature_str += ':'
            return_str = ''
    if class_method:
        doc_str = '\n'.join(
            f'{indent}{indent}:param {k[0]}: {k[1]["description"]}' for k in a
        )
        noqa_str = '\n'.join(
            f'{indent}{indent}.. # noqa: DAR{j}' for j in ['202', '101', '003']
        )
    else:
        doc_str = '\n'.join(f'{indent}:param {k[0]}: {k[1]["description"]}' for k in a)
        noqa_str = '\n'.join(
            f'{indent}.. # noqa: DAR{j}' for j in ['202', '101', '003']
        )
    if class_method:
        final_str = f'@overload\n{indent}{signature_str}\n{indent}{indent}"""{doc_str_title}\n\n{doc_str}{return_str}\n\n{noqa_str}\n{indent}{indent}"""'
        final_code = re.sub(
            rf'(# overload_inject_start_{regex_tag or cli_entrypoint}).*(# overload_inject_end_{regex_tag or cli_entrypoint})',
            f'\\1\n{indent}{final_str}\n{indent}\\2',
            open(filepath).read(),
            0,
            re.DOTALL,
        )
    else:
        final_str = f'@overload\n{signature_str}\n{indent}"""{doc_str_title}\n\n{doc_str}{return_str}\n\n{noqa_str}\n{indent}"""'
        final_code = re.sub(
            rf'(# overload_inject_start_{regex_tag or cli_entrypoint}).*(# overload_inject_end_{regex_tag or cli_entrypoint})',
            f'\\1\n{final_str}\n{indent}\\2',
            open(filepath).read(),
            0,
            re.DOTALL,
        )

    with open(filepath, 'w') as fp:
        fp.write(final_code)
    return {regex_tag or cli_entrypoint: doc_str}


def _get_docstring_title(file_str, tag):
    # extracts the description ('title') of a docstring, i.e. the initial part that has no :param:, :return: etc.
    title_start_regex = f'# implementation_stub_inject_start_{tag}'
    title_end_regex = (
        f':param|:return:|# implementation_stub_inject_end_{tag}|.. # noqa:'
    )
    doc_str_title_match = re.search(
        rf'({title_start_regex}).*?({title_end_regex})', file_str, flags=re.DOTALL
    )
    doc_str_title = file_str[
        doc_str_title_match.span()[0] : doc_str_title_match.span()[1]
    ]
    # trim of start and end patterns
    doc_str_title = re.sub('"""', '', doc_str_title, 0, re.DOTALL)  # delete """
    doc_str_title = re.sub(
        rf'{title_start_regex}', '', doc_str_title, 1, re.DOTALL
    )  # delete start regex
    doc_str_title = re.sub(
        rf'{title_end_regex}', '', doc_str_title, 1, re.DOTALL
    )  # delete end regex
    doc_str_title = re.sub(
        '\n+$', '', doc_str_title, 1, re.DOTALL
    )  # delete trailing white space
    doc_str_title = re.sub(
        '^\n+', '', doc_str_title, 1, re.DOTALL
    )  # delete leading white space
    doc_str_title = re.sub(
        '\s+$', '', doc_str_title, 1, re.DOTALL
    )  # delete trailing newline
    doc_str_title = re.sub(
        '^\s+', '', doc_str_title, 1, re.DOTALL
    )  # delete leading newline
    return doc_str_title


def fill_implementation_stub(
    doc_str_return,
    return_type,
    filepath,
    overload_fn,
    class_method,
    indent=' ' * 4,
    overload_tags=[],  # from which methods should we gather the docstrings?
    regex_tag=None,
    tag_to_docstring=dict(),
    additional_params=[],  # :param: lines that do not come from the override methods, but from the implementation stub itself
):
    # collects all :param: descriptions from overload methods and adds them to the method stub that has the actual implementation
    overload_fn = overload_fn.lower()
    relevant_docstrings = [tag_to_docstring[t] for t in overload_tags]
    add_param_indent = f'{indent}{indent}' if class_method else f'{indent}'
    relevant_docstrings += [add_param_indent + p for p in additional_params]
    if class_method:
        doc_str = ''
        for i, s in enumerate(relevant_docstrings):
            if i != 0:
                doc_str += '\n'
            doc_str += s
        noqa_str = '\n'.join(
            f'{indent}{indent}.. # noqa: DAR{j}' for j in ['102', '202', '101', '003']
        )
        if return_type:
            return_str = f'\n{indent}{indent}:return: {doc_str_return}'
        else:
            return_str = ''
    else:
        doc_str = ''
        for i, s in enumerate(relevant_docstrings):
            if i != 0:
                doc_str += '\n'
            doc_str += s
        noqa_str = '\n'.join(
            f'{indent}.. # noqa: DAR{j}' for j in ['102', '202', '101', '003']
        )
        if return_type:
            return_str = f'\n{indent}:return: {doc_str_return}'
        else:
            return_str = ''
    if class_method:
        file_str = open(filepath).read()
        doc_str_title = _get_docstring_title(file_str, regex_tag or overload_fn)
        final_str = f'\n{indent}{indent}"""{doc_str_title}\n\n{doc_str}{return_str}\n\n{noqa_str}\n{indent}{indent}"""'
        final_code = re.sub(
            rf'(# implementation_stub_inject_start_{regex_tag or overload_fn}).*(# implementation_stub_inject_end_{regex_tag or overload_fn})',
            f'\\1\n{indent}{final_str}\n{indent}\\2',
            file_str,
            0,
            re.DOTALL,
        )
    else:
        file_str = open(filepath).read()
        doc_str_title = _get_docstring_title(file_str, regex_tag or overload_fn)
        final_str = f'\n{indent}"""{doc_str_title}\n\n{doc_str}{return_str}\n\n{noqa_str}\n{indent}"""'
        final_code = re.sub(
            rf'(# implementation_stub_inject_start_{regex_tag or overload_fn}).*(# implementation_stub_inject_end_{regex_tag or overload_fn})',
            f'\\1\n{final_str}\n{indent}\\2',
            file_str,
            0,
            re.DOTALL,
        )

    with open(filepath, 'w') as fp:
        fp.write(final_code)


# param
entries = [
    dict(
        cli_entrypoint='deployment',
        doc_str_title='Add an Executor to the current Flow object.',
        doc_str_return='a (new) Flow object with modification',
        return_type="Union['Flow', 'AsyncFlow']",
        filepath='../jina/orchestrate/flow/base.py',
        overload_fn='add',
        class_method=True,  # if it is a method inside class.
    ),
    dict(
        cli_entrypoint='flow',
        doc_str_title='Create a Flow. Flow is how Jina streamlines and scales Executors. This overloaded method provides arguments from `jina flow` CLI.',
        doc_str_return='the new Flow object',
        return_type=None,
        filepath='../jina/orchestrate/flow/base.py',
        overload_fn='__init__',
        class_method=True,
    ),
    dict(
        cli_entrypoint='gateway',
        doc_str_title='Create a Flow. Flow is how Jina streamlines and scales Executors. This overloaded method provides arguments from `jina gateway` CLI.',
        doc_str_return='the new Flow object',
        return_type=None,
        filepath='../jina/orchestrate/flow/base.py',
        overload_fn='__init__',
        class_method=True,
        regex_tag='gateway_flow',
    ),
    dict(
        cli_entrypoint='client',
        doc_str_title='Create a Flow. Flow is how Jina streamlines and scales Executors. This overloaded method provides arguments from `jina client` CLI.',
        doc_str_return='the new Flow object',
        return_type=None,
        filepath='../jina/orchestrate/flow/base.py',
        overload_fn='__init__',
        class_method=True,
        regex_tag='client_flow',
    ),
    dict(
        cli_entrypoint='client',
        doc_str_title='Create a Client. Client is how user interact with Flow',
        doc_str_return='the new Client object',
        return_type="Union['AsyncWebSocketClient', 'WebSocketClient', 'AsyncGRPCClient', 'GRPCClient', 'HTTPClient', 'AsyncHTTPClient']",
        filepath='../jina/clients/__init__.py',
        overload_fn='Client',
        class_method=False,
    ),
    dict(
        cli_entrypoint='gateway',
        doc_str_title='Configure the Gateway inside a Flow. The Gateway exposes your Flow logic as a service to the internet according to the protocol and configuration you choose.',
        doc_str_return='the new Flow object',
        return_type=None,
        filepath='../jina/orchestrate/flow/base.py',
        overload_fn='config_gateway',
        class_method=True,
        regex_tag='config_gateway',
    ),
    dict(
        cli_entrypoint='deployment',
        doc_str_title='Serve this Executor in a temporary Flow. Useful in testing an Executor in remote settings.',
        doc_str_return='None',
        return_type=None,
        filepath='../jina/serve/executors/__init__.py',
        overload_fn='serve',
        class_method=True,
        regex_tag='executor_serve',
    ),
]

# param
implementation_stub_entries = [
    dict(
        doc_str_return='a (new) Flow object with modification',
        return_type="Union['Flow', 'AsyncFlow']",
        filepath='../jina/orchestrate/flow/base.py',
        overload_fn='add',
        class_method=True,  # if it is a method inside class.
        overload_tags=['deployment'],
        additional_params=[  # param docstrings which do not come from overloads (or from overlaods that are not parser-generated) need to be defined here!
            ':param needs: the name of the Deployment(s) that this Deployment receives data from. One can also use "gateway" to indicate the connection with the gateway.',
            ':param deployment_role: the role of the Deployment, used for visualization and route planning',
            ':param copy_flow: when set to true, then always copy the current Flow and do the modification on top of it then return, otherwise, do in-line modification',
            ':param kwargs: other keyword-value arguments that the Deployment CLI supports',
            ':return: a (new) Flow object with modification',
        ],
    ),
    dict(
        doc_str_return='the new Flow object',
        return_type=None,
        filepath='../jina/orchestrate/flow/base.py',
        overload_fn='__init__',
        class_method=True,
        overload_tags=['client_flow', 'gateway_flow', 'flow'],
        regex_tag='flow',
    ),
    dict(
        doc_str_return='the new Flow object',
        return_type="Union['Flow', 'AsyncFlow']",
        filepath='../jina/orchestrate/flow/base.py',
        overload_fn='config_gateway',
        class_method=True,
        overload_tags=['config_gateway'],
        regex_tag='config_gateway',
    ),
    dict(
        doc_str_return='the new Client object',
        return_type="Union['AsyncWebSocketClient', 'WebSocketClient', 'AsyncGRPCClient', 'GRPCClient', 'HTTPClient', 'AsyncHTTPClient']",
        filepath='../jina/clients/__init__.py',
        overload_fn='Client',
        class_method=False,
        overload_tags=['client'],
    ),
]


if __name__ == '__main__':
    tag_to_docstring = dict()
    all_changed_files = set()
    for d in entries:
        new_docstring = fill_overload(**d)
        tag_to_docstring.update(new_docstring)
        all_changed_files.add(d['filepath'])
    for d in implementation_stub_entries:
        fill_implementation_stub(**d, tag_to_docstring=tag_to_docstring)
        all_changed_files.add(d['filepath'])
    for f in all_changed_files:
        print(f)
