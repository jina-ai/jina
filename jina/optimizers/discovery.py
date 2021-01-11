import os
import shutil

from jina.executors import BaseExecutor
from jina.logging import default_logger as logger
from jina.jaml import JAML


def _read_file(filename):
    with open(filename, "r") as file:
        return file.readlines()


def _extract_executor_files(flows):
    executor_files = set()
    for flow_file, flow_definition in flows.items():
        flow_directory = os.path.dirname(flow_file)
        for line in flow_definition:
            stripped = line.strip()
            if stripped.startswith("uses") or stripped.startswith("- uses"):
                executor_file = stripped.split(":", 1)[1].strip()
                executor_files.add(os.path.join(flow_directory, executor_file))
    return executor_files


def _extract_parameters(executor_yml):
    try:
        with BaseExecutor.load_config(executor_yml) as executor:
            if hasattr(executor, "DEFAULT_OPTIMIZATION_PARAMETER"):
                default_config = executor.DEFAULT_OPTIMIZATION_PARAMETER
            else:
                default_config = {}
            return default_config
    except TypeError:
        logger.warning(
            f"Failing building from {executor_yml}. All environment variables in {executor_yml} must be defined!"
        )


def print_parameter(discovered_parameters):
    for filename, (
        encoder_name,
        default_parameters,
    ) in discovered_parameters.items():
        print(f"Default .yaml configurations for {filename}:{encoder_name}:")
        print("with:")
        for parameter, value in default_parameters.items():
            print(f"    {parameter}: {value}")


def _replace_parameters(executor_yml, default_parameters):
    for parameter in default_parameters:
        if "\nwith:\n" not in executor_yml:
            executor_yml = executor_yml + "\nwith:\n"
        if f"{parameter.parameter_name}:" in executor_yml:
            logger.warning(
                f"Skipping the following parameter, since it is already defined: {parameter.parameter_name}"
            )
            continue
        executor_yml = executor_yml.replace(
            "\nwith:\n",
            f"\nwith:\n  {parameter.parameter_name}: ${parameter.env_var}\n",
        )
    return executor_yml


def _write_new_executors(executor_configurations):
    for executor_file, default_parameters in executor_configurations.items():
        full_content = "".join(_read_file(executor_file))
        content_with_parameter = _replace_parameters(full_content, default_parameters)
        _write_to(executor_file, content_with_parameter)


def _write_optimization_parameter(
    executor_configurations, target_file, overwrite_parameter_file
):
    output = [
        parameter for config in executor_configurations.values() for parameter in config
    ]

    if os.path.exists(target_file) and not overwrite_parameter_file:
        logger.warning(
            f"{target_file} already exists. Skip writing. Please remove it before parameter discovery."
        )
    else:
        with open(target_file, "w") as outfile:
            JAML.dump(output, outfile)


def _write_to(filepath, content, create_backup=True):
    if create_backup:
        shutil.move(filepath, f"{filepath}.backup")
    with open(filepath, "w", encoding="utf8") as new_file:
        new_file.write(content)


def run_parameter_discovery(flow_files, target_file, overwrite_parameter_file):
    flows = {flow_file: _read_file(flow_file) for flow_file in flow_files}
    executor_files = _extract_executor_files(flows)
    executor_configurations = {}
    for file in executor_files:
        optimization_parameter = _extract_parameters(file)
        if optimization_parameter:
            executor_configurations[file] = optimization_parameter

    _write_new_executors(executor_configurations)
    _write_optimization_parameter(
        executor_configurations, target_file, overwrite_parameter_file
    )


def config_global_environment():
    os.environ.setdefault("JINA_WORKSPACE", "workspace_discovery")
    os.environ.setdefault("JINA_MYENCODER_TARGET_DIMENSION", "64")


def main():
    config_global_environment()

    run_parameter_discovery(
        flow_files=["flows/index.yml", "flows/evaluate.yml"],
        target_file="flows/parameter.yml",
        overwrite_parameter_file=True,
    )


if __name__ == "__main__":
    main()
