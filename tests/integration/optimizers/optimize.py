from fashion.data import get_data
from fashion.evaluation import index_document_generator, evaluation_document_generator

from jina.optimizers import OptunaOptimizer, EvaluationCallback
from jina.optimizers.flow_runner import FlowRunner

DATA_DIRECTORY = "data"


def main():
    data = get_data(DATA_DIRECTORY)

    index_flow_runner = FlowRunner(
        flow_yaml="flows/index.yml",
        documents=index_document_generator(1000, data),
        batch_size=500,
        pod_dir="pods",
        task="index",
        overwrite_workspace=True,
    )

    eval_flow_runner = FlowRunner(
        flow_yaml="flows/evaluate.yml",
        documents=evaluation_document_generator(1000, data),
        batch_size=500,
        pod_dir="pods",
        task="search",
        callback=EvaluationCallback(),
    )

    opt = OptunaOptimizer(
        index_flow_runner,
        eval_flow_runner,
        "flows/parameter.yml",
        best_config_filepath="config/best_config.yml",
        workspace_env="JINA_WORKSPACE",
    )
    opt.optimize_flow(n_trials=2)


if __name__ == "__main__":
    main()
