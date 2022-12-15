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
  workspace: /home/my/workspace
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


## Variables

Jina Flow YAMLs support variables and variable substitution according to the [Github Actions syntax](https://docs.github.com/en/actions/learn-github-actions/environment-variables).

This means that the following variable substitutions are supported:

### Environment variables

Use `${{ ENV.VAR }}` to refer to the environment variable `VAR`.

## Context variables

Use `${{ CONTEXT.VAR }}` to refer to the context variable `VAR`.
Context variables can be passed to `f.load_config(..., context=...)` in the form of a Python dictionary.

## Relative paths

Use `${{root.path.to.var}}` to refer to the variable `var` within the same YAML file, found at the provided path in the file's structure.
Note that the only difference between environment variable syntax and relative path syntax is the omission of spaces in the latter.
