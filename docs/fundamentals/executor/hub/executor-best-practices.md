(hub-executor-best-practices)=
# Best practices

## Developing Hub Executors

When developing Hub Executors, make sure to follow these tips:

* Use `jina hub new` CLI to create an Executor

  To get started, always use the command and follow the instructions. This will ensure you follow the right file 
structure.

* No need to write Dockerfile manually 

  {abbr}`Hubble (Hubble is the Jina Hub building system)` will generate a well-optimized Dockerfile according to your Executor 
    package


* No need to bump Jina version

  Hub executors are version-agnostic. When you pull an Executor from Hub, Hubble will always select the right Jina 
version for you. No worries about Jina version upgrade!


* Fill in `manifest.yml` correctly. 

  Information you include in `manifest.yml` will be displayed on our website.
Want to make your Executor eye-catching on our website? Fill all fields in `manifest.yml` with heart & love!


## Using Hub Executors

When using Hub Executors, make sure to follow these tips:

* Ensure sufficient Docker resources are allocated when using `jinahub+docker`

  When `jinahub+docker` executors are not loading properly or are having issues during initialization, please ensure sufficient Docker resources are allocated.
