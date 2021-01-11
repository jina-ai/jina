import os

from jina.optimizers.parameters import (
    IntegerParameter,
    FloatParameter,
    LogUniformParameter,
    UniformParameter,
    CategoricalParameter,
    DiscreteUniformParameter,
    load_optimization_parameters,
)

import pytest


arg_dict = [
    (
        IntegerParameter,
        {
            'executor_name': 'executor',
            'low': 0,
            'high': 10,
            'step_size': 1,
            'log': False,
            'parameter_name': 'dummy_param',
        },
        {
            'name': 'JINA_EXECUTOR_DUMMY_PARAM',
            'low': 0,
            'high': 10,
            'step': 1,
            'log': False,
        },
    ),
    (
        FloatParameter,
        {
            'executor_name': 'executor',
            'low': 0,
            'high': 10,
            'step_size': 1,
            'log': False,
            'parameter_name': 'dummy_param',
        },
        {
            'name': 'JINA_EXECUTOR_DUMMY_PARAM',
            'low': 0,
            'high': 10,
            'step': 1,
            'log': False,
        },
    ),
    (
        UniformParameter,
        {
            'executor_name': 'executor',
            'low': 0,
            'high': 10,
            'parameter_name': 'dummy_param',
        },
        {
            'name': 'JINA_EXECUTOR_DUMMY_PARAM',
            'low': 0,
            'high': 10,
        },
    ),
    (
        LogUniformParameter,
        {
            'executor_name': 'executor',
            'low': 0,
            'high': 10,
            'parameter_name': 'dummy_param',
        },
        {
            'name': 'JINA_EXECUTOR_DUMMY_PARAM',
            'low': 0,
            'high': 10,
        },
    ),
    (
        CategoricalParameter,
        {
            'executor_name': 'executor',
            'choices': ['a', 'b'],
            'parameter_name': 'dummy_param',
        },
        {
            'name': 'JINA_EXECUTOR_DUMMY_PARAM',
            'choices': ['a', 'b'],
        },
    ),
    (
        DiscreteUniformParameter,
        {
            'executor_name': 'executor',
            'low': 0,
            'high': 10,
            'q': 0.1,
            'parameter_name': 'dummy_param',
        },
        {'name': 'JINA_EXECUTOR_DUMMY_PARAM', 'low': 0, 'high': 10, 'q': 0.1},
    ),
]


@pytest.mark.parametrize('paramter_class, inputs, outputs', arg_dict)
def test_parameters(paramter_class, inputs, outputs):
    param = paramter_class(**inputs)
    assert param.to_optuna_args() == outputs


def test_parameter_file_loading():
    params_loaded = load_optimization_parameters(
        os.path.join(os.path.dirname(__file__), 'parameters.yml')
    )
    expected = [
        IntegerParameter,
        FloatParameter,
        UniformParameter,
        UniformParameter,
        LogUniformParameter,
        CategoricalParameter,
        DiscreteUniformParameter,
    ]
    for param, param_type in zip(params_loaded, expected):
        assert type(param) == param_type
