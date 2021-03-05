import json
import os

import pytest
import yaml
from google.protobuf.json_format import MessageToJson

from jina import Document
from jina.jaml import JAML
from jina.optimizers import FlowOptimizer, MeanEvaluationCallback
from jina.optimizers import run_optimizer_cli
from jina.optimizers.flow_runner import SingleFlowRunner, MultiFlowRunner
from jina.parsers.optimizer import set_optimizer_parser

cur_dir = os.path.dirname(os.path.abspath(__file__))

BEST_PARAMETERS = {
    'JINA_DUMMYCRAFTER_PARAM1': 0,
    'JINA_DUMMYCRAFTER_PARAM2': 1,
    'JINA_DUMMYCRAFTER_PARAM3': 1,
}


@pytest.fixture
def config(tmpdir):
    os.environ['JINA_OPTIMIZER_WORKSPACE_DIR'] = str(tmpdir)
    os.environ['JINA_OPTIMIZER_PARAMETER_FILE'] = os.path.join(cur_dir, 'parameter.yml')
    os.environ['JINA_OPTIMIZER_DATA_FILE'] = os.path.join(cur_dir, 'data.jsonlines')
    yield
    del os.environ['JINA_OPTIMIZER_WORKSPACE_DIR']
    del os.environ['JINA_OPTIMIZER_PARAMETER_FILE']
    del os.environ['JINA_OPTIMIZER_DATA_FILE']


def validate_result(result, tmpdir):
    result_path = os.path.join(tmpdir, 'out/best_parameters.yml')
    result.save_parameters(result_path)
    assert result.best_parameters == BEST_PARAMETERS
    assert yaml.load(open(result_path)) == BEST_PARAMETERS


def document_generator(num_doc):
    for _ in range(num_doc):
        doc = Document(content='hello')
        groundtruth_doc = Document(content='hello')
        yield doc, groundtruth_doc


def test_optimizer_single_flow(tmpdir, config):
    eval_flow_runner = SingleFlowRunner(
        flow_yaml=os.path.join(cur_dir, 'flow.yml'),
        documents=document_generator(10),
        request_size=1,
        execution_method='search',
    )
    opt = FlowOptimizer(
        flow_runner=eval_flow_runner,
        parameter_yaml=os.path.join(cur_dir, 'parameter.yml'),
        evaluation_callback=MeanEvaluationCallback(),
        workspace_base_dir=str(tmpdir),
        n_trials=5,
    )
    result = opt.optimize_flow()
    validate_result(result, tmpdir)


def test_optimizer_multi_flow(tmpdir, config):
    multi_flow_runner = MultiFlowRunner(
        [
            SingleFlowRunner(
                flow_yaml=os.path.join(cur_dir, 'flow.yml'),
                documents=document_generator(10),
                request_size=1,
                execution_method='index',
            ),
            SingleFlowRunner(
                flow_yaml=os.path.join(cur_dir, 'flow.yml'),
                documents=document_generator(10),
                request_size=1,
                execution_method='search',
            ),
        ]
    )
    opt = FlowOptimizer(
        flow_runner=multi_flow_runner,
        parameter_yaml=os.path.join(cur_dir, 'parameter.yml'),
        evaluation_callback=MeanEvaluationCallback(),
        workspace_base_dir=str(tmpdir),
        n_trials=5,
    )
    result = opt.optimize_flow()
    validate_result(result, tmpdir)


def test_yaml_multi_flow(tmpdir, config):
    jsonlines_file = os.path.join(tmpdir, 'docs.jsonlines')
    optimizer_yaml = f'''!FlowOptimizer
version: 1
with:
  flow_runner: !MultiFlowRunner
    with:
      flows:
        - !SingleFlowRunner
          with:
            flow_yaml: '{os.path.join(cur_dir, 'flow.yml')}'
            documents: {jsonlines_file}
            request_size: 1
            execution_method: 'index_lines'
            documents_parameter_name: 'filepath'
        - !SingleFlowRunner
          with:
            flow_yaml: '{os.path.join(cur_dir, 'flow.yml')}'
            documents: {jsonlines_file}
            request_size: 1
            execution_method: 'search_lines'
            documents_parameter_name: 'filepath'
  evaluation_callback: !MeanEvaluationCallback {{}}
  parameter_yaml: '{os.path.join(cur_dir, 'parameter.yml')}'
  workspace_base_dir: {tmpdir}
  n_trials: 5
'''
    documents = document_generator(10)
    with open(jsonlines_file, 'w') as f:
        for document, groundtruth_doc in documents:
            document.id = ""
            groundtruth_doc.id = ""
            json.dump(
                {
                    'document': json.loads(MessageToJson(document).replace('\n', '')),
                    'groundtruth': json.loads(
                        MessageToJson(groundtruth_doc).replace('\n', '')
                    ),
                },
                f,
            )
            f.write('\n')

    optimizer = JAML.load(optimizer_yaml)
    result = optimizer.optimize_flow()
    validate_result(result, tmpdir)


def test_yaml_single_flow(tmpdir, config):
    jsonlines_file = os.path.join(tmpdir, 'docs.jsonlines')
    optimizer_yaml = f'''!FlowOptimizer
version: 1
with:
  flow_runner: !SingleFlowRunner
    with:
      flow_yaml: '{os.path.join(cur_dir, 'flow.yml')}'
      documents: {jsonlines_file}
      request_size: 1
      execution_method: 'search_lines'
      documents_parameter_name: 'filepath'
  evaluation_callback: !MeanEvaluationCallback {{}}
  parameter_yaml: '{os.path.join(cur_dir, 'parameter.yml')}'
  workspace_base_dir: {tmpdir}
  n_trials: 5
'''
    documents = document_generator(10)
    with open(jsonlines_file, 'w') as f:
        for document, groundtruth_doc in documents:
            document.id = ""
            groundtruth_doc.id = ""
            json.dump(
                {
                    'document': json.loads(MessageToJson(document).replace('\n', '')),
                    'groundtruth': json.loads(
                        MessageToJson(groundtruth_doc).replace('\n', '')
                    ),
                },
                f,
            )
            f.write('\n')

    optimizer = JAML.load(optimizer_yaml)
    result = optimizer.optimize_flow()
    validate_result(result, tmpdir)


@pytest.mark.parametrize('uses_output_dir', (True, False))
def test_cli(tmpdir, config, uses_output_dir):
    print(os.environ['JINA_OPTIMIZER_PARAMETER_FILE'])
    args = ['--uses', os.path.join(cur_dir, 'optimizer_conf.yml')]
    output_dir = os.path.join(tmpdir, 'out')
    if uses_output_dir:
        args.extend(['--output-dir', output_dir])
    run_optimizer_cli(set_optimizer_parser().parse_args(args))
    if uses_output_dir:
        assert (
            yaml.load(open(os.path.join(output_dir, 'best_parameters.yml')))
            == BEST_PARAMETERS
        )
