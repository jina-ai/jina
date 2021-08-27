## 3. Update Executor in JinaHub

### 3.1 Basic

Everything is iterating in Internet world. We also provide a way to update your existing Executor in JinaHub. To update one Executor, you must have both `UUID` and `SECRET`.

```bash
$ jina hub push [--public/--private] --force <UUID> --secret <SECRET> <path_to_executor_folder>
```

````{admonition} Note
:class: note
With `--public` option, the resulted Executor will be **visible to public**.
````

````{admonition} Note
:class: note
With `--private` options, the resulted Executor will be **invisible to public**.
````

### 3.2 Advanced

If you want to make a new tag on the existing Executor, you can also add the `-t` option here:

```bash
$ jina hub push [--public/--private] --force <UUID> --secret <SECRET> -t TAG <path_to_executor_folder>
```
