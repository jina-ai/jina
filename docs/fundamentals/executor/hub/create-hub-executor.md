(create-executor)=
# Create

To create your Hub {class}`~jina.Executor`, you just need to run:

```bash
jina hub new
```


```{figure} screenshots/create-new.gif
:align: center
```

For the basic configuration, 
you will be asked for two things: The Executor’s name and where it should be saved. A more advanced configuration is optional but rarely necessary.

After running the command, a project with the following structure will be generated:

```text
MyExecutor/
├── Dockerfile	        # Advanced configuration will generate this file
├── manifest.yml
├── config.yml
├── README.md
├── requirements.txt
└── executor.py
```

- `manifest.yml` should contain the Executor's annotations for getting better exposure on Jina Hub. {ref}`Its specification can be found here<manifest-yaml>`.
- `config.yml` is the Executor's configuration file, where you can define **__init__** arguments using **with** keyword.
- `requirements.txt` describes the Executor's Python dependencies.
- `executor.py` should contain your Executor's main logic.
- `README.md` should describe how to use your Executor.



## Tips


When developing Hub {class}`~jina.Executor`s, make sure to follow these tips:

* Use `jina hub new` CLI to create an Executor

  To get started, always use the command and follow the instructions. This will ensure you follow the right file 
structure.

* No need to write Dockerfile manually 

  Most of the time, you do not need to create `Dockerfile` manually, {abbr}`Hubble (Hubble is the Jina Hub building system)` will generate a well-optimized Dockerfile according to your Executor 
    package.


* No need to bump Jina version

  Hub executors are version-agnostic. When you pull an Executor from Hub, Hubble will always select the right Jina 
version for you. No worries about Jina version upgrade!


* Fill in `manifest.yml` correctly. 

  Information you include in `manifest.yml` will be displayed on our website.
Want to make your Executor eye-catching on our website? Fill all fields in `manifest.yml` with heart & love! {ref}`Its specification can be found here<manifest-yaml>`.
