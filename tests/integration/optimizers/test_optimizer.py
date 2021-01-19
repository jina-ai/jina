import json
import os
import yaml

from google.protobuf.json_format import MessageToJson

from jina import Document
from jina.optimizers import OptunaOptimizer, EvaluationCallback
from jina.optimizers.flow_runner import SingleFlowRunner

BEST_PARAMETERS = {
    'JINA_DUMMYCRAFTER_PARAM1': 0,
    'JINA_DUMMYCRAFTER_PARAM2': 1,
    'JINA_DUMMYCRAFTER_PARAM3': 1,
}


def document_generator(num_doc):
    for _ in range(num_doc):
        doc = Document(content='hello')
        groundtruth_doc = Document(content='hello')
        yield doc, groundtruth_doc


def test_optimizer(tmpdir):
    eval_flow_runner = SingleFlowRunner(
        flow_yaml='tests/integration/optimizers/flow.yml',
        documents=document_generator(10),
        request_size=1,
        task='search',
        callback=EvaluationCallback(),
    )

    opt = OptunaOptimizer(
        flow_runner=eval_flow_runner,
        parameter_yaml='tests/integration/optimizers/parameter.yml',
        workspace_base_dir=str(tmpdir),
    )
    result = opt.optimize_flow(n_trials=10)
    result_path = str(tmpdir) + '/results/best_parameters.yml'
    result.save_parameters(result_path)
    parameters = result.best_parameters

    assert parameters == BEST_PARAMETERS
    assert yaml.load(open(result_path)) == BEST_PARAMETERS


def test_yaml(tmpdir):
    jsonlines_file = os.path.join(tmpdir, 'docs.jsonlines')
    optimizer_yaml = f'''
!OptunaOptimizer:
flow_runner:
  !SingleFlowRunner:
    flow_yaml: 'tests/integration/optimizers/flow.yml'
    documents: {jsonlines_file}
    request_size: 1
    task: 'search'
    callback: !EvaluationCallback
parameter_yaml: 'tests/integration/optimizers/parameter.yml'
workspace_base_dir: {tmpdir}
'''
    documents = document_generator(10)

    with open(jsonlines_file, 'w') as f:
        for document, groundtruth_doc in documents:
            json.dump(
                {
                    'document': MessageToJson(document).replace('\n', ''),
                    'groundtruth': MessageToJson(groundtruth_doc).replace('\n', ''),
                },
                f,
            )
            f.write('\n')

    with OptunaOptimizer.load_config(optimizer_yaml) as optimizer:
        result = optimizer.optimize_flow(n_trials=10)

        result_path = str(tmpdir) + '/results/best_parameters.yml'
        result.save_parameters(result_path)
        parameters = result.best_parameters

        assert parameters == BEST_PARAMETERS
        assert yaml.load(open(result_path)) == BEST_PARAMETERS
