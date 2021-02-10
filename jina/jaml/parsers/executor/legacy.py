import os
import inspect
from typing import Dict, Any, Type, Set
from functools import reduce

from ..base import VersionedYAMLParser
from ....executors import BaseExecutor, get_default_metas
from ....executors.compound import CompoundExecutor


class LegacyParser(VersionedYAMLParser):
    version = 'legacy'  # the version number this parser designed for

    @staticmethod
    def _get_all_arguments(class_):
        """

        :param class_: target class from which we want to retrieve arguments
        :return: all the arguments of all the classes from which `class_` inherits
        """
        def get_class_arguments(class_):
            """
            :param class_: the class to check
            :return: a list containing the arguments from `class_`
            """
            signature = inspect.signature(class_.__init__)
            class_arguments = [p.name for p in signature.parameters.values()]
            return class_arguments

        def accumulate_classes(cls) -> Set[Type]:
            """
            :param cls: the class to check
            :return: all classes from which cls inherits from
            """
            def _accumulate_classes(c, cs):
                cs.append(c)
                if cls == object:
                    return cs
                for base in c.__bases__:
                    _accumulate_classes(base, cs)
                return cs
            
            classes = []
            _accumulate_classes(cls, classes)
            return set(classes)

        all_classes = accumulate_classes(class_)
        args = list(map(lambda x: get_class_arguments(x), all_classes))
        return set(reduce(lambda x,y: x+y,args))

    @staticmethod
    def _get_dump_path_from_config(meta_config: Dict):
        if 'name' in meta_config:
            work_dir = meta_config['workspace']
            name = meta_config['name']
            pea_id = meta_config['pea_id']
            if work_dir:
                # then try to see if it can be loaded from its regular expected workspace (ref_indexer)
                dump_path = BaseExecutor.get_shard_workspace(work_dir, name, pea_id)
                bin_dump_path = os.path.join(dump_path, f'{name}.bin')
                if os.path.exists(bin_dump_path):
                    return bin_dump_path

            root_work_dir = meta_config['root_workspace']
            root_name = meta_config['root_name']
            if root_name != name:
                # try to load from the corresponding file as if it was a CompoundExecutor, if the `.bin` does not exist,
                # we should try to see if from its workspace can be loaded as it may be a `ref_indexer`
                compound_work_dir = CompoundExecutor.get_component_workspace_from_compound_workspace(root_work_dir,
                                                                                                     root_name,
                                                                                                     pea_id)
                dump_path = BaseExecutor.get_shard_workspace(compound_work_dir, name, pea_id)
                bin_dump_path = os.path.join(dump_path, f'{name}.{"bin"}')
                if os.path.exists(bin_dump_path):
                    return bin_dump_path

    def parse(self, cls: Type['BaseExecutor'], data: Dict) -> 'BaseExecutor':
        """
        :param cls: target class type to parse into, must be a :class:`JAMLCompatible` type
        :param data: flow yaml file loaded as python dict
        :return: the Flow YAML parser given the syntax version number
        """
        _meta_config = get_default_metas()
        _meta_config.update(data.get('metas', {}))
        if _meta_config:
            data['metas'] = _meta_config

        dump_path = self._get_dump_path_from_config(data.get('metas', {}))
        load_from_dump = False
        if dump_path:
            obj = cls.load(dump_path)
            obj.logger.success(f'restore {cls.__name__} from {dump_path}')
            # consider the case where `dump_path` is not based on `obj.workspace`. This is needed
            # for
            workspace_loaded_from = data.get('metas', {})['workspace']
            workspace_in_dump = getattr(obj, 'workspace', None)
            if workspace_in_dump != workspace_loaded_from:
                obj.workspace = workspace_loaded_from
            load_from_dump = True
        else:
            cls._init_from_yaml = True

            if cls.store_args_kwargs:
                p = data.get('with', {})  # type: Dict[str, Any]
                a = p.pop('args') if 'args' in p else ()
                k = p.pop('kwargs') if 'kwargs' in p else {}
                # maybe there are some hanging kwargs in "parameters"
                # tmp_a = (expand_env_var(v) for v in a)
                # tmp_p = {kk: expand_env_var(vv) for kk, vv in {**k, **p}.items()}
                tmp_a = a
                tmp_p = {kk: vv for kk, vv in {**k, **p}.items()}
                obj = cls(*tmp_a, **tmp_p, metas=data.get('metas', {}), requests=data.get('requests', {}))
            else:
                # tmp_p = {kk: expand_env_var(vv) for kk, vv in data.get('with', {}).items()}
                obj = cls(**data.get('with', {}), metas=data.get('metas', {}), requests=data.get('requests', {}))
            cls._init_from_yaml = False

            # check if the yaml file used to instanciate 'cls' has arguments that are not in 'cls'
            arguments_from_cls = LegacyParser._get_all_arguments(cls)
            arguments_from_yaml = set(data.get('with', {}))
            difference_set = arguments_from_yaml  - arguments_from_cls
            if any(difference_set):
                obj.logger.warning(f'The arguments {difference_set} defined in the YAML are not expected in the '
                                   f'class {cls.__name__}')

            obj.logger.success(f'successfully built {cls.__name__} from a yaml config')

        # if node.tag in {'!CompoundExecutor'}:
        #     os.environ['JINA_WARN_UNNAMED'] = 'YES'

        if not _meta_config:
            obj.logger.warning(
                '"metas" config is not found in this yaml file, '
                'this map is important as it provides an unique identifier when '
                'persisting the executor on disk.')

        # for compound executor
        if not load_from_dump and 'components' in data:
            obj.components = lambda: data['components']

        obj.is_updated = False
        return obj

    def dump(self, data: 'BaseExecutor') -> Dict:
        """
        :param data: versioned executor object
        :return: the dictionary given a versioned flow object
        """
        # note: we only save non-default property for the sake of clarity
        _defaults = get_default_metas()
        p = {k: getattr(data, k) for k, v in _defaults.items() if getattr(data, k) != v}
        a = {k: v for k, v in data._init_kwargs_dict.items() if k not in _defaults}
        r = {}
        if a:
            r['with'] = a
        if p:
            r['metas'] = p

        if hasattr(data, '_drivers'):
            r['requests'] = {'on': data._drivers}

        if hasattr(data, 'components'):
            r['components'] = data.components
        return r
