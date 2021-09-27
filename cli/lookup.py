from cli.export import api_to_dict


def _build_lookup_table():
    all_keywords = {}
    import copy

    def build_invert_index(d, usage='jina'):
        for k in d['methods']:
            usg = f'{usage} {k["name"]}'
            if 'methods' in k:
                build_invert_index(k, usage=usg)
            if k['name'] not in all_keywords:
                all_keywords[k['name']] = []
            _k = {'name': k['name'], 'type': 'command', 'usage': usg, 'help': k['help']}
            all_keywords[k['name']].append(_k)
            if 'options' in k:
                for kk in k['options']:
                    if kk['name'] not in all_keywords:
                        all_keywords[kk['name']] = []
                    _kk = copy.deepcopy(kk)
                    _kk['usage'] = usg
                    all_keywords[kk['name']].append(_kk)

    def build_noisy_index(d):
        noise2key = {}
        for k, z in d.items():
            for v in z:
                noises = [k]
                noises.append(v.get('name', []))
                noises.extend(v.get('option_strings', []))
                dash_to_space = [k.replace('-', ' ').replace('_', ' ') for k in noises]
                no_dash = [k.replace('-', '').replace('_', '') for k in noises]
                no_leading_dash = [k.replace('--', '') for k in noises]
                noises.extend(dash_to_space)
                noises.extend(no_dash)
                noises.extend(no_leading_dash)
                no_ending_plural = [k[:-1] if k.endswith('s') else k for k in noises]
                noises.extend(no_ending_plural)
                for kk in set(noises):
                    noise2key[kk] = k
        return noise2key

    build_invert_index(api_to_dict(show_all_args=True))
    nkw2kw = build_noisy_index(all_keywords)
    return nkw2kw, all_keywords


def _prettyprint_help(d, also_in=None):
    from jina.helper import colored

    if d['type'] == 'command':
        print(
            f'''
    {colored(d['name'], attrs='bold')} is a CLI command of Jina.
    
    {colored(d['help'], attrs='bold')}
    
    More info: {d['usage']} --help
        '''
        )
    else:
        availables = '  '.join(
            colored(v, attrs='underline')
            for v in (set(h['usage'] for h in also_in) if also_in else {d['usage']})
        )
        option_str = '  '.join(colored(v, attrs='bold') for v in d['option_strings'])
        if option_str:
            option_str = f'as {option_str}'

        table = {}
        table['Type'] = d['type']
        table['Required'] = d['required']
        if d['choices']:
            table['Choices'] = ' | '.join(d['choices'])
        if not d['default_random'] and d['default'] is not None:
            table['Default'] = d['default']
        if d['default_random']:
            table['Remark'] = colored(
                'This argument has a random default value!', 'yellow'
            )

        table_str = '\n    '.join(
            f'{k + ": " + colored(v, attrs="bold")}' for k, v in table.items()
        )

        lb = '\033[F'
        import argparse

        print(
            f'''
    {colored(d['name'], attrs='bold')} is {colored('an internal CLI of Jina, should not be used directly', color='yellow') if d['help'] == argparse.SUPPRESS else 'a CLI argument of Jina.'}. 
    It is available in {availables} {option_str}
    
    {colored(d['help'], attrs='bold') if d['help'] != argparse.SUPPRESS else lb * 2}

    {table_str}
        '''
        )


def lookup_and_print(query: str):
    """Lookup argument name in Jina API and prettyprint the result.

    :param query: the argument (fuzzy) name
    """

    nkw2kw, kw2info = _build_lookup_table()
    if query not in nkw2kw:
        from jina.helper import colored

        print(
            f'Can not find argument {colored(query, attrs="bold")}, '
            f'maybe it\'s a misspelling or Jina does not have this argument.'
        )
    else:
        helps = kw2info[nkw2kw[query]]  # type: list
        if len(helps) == 1:
            _prettyprint_help(helps[0])
        elif len(helps) > 1 and len(set(h['help'] for h in helps)) == 1:
            _prettyprint_help(helps[0], also_in=helps)
        elif len(helps) > 1:
            from collections import defaultdict
            from jina.helper import colored

            help_group = defaultdict(list)
            for h in helps:
                help_group[h['help']].append(h)

            print(
                colored(f'Found {len(help_group)} mentions in Jina API.', attrs='dark')
            )

            for hg in help_group.values():
                _prettyprint_help(hg[0], also_in=hg)
                print(colored('─' * 40, attrs='dark'))
