(hub-executor-best-practices)=
# Hub Executor Best Practices

When developing Hub Executors, make sure to follow these tips:

* Use `jina hub new` CLI to create an Executor
```{admonition} Hint
:class: hint
To get started, always use the command and follow the instructions. This will ensure you follow the right file 
structure.
```

* No need to write Dockerfile manually: Hubble will generate a well-optimized Dockerfile according to your Executor 
  package

```{admonition} Note
:class: note
Hubble is the Jina Hub building system
```

* No need to bump Jina version
```{admonition} Important
:class: important
Hub executors are version-agnostic. When you pull an Executor from Hub, Hubble will always select the right Jina 
version for you. No worries about Jina version upgrade!
```

* Fill in `manifest.yml` correctly. 

```{admonition} Hint
:class: hint
Information you include in `manifest.yml` will be displayed on our website.
Want to make your Executor eye-catching on our website ? Fill all fields in `manifest.yml` with heart & love!
```
