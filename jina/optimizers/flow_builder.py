from jina import Flow


class FlowBuilder:
    def __init__(self, flow_yaml_template: str, *args, **kwargs):
        self._flow_yaml_template = flow_yaml_template

    def _build_from_params(self, params):
        return params

    def build(self, params) -> 'Flow':
        trial_parameters = self._build_from_params(params)
        print(f' context {trial_parameters}')
        return Flow.load_config(self._flow_yaml_template, context=trial_parameters)
