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

<script id="asciicast-tpvuZ9u0lU2IumRyLlly3JI93" src="https://asciinema.org/a/tpvuZ9u0lU2IumRyLlly3JI93.js" async></script>

If you have logged in Jina, it will return `TASK_ID`. You need that to get build status and logs. 

If you haven't logged in Jina, it will return `NAME` and `SECRET`. You will need them to use (if the Executor is private) or update the Executor. **Please keep them carefully.**

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
## Use environment variables

Sometimes you might want to use private token in `requirements.txt` to install private dependencies. For security reasons, you don't want to expose this token to anyone else. The `--build-env` parameter could help with this situation. For example, now we have `requirements.txt` like below: 

```txt
# requirements.txt
git+http://${YOUR_TOKEN}@github.com/your_private_repo 
```

When doing `jina hub push`, you can pass the `--build-env` parameter:

```bash
jina hub push --build-env YOUR_TOKEN=foo
```

````{admonition} Note
:class: note
There are restrictions in terms of naming environment variables:
- `{` and `}` is required when using environment variables in `requirements.txt`. e.g `$YOUR_TOKEN` doesn't work as expected. 
- Environment variables are limited to the uppercase letter and numbers and the `_` (underscore), not start with `_`. 
````

````{admonition} Limitations
:class: attention

There are limitations if you push Executors via `--build-env` and pull/use it as source code (but doesn't matter if you use docker image): 

- When you use `jina hub pull jinahub://YOUR_EXECUTOR`, you must set the corresponding environment variable according to the prompt.

  ```bash
  export YOUR_TOKEN=foo
  ```

- When you use `.add(uses='jinahub://YOUR_EXECUTOR')` in Flow, you must set the corresponding environment variable also. 
For example:

    ```python
    from jina import Flow, Executor, requests, Document
    import os

    os.environ["YOUR_TOKEN"] = 'foo'
    f = Flow().add(uses='jinahub://YOUR_EXECUTOR')

    with f:
        f.post(on='/', inputs=Document(), on_done=print)
    ```
````

For multiple environment variables, we can pass it in this way:

```bash
jina hub push --build-env FIRST=foo --build-env SECOND=bar
```

## Building status of an Executor 

You can query the build status of a pushed Executor by doing:

```bash
jina hub status [<path_to_executor_folder>] [--id TASK_ID] [--verbose] [--replay]
```

If set `--id TASK_ID`, you can get the build status of a specific build task.

If set `--verbose`, verbose build logs will be printed.

If set `--replay`, will print build status from the beginning.

<script id="asciicast-Asd8bQ9YqsuJBVV1V7EfWmCu3" src="https://asciinema.org/a/Asd8bQ9YqsuJBVV1V7EfWmCu3.js" async></script>