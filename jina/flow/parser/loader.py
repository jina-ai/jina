"""
# loader function format

    def load_v_MAJOR[_MINOR](data)
    e.g.
        - def load_v_1_1(data)
        - def load_v_1(data)

# match priority
    if version is available:
        - load_v_MAJOR_MINOR
        - load_v_MAJOR
        - throw BadFlowYAMLVersion
    otherwise:
        - load_v_legacy
"""

from typing import Dict, Any

from .. import Flow
from ...helper import expand_env_var


def load_v_legacy(data):
    p = data.get('with', {})  # type: Dict[str, Any]
    a = p.pop('args') if 'args' in p else ()
    k = p.pop('kwargs') if 'kwargs' in p else {}
    # maybe there are some hanging kwargs in "parameters"
    tmp_a = (expand_env_var(v) for v in a)
    tmp_p = {kk: expand_env_var(vv) for kk, vv in {**k, **p}.items()}
    obj = Flow(*tmp_a, **tmp_p)

    pp = data.get('pods', {})
    for pod_name, pod_attr in pp.items():
        p_pod_attr = {kk: expand_env_var(vv) for kk, vv in pod_attr.items()}
        if pod_name != 'gateway':
            # ignore gateway when reading, it will be added during build()
            obj.add(name=pod_name, **p_pod_attr, copy_flow=False)
    # if node.tag in {'!CompoundExecutor'}:
    #     os.environ['JINA_WARN_UNNAMED'] = 'YES'
    return obj


def load_v_1(data):
    p = data.get('with', {})  # type: Dict[str, Any]
    a = p.pop('args') if 'args' in p else ()
    k = p.pop('kwargs') if 'kwargs' in p else {}
    # maybe there are some hanging kwargs in "parameters"
    tmp_a = (expand_env_var(v) for v in a)
    tmp_p = {kk: expand_env_var(vv) for kk, vv in {**k, **p}.items()}
    obj = Flow(*tmp_a, **tmp_p)

    pp = data.get('pods', [])
    for pods in pp:
        p_pod_attr = {kk: expand_env_var(vv) for kk, vv in pods.items()}
        # in v1 YAML, flow is an optional argument
        if p_pod_attr.get('name', None) != 'gateway':
            # ignore gateway when reading, it will be added during build()
            method = p_pod_attr.get('method', 'add')
            # support methods: add, needs, inspect
            getattr(obj, method)(**p_pod_attr, copy_flow=False)
    return obj
