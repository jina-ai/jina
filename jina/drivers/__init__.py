import sys
from collections import defaultdict
from typing import List
from typing import Tuple, Union, Callable, Dict

from pkg_resources import resource_filename

from ..excepts import WaitPendingMessage, DriverNotInstalled, BadDriverGroup, NoRequestHandler
from ..helper import yaml
from ..proto import jina_pb2

if False:
    # fix type-hint complain for sphinx and flake
    from ..peapods.pea import Pea

_req_key_map = {
    'ControlRequest': jina_pb2.Request.ControlRequest,
    'IndexRequest': jina_pb2.Request.IndexRequest,
    'TrainRequest': jina_pb2.Request.TrainRequest,
    'SearchRequest': jina_pb2.Request.SearchRequest,
    '/': [jina_pb2.Request.IndexRequest,
          jina_pb2.Request.TrainRequest,
          jina_pb2.Request.SearchRequest]
}


class Driver:
    """Driver is an intermediate layer between :class:`jina.executors.BaseExecutor` and
     :class:`jina.peapods.pea.Pea`. It is protobuf- and context-aware. A ``Driver`` reads the protobuf message
     and extracts the required information using ``handler`` or ``hook``, and then feed to an ``Executor``.
     After the result is returned, the driver will change the protobuf message accordingly and handover to ``Pea``.

     .. note:: Rationale and Goals

         The call chain here is as follows:

         Pea/Pod -> Driver (specified by a driver map config) -> Handlers/Hooks -> Executor (specified by the compound yaml
         config).

         Thus, the handler function is either designed to knows what executor's function to call, or it receives a function
         name specified by the driver map.

         Goal 1: we don't want to frequently change handlers, hooks and executors. Sometimes we can't change their code (in
         a different language or in a docker image).

         Goal 2: the naming of a compound route is quite arbitrary, we want to restrict such arbitrary in the yaml config
         file, not in the actual code.
    """

    def __init__(self, pea: 'Pea' = None, driver_yaml_path: str = None, driver_group: str = None,
                 install_default: bool = True):
        """

        :param pea: a :class:`jina.peapods.pea.Pea` object the driver attached to
        :param driver_yaml_path: the yaml file path to the driver map
        :param driver_group: a group of drivers to be installed
        :param install_default: install default handlers and hooks to this driver

        A ``driver_map`` must have two fields ``drivers``. Below is an YAML example:

        .. highlight:: yaml
        .. code-block:: yaml

            drivers:
              encode:
                handlers:
                  /:
                    - handler_encode_doc
                help: encode documents into embeddings

        - ``drivers``: a mapping grouped by name and handler-group

            - ``handlers``: a mapping grouped by events and handlers:
                `ControlRequest`, `IndexRequest`, `TrainRequest`, `SearchRequest`, note ``/`` represents all types of requests

                - list of function names, functions will be called in this order
            - ``help``: help text of this driver group

        """

        self._handlers = defaultdict(list)
        self._pre_hooks, self._post_hooks = [], []
        if pea:
            self.attach_to(pea)

        self.pending_msgs = defaultdict(list)  # type: Dict[str, List]

        # always install the default handler
        driver_map = self.install_from_config(
            resource_filename('jina', '/'.join(('resources', 'drivers.default.yml'))),
            'default') if install_default else None

        # if given, then install the given handler
        if not driver_yaml_path:
            driver_yaml_path = resource_filename('jina', '/'.join(('resources', 'drivers.default.yml')))
        if driver_group:
            # self.logger.info('driver %s from %s to be installed' % (driver_yaml_path, driver_group))
            self.install_from_config(driver_yaml_path, driver_group, driver_map)
        # else:
        #     self.logger.warning('no driver is installed, this Pod/Pea can only handle control request then')

    def attach_to(self, pea: 'Pea'):
        """Attach this driver to a Pea

        :param pea: :class:`Pea` to attach
        """
        self.context = pea
        self.logger = self.context.logger

    def install_from_config(self, driver_yaml_path: str, driver_group: str, driver_map: Dict = None) -> Dict:
        """ Install a group of handlers, pre- and post-hooks into this driver from a YAML config file

        :param driver_yaml_path: the yaml file path to the driver map, ``drivers`` field is required
        :param driver_group: a group of drivers to be installed
        :param driver_map: the existing driver map to be built on
        :return: loaded driver map from the yaml file, which can be used in the proceeding :func:`install_from_config`

        Example YAML spec:

        .. highlight:: yaml
        .. code-block:: yaml

            drivers:
              dummyA:
                handlers:
                  ControlRequest:
                    - handler_control_req
                pre_hooks:
                  - hook_add_route_to_msg
                post_hooks:
                  - hook_update_timestamp
                help: the default driver configurations for all

              encode:
                handlers:
                  /:
                    - handler_encode_doc
                help: encode documents into embeddings
        """
        if not driver_map:
            driver_map = {}

        if isinstance(driver_yaml_path, str):
            with open(driver_yaml_path, encoding='utf8') as fp:
                driver_map.update(yaml.load(fp)['drivers'])
        else:
            with driver_yaml_path:
                driver_map.update(yaml.load(driver_yaml_path)['drivers'])

        if driver_group in driver_map:
            self.install(driver_map[driver_group])
        else:
            raise BadDriverGroup('can not find %s in the driver group from %s' % (driver_group, driver_yaml_path))

        return driver_map

    def install(self, driver_group: Dict) -> None:
        """ Install a group of handlers, pre- and post-hooks into this driver_group

        :param driver_group: the driver_group map to be installed

        Example YAML spec:

        .. highlight:: yaml
        .. code-block:: yaml

          encode:
            handlers:
              /:
                - handler_encode_doc
            help: encode documents into embeddings

        """

        if 'handlers' in driver_group:
            for k, v in driver_group['handlers'].items():
                self.add_handlers(import_driver_fns(funcs=v), _req_key_map[k])

        if 'pre_hooks' in driver_group:
            self.add_pre_hook(import_driver_fns(funcs=driver_group['pre_hooks']))

        if 'post_hooks' in driver_group:
            self.add_pre_hook(import_driver_fns(funcs=driver_group['post_hooks']))

    def verify(self):
        """ Validate this driver to check if it is usable, otherwise raise a ``DriverNotInstalled`` exception
        """
        if not self._handlers or not self.context:
            raise DriverNotInstalled

    def add_handlers(self, f: Union[Tuple[Callable, str], List[Tuple[Callable, str]]],
                     req_type: Union[List, Tuple, type] = (jina_pb2.Request.IndexRequest,
                                                           jina_pb2.Request.TrainRequest,
                                                           jina_pb2.Request.SearchRequest)):
        """Add new handlers to this driver

        :param f: the function or list of functions. The function must follow the signature of a ``handler``.
        :param req_type: the request type to bind
        """

        if not isinstance(f, list):
            f = [f]

        if isinstance(req_type, list) or isinstance(req_type, tuple):
            for m in req_type:
                self._handlers[m].extend(f)
        else:
            self._handlers[req_type].extend(f)

    def add_pre_hook(self, f: Union[Tuple[Callable, str], List[Tuple[Callable, str]]]):
        """Add a pre-handler hook to this driver. This hooks will be invoked *before* handling the message.

        :param f: the function or list of functions. The function must follow the signature of a ``hook``.
        """

        if not isinstance(f, list):
            f = [f]
        self._pre_hooks.extend(f)

    def add_post_hook(self, f: Union[Tuple[Callable, str], List[Tuple[Callable, str]]]):
        """Add a post-handler hook to this driver. This hooks will be invoked *after* handling the message.

        :param f: the function or list of functions. The function must follow the signature of a ``hook``.
        """
        if not isinstance(f, list):
            f = [f]

        self._post_hooks.extend(f)

    def do_handlers(self, msg: 'jina_pb2.Message', *args, **kwargs):
        """Apply the handler functions on the message

        :param msg: the protobuf message to be applied on
        """
        req = getattr(msg.request, msg.request.WhichOneof('body'))
        msg_type = type(req)

        fns = self._handlers[msg_type]

        if fns:
            self.logger.debug('handling message with %r' % fns)

            if self.context.args.num_part > 1 and msg_type != jina_pb2.Request.ControlRequest:
                # do not wait for control request
                req_id = msg.envelope.request_id
                self.pending_msgs[req_id].append(msg)
                num_req = len(self.pending_msgs[req_id])

                if num_req == self.context.args.num_part:
                    prev_msgs = self.pending_msgs.pop(req_id)
                    prev_reqs = [getattr(v.request, v.request.WhichOneof('body')) for v in prev_msgs]
                else:
                    self.logger.debug('waiting for %d/%d %s messages' % (num_req, self.context.args.num_part, msg_type))
                    raise WaitPendingMessage
            else:
                prev_reqs = None
                prev_msgs = None

            for fn, exec_fn in fns:
                if exec_fn and hasattr(self.context, 'executor'):
                    exec_fn = getattr(self.context.executor, exec_fn)
                else:
                    exec_fn = None
                fn(exec_fn, self.context, req, msg, prev_reqs, prev_msgs, *args, **kwargs)
        else:
            raise NoRequestHandler(msg_type)

    def do_pre_hooks(self, msg: 'jina_pb2.Message', *args, **kwargs):
        """Apply the pre-handler hook functions to the message

        :param msg: the protobuf message to be applied on
        """
        self._do_hooks(msg)

    def do_post_hooks(self, msg: 'jina_pb2.Message', *args, **kwargs):
        """Apply the post-handler hook functions to the message

        :param msg: the protobuf message to be applied on
        """
        self._do_hooks(msg, pre=False)

    def _do_hooks(self, msg: 'jina_pb2.Message', pre: bool = True, *args, **kwargs):
        for fn, _ in (self._pre_hooks if pre else self._post_hooks):
            try:
                fn(self.context, msg, *args, **kwargs)
            except Exception as ex:
                self.logger.warning('the %s-hook function %r throws an exception, '
                                    'this wont affect the server but you may want to pay attention' % (
                                        'pre' if pre else 'post', fn))
                self.logger.error(ex, exc_info=True)

    def callback(self, msg: 'jina_pb2.Message'):
        """Apply the complete callback cycle pre->handler->post to the message.

        :param msg: the protobuf message to be applied on
        """
        self.do_pre_hooks(msg)
        self.do_handlers(msg)
        self.do_post_hooks(msg)
        return msg


