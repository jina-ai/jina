(push-executor)=
# Publish Executor

If you want to share your Executors to other persons or colleges, you can push your local Executor to JinaHub.

(jina-hub-usage)=
## Basic push

```bash
jina hub push [--public/--private] <path_to_executor_folder>
```

```{figure} ../../../.github/hub-push.png
:align: center
```


It will return an **UUID** as well as a **SECRET**. You would need these two items when using or update the Executor later. **Please keep them carefully.**



````{admonition} Note
:class: note
When no `--public` or `--private` visibility options are provided. **By default, it's public.**
````

````{admonition} Important
:class: important
There is only one difference between `--public` and `--private`. You can use public Executor once you know the `UUID`, but you must know `SECRET` and `UUID` if you want to use a private Executor.
````


## Update a published Executor

Everything is iterating in Internet world. We also provide a way to update your existing Executor in JinaHub. To update one Executor, you must have both `UUID` and `SECRET`.

```bash
jina hub push [--public/--private] --force <UUID> --secret <SECRET> <path_to_executor_folder>
```


````{admonition} Note
:class: note
With `--public` option, the resulted Executor will be **visible to public**.
````

````{admonition} Note
:class: note
With `--private` options, the resulted Executor will be **invisible to public**.
````

## Advanced: tagging your published Executor

```bash
jina hub push <path_to_executor_folder> -t TAG1 -t TAG2 -f <path_to_dockerfile>
```



You can specify `-t` or `--tags` parameters to tag one Executor. In additional, you can specify `-f` or `--docker-file` parameters to use a specific docker file to build your Executor.

If there is no `-t` parameter provided, the default tag is `latest`. And if you provide `-t` parameters, and you still want to have `latest` tag, you must write it as one `-t` parameter.

```bash
jina hub push .                     # Result in one tag: latest
jina hub push . -t v1.0.0           # Result in one tag: v1.0.0
jina hub push . -t v1.0.0 -t latest # Result in two tags: v1.0.0, latest
```

If you want to make a new tag on the existing Executor, you can also add the `-t` option here:

```bash
jina hub push [--public/--private] --force <UUID> --secret <SECRET> -t TAG <path_to_executor_folder>
```
