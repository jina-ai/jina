import json

from jina.orchestrate.flow.base import Flow
from jina.orchestrate.deployments import Deployment
from jina.jaml import JAML
from jina.logging.predefined import default_logger
from jina.schemas import get_full_schema
from jina_cli.export import api_to_dict


def export_kubernetes(args):
    """Export to k8s yaml files

    :param args: args from CLI
    """
    from jina.jaml import JAMLCompatible

    obj = JAMLCompatible.load_config(args.config_path)

    if isinstance(obj, (Flow, Deployment)):
        obj.to_kubernetes_yaml(
            output_base_path=args.outpath, k8s_namespace=args.k8s_namespace
        )
    else:
        raise NotImplementedError(f'Object of class {obj.__class__.__name__} cannot be exported to Kubernetes')


def export_docker_compose(args):
    """Export to Docker compose yaml files

    :param args: args from CLI
    """

    from jina.jaml import JAMLCompatible

    obj = JAMLCompatible.load_config(args.config_path)

    if isinstance(obj, (Flow, Deployment)):
        obj.to_docker_compose_yaml(
            output_path=args.outpath, network_name=args.network_name
        )
    else:
        raise NotImplementedError(f'Object of class {obj.__class__.__name__} cannot be exported to Docker Compose')


def export_flowchart(args):
    """Export to flowchart file

    :param args: args from CLI
    """
    Flow.load_config(args.config_path).plot(
        args.outpath, vertical_layout=args.vertical_layout
    )


def export_schema(args):
    """Export to JSON Schemas

    :param args: args from CLI
    """
    from jina import __version__
    if args.yaml_path:
        dump_api = api_to_dict()
        for yp in args.yaml_path:
            f_name = (yp % __version__) if '%s' in yp else yp
            with open(f_name, 'w', encoding='utf8') as fp:
                JAML.dump(dump_api, fp)
            default_logger.info(f'API is exported to {f_name}')

    if args.json_path:
        dump_api = api_to_dict()
        for jp in args.json_path:
            f_name = (jp % __version__) if '%s' in jp else jp
            with open(f_name, 'w', encoding='utf8') as fp:
                json.dump(dump_api, fp, sort_keys=True)
            default_logger.info(f'API is exported to {f_name}')

    if args.schema_path:
        dump_api = get_full_schema()
        for jp in args.schema_path:
            f_name = (jp % __version__) if '%s' in jp else jp
            with open(f_name, 'w', encoding='utf8') as fp:
                json.dump(dump_api, fp, sort_keys=True)
            default_logger.info(f'API is exported to {f_name}')
