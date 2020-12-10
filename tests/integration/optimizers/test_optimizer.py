from .fashion.data import get_data
from .fashion.evaluation import index_document_generator, evaluation_document_generator

from jina.optimizers import OptunaOptimizer
from jina.optimizers.flow_runner import FlowRunner


def test_optimizer():
    """This will run complete optimisation.
    Todo: fix number of index and query doc so that test doesnt run long
    Todo: assert to check eval key and value for values generated in config/best_config.yml
    Todo: after optimisation is complete, assert to check trial pods and flows do not have any evironment variable.
          This can be checked by some of our current yaml related functions in flow runner
          and changing its functionality to assert values are not starting with $.
    """
    DATA_DIRECTORY = "data"

    data = get_data(DATA_DIRECTORY)

    flow_runner = FlowRunner(
        index_document_generator(1000, data),
        evaluation_document_generator(1000, data),
        500,
        500,
        "pods",
        env_yaml="flows/env.yml",
        overwrite_workspace=True,
    )

    opt = OptunaOptimizer(
        flow_runner,
        "flows/index.yml",
        "flows/evaluate.yml",
        "flows/parameter.yml",
    )

    opt.optimize_flow(n_trials=2)