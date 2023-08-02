import inspect
import re
import warnings
from operator import itemgetter
from typing import Optional, Tuple, List

from jina import Document


def get_properties(cls) -> List[Tuple[str, Optional[str], Optional[str]]]:
    src = inspect.getsource(cls)
    members = dict(inspect.getmembers(cls))
    setters = re.findall(
        r'@[a-zA-Z0-9_]+\.setter\s+def\s+([a-zA-Z0-9_]+)\s*\(self,\s*[a-zA-Z0-9_]+\s*:\s*(.*?)\)',
        src,
        flags=re.DOTALL,
    )

    property_docs = []
    for setter, _ in setters:
        if setter not in members:
            warnings.warn(
                f'{setter} is found as a setter but there is no corresponding getter'
            )
            property_docs.append(None)
        else:
            doc = inspect.getdoc(members[setter])
            description = next(iter(re.findall(':return:(.*)', doc)), None)
            if description:
                description = description.strip()
            property_docs.append(description)
    return sorted(
        list(
            zip(map(itemgetter(0), setters), map(itemgetter(1), setters), property_docs)
        ),
        key=lambda x: x[0],
    )


def get_overload_signature(
    properties,
    indent=' ' * 4,
):
    kwargs = [
        f'{indent}{indent}{property_name}: Optional[{type_hint}] = None'
        for property_name, type_hint, _ in properties
    ]
    args_str = ', \n'.join(kwargs + [f'{indent}{indent}**kwargs'])
    doc_str = '\n'.join(
        [
            f'{indent}{indent}:param {property_name}: {description}'
            for property_name, _, description in properties
        ]
        + [
            f'{indent}{indent}:param kwargs: other parameters to be set _after_ the document is constructed'
        ]
    )

    signature = f'def __init__(\n{indent}{indent}self,\n{args_str}\n{indent}):'
    final_str = f'@overload\n{indent}{signature}\n{indent}{indent}"""\n{doc_str}\n{indent}{indent}"""'

    return final_str


def write_signature(
    cls,
    overload_signature,
    tag,
    indent=' ' * 4,
):
    filepath = inspect.getfile(cls)
    final_code = re.sub(
        rf'(# overload_inject_start_{tag}).*(# overload_inject_end_{tag})',
        f'\\1\n{indent}{overload_signature}\n{indent}\\2',
        open(filepath).read(),
        0,
        re.DOTALL,
    )
    with open(filepath, 'w', encoding='utf-8') as fp:
        fp.write(final_code)


def inject_properties_as_overload(cls):
    properties = get_properties(cls)
    overload_signature = get_overload_signature(properties)
    write_signature(cls, overload_signature, 'document')
    print(inspect.getfile(cls))


if __name__ == '__main__':
    inject_properties_as_overload(Document)
