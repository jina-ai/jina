import re
from collections import defaultdict

import yaml


def get_extra_requires(path):
    try:
        with open(path) as fp:
            extra_deps = defaultdict(set)
            for k in fp:
                if k.strip() and not k.startswith('#'):
                    tags = set()
                    if ':' in k:
                        k, v = k.split(':')
                        tags.update(vv.strip() for vv in v.split(','))

                    k = re.split('([<>=])', k, 1)

                    # If we have some version requrement, it will be returned as a
                    # separate item by the split function
                    if len(k) == 3:
                        k = [k[0], k[1] + k[2]]
                    assert len(k) <= 2, 'requirement should not have more than 2 parts'

                    # Can not use extra requirements in conda - i.e. uvicorn[standard]
                    k[0] = re.sub(r'\[\w\]', '', k[0])

                    # The docker package is docker-py on conda-forge
                    if k[0] == 'docker':
                        k[0] = 'docker-py'

                    # In conda recipe pkg name and version must be separated by space
                    k = ' '.join(k)

                    for t in tags:
                        extra_deps[t].add(k)

        return extra_deps
    except FileNotFoundError:
        return {}


class RecipeDumper(yaml.SafeDumper):
    """Adds a line break between top level objects and ignore aliases"""

    def write_line_break(self, data=None):
        super().write_line_break(data)
        if len(self.indents) == 1:
            super().write_line_break()

    def ignore_aliases(self, data):
        return True


extra_deps = get_extra_requires('extra-requirements.txt')
reqs = {}

# core < perf < standard < daemon
reqs['core'] = extra_deps['core']
reqs['perf'] = reqs['core'].union(extra_deps['perf'])
reqs['standard'] = reqs['perf'].union(extra_deps['standard'])
reqs['daemon'] = reqs['standard'].union(extra_deps['daemon'])

# Make all the others a diff from core:
for key in reqs:
    if key != 'core':
        reqs[key] = reqs[key] - reqs['core']


# Create yaml file as a dictionary
test_object = {
    'requires': ['pip'],
    'imports': ['jina'],
    'commands': ['pip check', 'jina --version'],
}
build_object = {
    'entry_points': ['jina = cli:main', 'jinad = daemon:main'],
    'script': 'python -m pip install . --no-deps -vv',
}
recipe_object = {
    'package': {'name': '{{ name|lower }}', 'version': '{{ version }}'},
    'source': {
        'url': 'https://pypi.io/packages/source/{{ name[0] }}/{{ name }}/{{ name }}-{{ version }}.tar.gz',
        'sha': 'malinki, malinki ;)',
    },
    'build': {'number': 0},
    'outputs': [
        {
            'name': 'jina-core',
            'build': build_object,
            'test': test_object,
            'requirements': {
                'host': ['python >=3.7', 'pip'],
                'run': ['python'] + list(reqs['core']),
            },
        },
        {
            'name': 'jina-perf',
            'test': test_object,
            'requirements': {
                'host': ['python >=3.7', 'pip'],
                'run': ['python >=3.7', "{{ pin_subpackage('jina-core', exact=True) }}"]
                + list(reqs['perf']),
            },
        },
        {
            'name': 'jina',  # standard
            'test': test_object,
            'requirements': {
                'host': ['python >=3.7', 'pip'],
                'run': ['python >=3.7', "{{ pin_subpackage('jina-core', exact=True) }}"]
                + list(reqs['standard']),
            },
        },
        {
            'name': 'jina-daemon',
            'test': test_object,
            'requirements': {
                'host': ['python >=3.7', 'pip'],
                'run': ['python >=3.7', "{{ pin_subpackage('jina-core', exact=True) }}"]
                + list(reqs['daemon']),
            },
        },
    ],
    'about': {
        'home': 'https://github.com/jina-ai/jina/',
        'license': 'Apache-2.0',
        'license_family': 'Apache',
        'license_file': 'LICENSE',
        'description': 'Jina is the cloud-native neural search framework for any kind of data',
        'doc_url': 'https://docs.jina.ai',
    },
    'extra': {'recipe-maintainers': ['tadejsv', 'maateen', 'nan-wang', 'hanxiao']},
}


with open('conda/recipe.yaml', 'w+') as fp:
    yaml.dump(
        recipe_object,
        stream=fp,
        Dumper=RecipeDumper,
        width=1000,
        sort_keys=False,
        default_style=None,
    )
