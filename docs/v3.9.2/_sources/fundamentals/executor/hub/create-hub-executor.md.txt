(create-executor)=
# Create

To create your Hub {class}`~jina.Executor`, you just need to run:

```bash
jina hub new
```

<script id="asciicast-T98aWaJLe0r0ul3cXGk7AzqUs" src="https://asciinema.org/a/T98aWaJLe0r0ul3cXGk7AzqUs.js" async></script>

For the basic configuration (advanced configuration is optional but rarely necessary), you will be asked for two things: 

- Name of your Executor 
- Path to the folder where it should be saved. 

After running the command, a project with the following structure will be generated:

```text
MyExecutor/
├── executor.py
├── config.yml
├── README.md
├── requirements.txt
└── Dockerfile
```

- `executor.py` should contain your Executor's main logic.
- `config.yml` is the Executor's {ref}`configuration <executor-yaml-spec>` file, where you can define `__init__` arguments using `with` keyword. You can also define meta annotations relevant to the executor, for getting better exposer on Jina Hub.
- `requirements.txt` describes the Executor's Python dependencies.
- `README.md` should describe how to use your Executor.
- `Dockerfile` will only be generated once you request advanced configuration.


## Tips


When developing Hub {class}`~jina.Executor`s, make sure to follow these tips:

* Use `jina hub new` CLI to create an Executor

  To get started, always use the command and follow the instructions. This will ensure you follow the right file 
structure.

* No need to write Dockerfile manually 

  Most of the time, you do not need to create `Dockerfile` manually. Build system will generate a well-optimized Dockerfile according to your Executor package.


```{tip}
In the wizard of `jina hub new`, you can choose from four Dockerfile templates: `cpu`, `tf-gpu`, `torch-gpu`, and `jax-gpu`.
```


* No need to bump Jina version

  Hub executors are version-agnostic. When you pull an Executor from Hub, Hubble will always select the right Jina version for you. No worries about Jina version upgrade!


* Fill in metadata of your Executor correctly

  Information you include under the `metas` key, in `config.yml`, will be displayed on our website. Want to make your Executor eye-catching on our website? Fill all `metas` fields in `config.yml` with heart & love! {ref}`Its specification can be found here<config.yml>`.
