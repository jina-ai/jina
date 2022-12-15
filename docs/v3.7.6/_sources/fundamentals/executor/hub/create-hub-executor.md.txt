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

- `manifest.yml` should contain the Executor's annotations for getting better exposure on Jina Hub.
- `config.yml` is the Executor's configuration file, where you can define **__init__** arguments using **with** keyword.
- `requirements.txt` describes the Executor's Python dependencies.
- `executor.py` should contain your Executor's main logic.
- `README.md` should describe how to use your Executor.


## Fields of `manifest.yml`

`manifest.yml` is optional.

`manifest.yml` annotates your image so that it can be better managed by the Hub portal. To get better exposure on Jina Hub, you may want to 
carefully set `manifest.yml` to the correct values:

| Key                | Description                                                                                | Default |
| ---                | ---                                                                                        | ---     |
| `manifest_version` | The version of the manifest protocol                                                       | `1`     |
| `name`             | Human-readable title of the Executor                                                       | None    |
| `description`      | Human-readable description of the Executor                                                 | None    |
| `url`              | URL to find more information about the Executor, normally the GitHub repo URL              | None    |
| `keywords`         | A list of strings to help users filter and locate your package                             | None    |

```{admonition} See Also
:class: seealso
{ref}`Hub Executor best practices <hub-executor-best-practices>`
```
