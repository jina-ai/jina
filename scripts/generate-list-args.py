from jina.schemas.helper import _cli_to_schema
from jina_cli.export import api_to_dict

for s in ('flow', 'gateway', 'executor'):
    a = _cli_to_schema(api_to_dict(), s)

    table = ['| Name | Description | Type | Default |', '|----|----|----|----|']

    for k, v in a[f'Jina::{s.capitalize()}']['properties'].items():
        desc = v["description"].replace("\n", "<br>")
        if k in ('port', 'port_monitoring'):
            v[
                'default'
            ] = 'random in [49152, 65535]'  # avoid random numbers cause devbot forever committing
        table.append(f'| `{k}` | {desc} | `{v["type"]}` | `{v["default"]}` |')

    with open(f'../docs/concepts/flow/{s}-args.md', 'w') as fp:
        fp.write('\n'.join(table))
