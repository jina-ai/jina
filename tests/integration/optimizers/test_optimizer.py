from jina import Document
from jina.optimizers import OptunaOptimizer, EvaluationCallback
from jina.optimizers.flow_runner import FlowRunner, MultiFlowRunner

import yaml


def test_optimizer():
    best_config = {'JINA_DUMMYCRAFTER_PARAM1': 0, 
                    'JINA_DUMMYCRAFTER_PARAM2': 1, 
                    'JINA_DUMMYCRAFTER_PARAM3': 1}

    def document_generator(num_doc):
        for _ in range(num_doc):
            doc = Document(content='hello')
            groundtruth_doc = Document(content='hello')
        yield doc, groundtruth_doc

    eval_flow_runner = FlowRunner(
        flow_yaml='flow.yml',
        documents=document_generator(10),
        batch_size=1,
        task='search',
        callback=EvaluationCallback(),
    )

    multi_flow = MultiFlowRunner(eval_flow_runner)

    opt = OptunaOptimizer(
        multi_flow,
        'parameter.yml',
        best_config_filepath='config/best_config.yml',
    )
    config = opt.optimize_flow(n_trials=10)
    assert config == best_config

    assert yaml.load(open('config/best_config.yml')) == best_config