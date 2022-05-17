(executor-yaml-spec)=
# YAML specification

This page outlines the specification for valid Executor YAML files.
Such YAML configurations can be used in a Flow via `Flow().add(uses='exec.yml')`, or loaded directly via `BaseExecutor.load_config('exec.yml')`.
Note that Executor YAML configurations always refer back to an Executor defined in a Python file.

## Example

The following constitutes a typical Executor configuration:

`exec.yml`/`exec.yaml`:
```yaml
jtype: MyExecutor
with:
  match_args: {}
metas:
  py_modules:
    - executor.py
  workspace: my/workspace/
  name: Indexer
  description: Indexes all documents
```

## Fields

- `jtype`
String specifying the Python type of the Executor

- `with` TODO is `uses_with` a synonym?
Collection containing keyword arguments passed to the Executor's `__init__()` method

- `metas`
Collection containing special internal attributes of the Executor
  - `py_modules` List of strings defining the Python dependencies of the Executor. Most notably this has to contain the
  Python file that contains the Executor definition itself, as well as any other files imported by this.
  - `name` String that defines the name of the Executor
  - `description` String that describes the Executor
  - `workspace` Filepath to the workspace of the Executor, i.e. the directory it can save and load data to and from.

