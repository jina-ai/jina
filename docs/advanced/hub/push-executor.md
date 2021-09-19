(push-executor)=
# Publish Executor

If you want to share your Executors to other persons or colleges, you can push your local Executor to the Hub.

There are two types of sharing:
- **Public** (default): anyone can use the public executors without any restriction.
- **Private**: only people that has the `secret` can use the private executors. 

(jina-hub-usage)=
## First publish

```bash
jina hub push [--public/--private] <path_to_executor_folder>
```

```{figure} screenshots/hub-push.gif
:align: center
```


It will return `UUID` & `SECRET`, which you will need when using (if private) or update the Executor later. **Please keep them carefully.**

You can then visit [the Hub portal](https://hub.jina.ai), click on the "Recent" tab and see your published Executor.

````{admonition} Note
:class: note
If no `--public` or `--private` visibility option is provided, then it is **public** by default.
````

````{admonition} Important
:class: important
Anyone can use any public Executor, but to use a private Executor one must know `SECRET`.
````


## Update published Executors

To override or update a published Executor, you must have both `UUID` and `SECRET`.

```bash
jina hub push [--public/--private] --force <UUID> --secret <SECRET> <path_to_executor_folder>
```

(hub_tags)=
## Tagging Executor

Tagging can be useful for versioning Executors; or differing Executors by their architectures (e.g. `gpu`, `cpu`).

```bash
jina hub push <path_to_executor_folder> -t TAG1 -t TAG2
```

You can specify `-t` or `--tags` parameters to tag one Executor.

If there is no `-t` parameter provided, the default tag is `latest`. And if you provide `-t` parameters, and you still want to have `latest` tag, you must write it as one `-t` parameter.

```bash
jina hub push .                     # Result in one tag: latest
jina hub push . -t v1.0.0           # Result in one tag: v1.0.0
jina hub push . -t v1.0.0 -t latest # Result in two tags: v1.0.0, latest
```

If you want to create a new tag for an existing Executor, you can also add the `-t` option here:

```bash
jina hub push [--public/--private] --force <UUID> --secret <SECRET> -t TAG <path_to_executor_folder>
```
