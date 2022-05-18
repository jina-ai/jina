(flow-yaml-spec)=
# YAML specification

This page outlines the specification for valid Flow YAML files.

Such YAML configurations can be used to generate a Flow object via `Flow.load_config('flow.yml')`.

To generate a YAML configuration from a `Flow` Python object, run `f.save_config()`.

## Example

The following constitutes an example Flow configuration:

`flow.yml`/`flow.yaml`:
```yaml
jtype: Flow
version: '1'
with:
  protocol: http
metas:
  - py_modules:
      - executor.py
executors:
# inline Executor YAML
- name: firstexec
  uses:
    jtype: MyExec
    py_modules:
      - executor.py
# reference to Executor YAML
- name: secondexec
  uses: indexer.yml
  workspace: /home/johannes/.config/JetBrains/PyCharmCE2022.1/scratches/indexed
# reference to Executor Python class
- name: thirdexec
  uses: CustomExec  # located in executor.py
```

## Fields

### `jtype`
String that is always set to "Flow", indicating the corresponding Python class.

### `version`
String indicating the version of the Flow.

### `with`
Keyword arguments passed to the Flow `__init__()` method. A complete list of these arguments can be found [here](https://docs.jina.ai/api/jina.orchestrate.flow.base/#jina.orchestrate.flow.base.Flow),
or by running `jina flow --help`.

### `executors`
Collection of Executors used in the Flow.
Each item in the collection corresponds to on `f.add()` call and specifies one Executor.

All keyword arguments passed to the Flow `add()` method can be added.
A complete list of these arguments can be found [here](https://docs.jina.ai/api/jina.orchestrate.flow.base/#jina.orchestrate.flow.base.Flow.add).

**`uses`**

`uses` can take a direct reference to a Python class, or a path to an Executor YAML specification, equivalently the `f.add(uses=...)` pattern.

Alternatively, an Executor YAML configuration can be proved directly inline in the Flow YAML configuration, like shown in the example above.

### `metas`
Collection that overrides the `metas` attribute for all Executors in a Flow.
This can be useful when loading multiple Executors from the same Python file.