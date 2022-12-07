(flow-yaml-spec)=
# {octicon}`file-code` YAML specification

To generate a YAML configuration from a {class}`~jina.Flow` Python object, use {meth}`~jina.jaml.JAMLCompatible.save_config`.

## YAML completion in IDE

We provide a [JSON Schema](https://json-schema.org/) for your IDE to enable code completion, syntax validation, members listing and displaying help text.

### PyCharm users

1. Click menu `Preferences` -> `JSON Schema mappings`;
2. Add a new schema, in the `Schema File or URL` write `https://api.jina.ai/schemas/latest.json`; select `JSON Schema Version 7`;
3. Add a file path pattern and link it to `*.jaml` or `*.jina.yml` or any suffix you commonly used for Jina Flow's YAML.

### VSCode users

1. Install the extension: `YAML Language Support by Red Hat`;
2. In IDE-level `settings.json` add:

```json
"yaml.schemas": {
    "https://api.jina.ai/schemas/latest.json": ["/*.jina.yml", "/*.jaml"],
}
```

You can bind Schema to any file suffix you commonly used for Jina Flow's YAML.

## Example YAML

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

Keyword arguments are passed to a Flow's `__init__()` method. You can set Flow-specific arguments and Gateway-specific arguments here:

#### Flow arguments

```{include} flow-args.md
```

#### Gateway arguments 

```{include} gateway-args.md
```


### `executors`
Collection of Executors used in the Flow.
Each item in the collection corresponds to on {meth}`~jina.Flow.add` call and specifies one Executor.

All keyword arguments passed to the Flow {meth}`~jina.Flow.add` method can be used here.

```{include} executor-args.md
```


## Variables

Jina Flow YAML supports variables and variable substitution according to the [Github Actions syntax](https://docs.github.com/en/actions/learn-github-actions/environment-variables):

### Environment variables

Use `${{ ENV.VAR }}` to refer to the environment variable `VAR`. You can find all {ref}`Jina environment variables here<jina-env-vars>`.

### Context variables

Use `${{ CONTEXT.VAR }}` to refer to the context variable `VAR`.
Context variables can be passed to `f.load_config(..., context=...)` in the form of a Python dictionary.

### Relative paths

Use `${{root.path.to.var}}` to refer to the variable `var` within the same YAML file, found at the provided path in the file's structure.
Note that the only difference between environment variable syntax and relative path syntax is the omission of spaces in the latter.
