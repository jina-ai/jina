import inspect
import re
import sys
from collections import defaultdict

from jina import Document

all_meth = defaultdict(list)
for f in inspect.getmembers(Document):
    if (
        callable(f[1])
        and not f[1].__name__.startswith('_')
        and not f[0].startswith('_')
    ):
        if 'return' in inspect.getfullargspec(f[1]).annotations and str(
            inspect.getfullargspec(f[1]).annotations['return']
        ) in ('~T', 'T'):
            module_name = f[1].__qualname__.split('.')[0].replace('Mixin', '')
            desc = inspect.getdoc(
                vars(sys.modules[f[1].__module__])[f[1].__qualname__.split('.')[0]]
            )

            all_meth[
                (
                    module_name,
                    desc.strip()
                    .replace(':class:', '{class}')
                    .replace(':attr:', '{attr}'),
                )
            ].append(f'{{meth}}`~{f[1].__module__}.{f[1].__qualname__}`')

all_s = []
for k, v in all_meth.items():
    all_s.append(f'### {k[0].strip()}')
    all_s.append(f'{k[1].strip()}')
    for vv in v:
        all_s.append(f'- {vv}')

    all_s.append('\n')


doc_md = '../docs/fundamentals/document/fluent-interface.md'
text = '\n'.join(all_s)

with open(doc_md, encoding='utf-8') as fp:
    _old = fp.read()
    _new = re.sub(
        r'(<!-- fluent-interface-start -->\s*?\n).*(\n\s*?<!-- fluent-interface-end -->)',
        rf'\g<1>{text}\g<2>',
        _old,
        flags=re.DOTALL,
    )

with open(doc_md, 'w', encoding='utf-8') as fp:
    fp.write(_new)
