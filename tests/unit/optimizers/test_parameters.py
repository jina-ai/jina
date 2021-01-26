import os

from jina.optimizers.parameters import (
    IntegerParameter,
    LogUniformParameter,
    UniformParameter,
    CategoricalParameter,
    DiscreteUniformParameter,
    load_optimization_parameters,
)


def test_parameter_file_loading():
    params_loaded = load_optimization_parameters(
        os.path.join(os.path.dirname(__file__), 'parameters.yml')
    )
    expected = [
        IntegerParameter,
        UniformParameter,
        UniformParameter,
        LogUniformParameter,
        CategoricalParameter,
        DiscreteUniformParameter,
    ]
    for param, param_type in zip(params_loaded, expected):
        assert type(param) == param_type
