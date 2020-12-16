# Jina API Schema for 3rd-Party Applications


Every time [jina-ai/jina](https://github.com/jina-ai/jina) is updated or released, the schema of Jina command line interface is exposed to JSON and YAML files. They can be used or referred in the 3rd-party applications. For example, [our dashboard](https://dashboard.jina.ai) is using this schema to arrange UI elements. The schema is tagged with [the Jina's version](https://github.com/jina-ai/jina/blob/master/RELEASE.md#version-explained). 

## Schema URL

- [`https://api.jina.ai/latest`](https://api.jina.ai/latest) gives you the latest stable API schema (corresponds to the last Sunday release) in JSON
- [`https://api.jina.ai/devel`](https://api.jina.ai/devel) gives you the latest development API schema (corresponds to the last master update of [jina-ai/jina](https://github.com/jina-ai/jina) in JSON

```bash
➜ curl https://api.jina.ai/devel

{"authors": "dev-team@jina.ai", "description": "Jina is the cloud-native neural search solution powered by state-of-the-art AI and deep learning technology", "docs": "https://docs.jina.ai", "license": "Apache 2.0", "methods": [{"name": "pod", "options": [{"choices": null, "default": null, "default_random": false, "help": "the name of this pea, used to identify the pod and its logs.", "name": "name", "option_strings": ["--name"], "required": false, "type": "str"},
```

You can specify the version and the schema format via:

```text
https://api.jina.ai/VER.json
https://api.jina.ai/VER.yml
```

where `VER` is [the Jina's version](https://github.com/jina-ai/jina/blob/master/RELEASE.md#version-explained), e.g. [`https://api.jina.ai/0.1.5.yml`](https://api.jina.ai/0.1.5.yml)


## Description

| Field | Description |
| --- | --- |
|`.methods[]`|  All subcommands under `jina` |
|`.methods[].name`|  The name of the subcommand  |
|`.methods[].options[]`|  All arguments of a subcommand  |
|`.methods[].options[].choices[]`| If it is non-empty list, then the value of this argument must be one of which |
|`.methods[].options[].default`| Default value, when not given, then default is a Python `None` |
|`.methods[].options[].default_random`|  If `true`, then the `default` is random value that changes on each run. In this case you tell the user `default` is just a random valid value, not a fixed value  |
|`.methods[].options[].help`| Help text of that option  |
|`.methods[].options[].name`|  The name of the argument  |
|`.methods[].options[].option_strings[]`|  The argument name in CLI, often starts with `--`  |
|`.methods[].options[].required`|  If this option is required  |
|`.methods[].options[].type`|  The Python type of this option  |
|`.name`| `Jina`   |
|`.revision`| VCS short commit tag |
|`.source`| `https://github.com/jina-ai/jina/tree/{.revision}` |
|`.url`|  `https://jina.ai`  |
|`.vendor`|  `Jina AI Limited`  |
|`.version`| Jina version given by `jina -v`  |
|`.authors`|  `dev-team@jina.ai`  |
|`.description`|  `Jina is the cloud-native neural search solution powered by state-of-the-art AI and deep learning technology`  |
|`.docs`|  `https://docs.jina.ai`  |
|`.license`|   `Apache 2.0` |
