(executor-yaml-spec)=
# {octicon}`file-code` YAML specification

This page outlines the Executor YAML file specification. These configurations can be used in a {class}`~jina.Deployment` with `Deployment(uses='exec.yml)` or loaded directly via `Executor.load_config('exec.yml')`.

Note that Executor YAML configuration always refers back to an Executor defined in a Python file.

## Example

The following is an example {class}`~jina.Executor` configuration:

```yaml
jtype: MyExecutor
with:
  match_args: {}
py_modules:
  - executor.py
metas:
  name: Indexer
  description: Indexes all Documents
  url: https://github.com/janedoe/indexer
  keywords: ['indexer', 'executor']
```

## Keywords

### `jtype`
String specifying the Executor's Python type. Used to locate the correct class in the Python files given by `py_modules`.

(executor-with-keyword)
### `with`
Collection containing keyword arguments passed to the Executor's `__init__()` method. Valid values depend on the Executor.

### `py_modules`
List of strings defining the Executor's Python dependencies. Most notably this must include the Python file containing the Executor definition itself, as well as any other files it imports.

### `metas`
Collection containing meta-information about the Executor.

Your Executor is annotated with this information when publishing to {ref}`Executor Hub <jina-hub>`. To get better appeal on Executor Hub, set the `metas` fields to the correct values:

- **`name`**: Human-readable name of the Executor.
- **`description`**: Human-readable description of the Executor. 
- **`url`**: URL of where to find more information about the Executor, normally a GitHub repo URL.
- **`keywords`**: A list of strings to help users filter and locate your package.
