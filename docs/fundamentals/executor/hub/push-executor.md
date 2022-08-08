(push-executor)=
# Publish

If you want to share your {class}`~jina.Executor`s, you can push it to Jina Hub.

There are two types of sharing:
- **Public** (default): Anyone can use public Executors without any restrictions.
- **Private**: Only people that have the `secret` can use private Executors. 

(jina-hub-usage)=
## First publish

```bash
jina hub push [--public/--private] <path_to_executor_folder>
```

```{figure} screenshots/hub-push.gif
:align: center
```


It will return `NAME` & `SECRET`, which you will need to use (if the Executor is private) or update the Executor. **Please keep them carefully.**

````{admonition} Note
:class: note
If you are logged in to the Hub using our CLI tools (`jina auth login` or `jcloud login`), you can push and pull your executors without `SECRET`.
````

You can then visit [the Hub portal](https://hub.jina.ai), click on the "Recent" tab and see your published Executor.

````{admonition} Note
:class: note
If no `--public` or `--private` argument is provided, then it is **public** by default.
````

````{admonition} Important
:class: important
Anyone can use public Executors, but to use a private Executor you must know its `SECRET`.
````


## Update published Executors

To override or update a published Executor, you must have both `NAME` and `SECRET`.

```bash
jina hub push [--public/--private] --force-update <NAME> --secret <SECRET> <path_to_executor_folder>
```

(hub_tags)=
## Tagging an Executor

Tagging can be useful for versioning Executors or differentiating them by their architecture (e.g. `gpu`, `cpu`).

```bash
jina hub push <path_to_executor_folder> -t TAG1 -t TAG2
```

You can specify `-t` or `--tags` parameter to tag an Executor.

- If you **don't** add the `-t` parameter, the default tag is `latest`
- If you **do** add the `-t` parameter and you still want to have the `latest` tag, you must write it as another `-t` parameter.

```bash
jina hub push .                     # Result in one tag: latest
jina hub push . -t v1.0.0           # Result in one tag: v1.0.0
jina hub push . -t v1.0.0 -t latest # Result in two tags: v1.0.0, latest
```

If you want to create a new tag for an existing Executor, you can also add the `-t` option here:

```bash
jina hub push [--public/--private] --force-update <NAME> --secret <SECRET> -t TAG <path_to_executor_folder>
```

### Protected tags

If you don’t want some tags to be later overwritten to keep a stable, consistent behavior, 
protected tags are the exact thing you are looking for.

You can leverage the `--protected-tag` option to create protected tags. 
After being pushed for the first time, the protected tags can not be pushed again.

```bash
jina hub push [--public/--private] --force-update <NAME> --secret <SECRET> --protected-tag <PROTECTED_TAG_1> --protected-tag <PROTECTED_TAG_2> <path_to_executor_folder>
```

### Set environment variables

If you want to set environment variables in your requirements.txt file when building the executor. Only needs two steps:

The first step:  
In requirements.txt, you must ensure two things:
1. Environment variables that contain a `$` aren't accidentally (partially) expanded.
2. Environment variables are limited to the uppercase letter and numbers and the `_` (underscore), not start with `_`. 

For example in your requirements.txt file:
```file
git+http://${FIRST_TOKEN}.github.com/your_private_repo 
git+http://${SECOND_TOKEN}.github.com/your_private_repo
```

The second step:  
You can leverage the `--build-env` option to set environment variables when you use `jina hub push`. And you must ensure one thing:
1. Environment variables are limited to the uppercase letter and numbers and the `_` (underscore), not start with `_`. 

For example when you use `jina hub push`:
```bash
jina hub push --build-env TOKEN=YOUR_ENV_VALUE # Set an environment variable
jina hub push --build-env FIRST_TOKEN=YOUR_ENV_VALUE SECOND_TOKEN=YOUR_ENV_VALUE # Set multiple environment variables
```

````{admonition} Attention
:class: attention

If you leverage the `--build-env` set environment variables in your executor. There some limited things:

- When you use `jina hub pull jinahub://YOUR_EXECUTOR`, you must set the corresponding environment variable According to the prompt.
```linux
export YOUR_ENV_VARIABLES=YOUR_ENV_VALUE # linux  
```

- When you use `.add(uses='jinahub://YOUR_EXECUTOR')` in Flow, you must set the corresponding environment variable also. 
For example:

```python
from docarray import Document
from jina import Flow, Executor, requests
import os

os.environ["YOUR_ENV_VARIABLES"]=YOUR_ENV_VALUE
f = Flow().add(uses='jinahub://YOUR_EXECUTOR')

with f:
f.post(on='/', inputs=Document(), on_done=print)
```
````