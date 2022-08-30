(executor-yaml-spec)=
# {octicon}`file-code` YAML specification

This page outlines the specification for valid Executor YAML files.

Such YAML configurations can be used in a Flow via `Flow().add(uses='exec.yml')`, or loaded directly via `Executor.load_config('exec.yml')`.

Note that Executor YAML configurations always refer back to an Executor defined in a Python file.

## Example

The following constitutes an example {class}`~jina.Executor` configuration:

```yaml
jtype: MyExecutor
with:
  match_args: {}
py_modules:
  - executor.py
metas:
  name: Indexer
  description: Indexes all documents
manifest:
  manifest_version: 1
  name: MyIndexer
  description: Indexes all documents
  url: https://github.com/janedoe/indexer
  keywords: ["indexer", "executor"]
```

## Keywords

### `jtype`
String specifying the Python type of the Executor. Used to locate the correct class in the Python files given by `py_modules`.

### `with`
Collection containing keyword arguments passed to the Executor's `__init__()` method. Valid values depend on the Executor.

### `py_modules`
List of strings defining the Python dependencies of the Executor. Most notably this must include the Python file that contains the Executor definition itself, as well as any other files imported by this.

### `metas`
Collection containing meta information about the Executor.

- **`name`**: String that defines the name of the Executor.
- **`description`**: String that describes the Executor.

### `manifest`
Optional collection containing meta information about the Executor relevant to Jina Hub. 

When publishing an executor (`jina hub push ...`), your executor will be annoted with this information so that it can be better managed by the Hub system.

To get better appeal on Jina Hub, you may want to carefully set the manifest fields to the correct values:

- **`manifest_version`**: The version of the manifest protocol.
- **`name`**: Human-readable name of the Executor.
- **`description`**: Human-readable description of the Executor. 
- **`url`**: URL of where to find more information about the Executor, normally a GitHub repo URL.
- **`keywords`**: A list of strings to help users filter and locate your package.