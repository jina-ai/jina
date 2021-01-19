import yaml

from jina import Document
from jina.optimizers import OptunaOptimizer, EvaluationCallback
from jina.optimizers.flow_runner import SingleFlowRunner


def test_optimizer(tmpdir):
    best_parameters = {'JINA_DUMMYCRAFTER_PARAM1': 0,
                       'JINA_DUMMYCRAFTER_PARAM2': 1,
                       'JINA_DUMMYCRAFTER_PARAM3': 1}

    def document_generator(num_doc):
        for _ in range(num_doc):
            doc = Document(content='hello')
            groundtruth_doc = Document(content='hello')
        yield doc, groundtruth_doc

    eval_flow_runner = SingleFlowRunner(
        flow_yaml='tests/integration/optimizers/flow.yml',
        documents=document_generator(10),
        request_size=1,
        task='search',
        callback=EvaluationCallback(),
    )

    opt = OptunaOptimizer(
        multi_flow=eval_flow_runner,
        parameter_yaml='tests/integration/optimizers/parameter.yml',
        workspace_base_dir=str(tmpdir)
    )
    result = opt.optimize_flow(n_trials=10)
    result_path = str(tmpdir) + '/results/best_parameters.yml'
    result.save_parameters(result_path)
    parameters = result.best_parameters

    assert parameters == best_parameters
    assert yaml.load(open(result_path)) == best_parameters