def import_driver_fns(path: str = __path__[0], namespace: str = 'jina.drivers',
                      funcs: List[Union[str, Dict]] = None,
                      show_import_table: bool = False, import_once: bool = False) -> List[Tuple[Callable, str]]:
    """ Import all or selected driver functions into the runtime

    :param path: the package path for search
    :param namespace: the namespace to add given the ``path``
    :param funcs: the list of function names to import
    :param show_import_table: show the import result as a table
    :param import_once: import everything only once, to avoid repeated import
    :return: a list of driver functions found

    """

    from .. import JINA_GLOBAL
    if import_once and JINA_GLOBAL.drivers_imported:
        return []

    from setuptools import find_packages
    from pkgutil import iter_modules

    modules = set()

    for info in iter_modules([path]):
        if not info.ispkg:
            modules.add('.'.join([namespace, info.name]))

    for pkg in find_packages(path):
        modules.add('.'.join([namespace, pkg]))
        pkgpath = path + '/' + pkg.replace('.', '/')
        if sys.version_info.major == 2 or (sys.version_info.major == 3 and sys.version_info.minor < 6):
            for _, name, ispkg in iter_modules([pkgpath]):
                if not ispkg:
                    modules.add('.'.join([namespace, pkg, name]))
        else:
            for info in iter_modules([pkgpath]):
                if not info.ispkg:
                    modules.add('.'.join([namespace, pkg, info.name]))

    if funcs:
        load_fns = [None] * len(funcs)  # type: List[Tuple[Callable, str]]
        func_names = {}  # type: Dict[str, Tuple]
        for idx, k in enumerate(funcs):
            if isinstance(k, str):
                func_names[k] = idx, None
            elif isinstance(k, dict):
                func_names[list(k.keys())[0]] = idx, list(k.values())[0]
            else:
                raise TypeError('%r is not a string or dict ' % type(k))
    else:
        func_names = None
    load_stat = defaultdict(list)
    bad_imports = []

    import importlib
    for m in modules:
        try:
            mod = importlib.import_module(m)
            for k in dir(mod):
                # import the class
                if callable(getattr(mod, k)) and (not func_names or (k in func_names)):
                    try:
                        _f = getattr(mod, k)
                        load_stat[m].append((k, True, ''))
                        if func_names and (k in func_names):
                            load_fns[func_names[k][0]] = _f, func_names[k][1]
                            if None not in load_fns:
                                return load_fns  # target execs are all found and loaded, return
                    except Exception as ex:
                        load_stat[m].append((k, False, ex))
                        bad_imports.append('.'.join([m, k]))
                        if k in funcs:
                            raise ex  # target fns is found but not loaded, raise return
        except Exception as ex:
            load_stat[m].append(('', False, ex))
            bad_imports.append(m)

    if show_import_table:
        from ..helper import print_load_table
        print_load_table(load_stat)
    else:
        if bad_imports:
            from jina.logging import default_logger
            default_logger.error('theses modules or classes can not be imported %s' % bad_imports)

    if funcs and (None in load_fns):
        raise ImportError('funcs %s result in %s can not be found in %s (%s)' % (funcs, load_fns, namespace, path))

    JINA_GLOBAL.drivers_imported = True
