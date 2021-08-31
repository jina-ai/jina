## Pull Executor

`Pull` means fetching the Executor content to your local machine. For each Executor, there are two different format content for user to pull.

### Fetch Docker image

```bash
$ jina hub pull jinahub+docker://<UUID>[:<SECRET>][/<TAG>]
```

You can find the Executor by running this command `docker images`. You can also indicate which version of the Executor you want to use by naming the `/<TAG>`.

```bash
$ jina hub pull jinahub+docker://DummyExecutor/v1.0.0
```

### Fetch the source code

```bash
$ jina hub pull jinahub://<UUID>[:<SECRET>][/<TAG>]
```

It will store Executor source code to `~/.jina/hub-packages`.


```{admonition} Note
:class: note
- For public Executor, you can ignore the `SECRET` option.
- For private Executor, you must provide the `SECRET` option.
```