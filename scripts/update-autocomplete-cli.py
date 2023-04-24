ac_file = '../jina_cli/autocomplete.py'


def _update_autocomplete():
    from jina.parsers import get_main_parser

    def _gaa(key, parser):
        _result = {}
        _compl = []
        for v in parser._actions:
            if v.option_strings:
                _compl.extend(v.option_strings)
            elif v.choices:
                _compl.extend(v.choices)
                if isinstance(v.choices, dict):
                    for kk, vv in v.choices.items():
                        _result.update(_gaa(' '.join([key, kk]).strip(), vv))
        # filer out single dash, as they serve as abbrev
        _compl = [k for k in _compl if (not k.startswith('-') or k.startswith('--'))]
        _result.update({key: _compl})
        return _result

    compl = _gaa('', get_main_parser())
    cmd = compl.pop('')
    compl = {'commands': cmd, 'completions': compl}

    with open(ac_file, 'w', encoding='utf-8') as fp:
        fp.write(f'ac_table = {compl}\n')


if __name__ == '__main__':
    _update_autocomplete()
