(create-hub-executor)=
# Create Executor

To create your Hub Executor, you just need to run this command in your terminal:

```bash
jina hub new
```


```{figure} screenshots/create-new.gif
:align: center
```

When you run the command above, a wizard will ask you some questions about the Executor. For the basic configuration, 
you will be asked two things: The Executor’s name and where it should be saved. The wizard will ask if you want to have 
a more advanced configuration, but it is unnecessary for most of use cases.

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

- `manifest.yml` should contain the annotations of the Executor for getting better appealing on Jina Hub.
- `config.yml` is the config file of your Executor. You can define **__init__** arguments using **with** keyword in this config file.
- `requirements.txt` describes the Python dependencies of the Executor.
- `executor.py` should contain the main logic of your Executor.
- `README.md` should describe the usage of the Executor.


## Fields of `manifest.yml`

`manifest.yml` is optional.

`manifest.yml` annotates your image so that it can be better managed by the Hub portal. To get better appealing on Jina Hub, you may want to 
carefully set `manifest.yml` to the correct values.

| Key | Description | Default |
| --- | --- | --- |
| `manifest_version` | The version of the manifest protocol | `1` |
| `name` | Human-readable title of the Executor | None |
| `description` | Human-readable description of the Executor | None |
| `url` | URL to find more information on the Executor, normally it should be the GitHub repo URL | None |
| `keywords` | A list of strings help user to filter and locate your package  | None | 

```{admonition} See Also
:class: seealso
{ref}`Hub Executor best practices <hub-executor-best-practices>`
```
