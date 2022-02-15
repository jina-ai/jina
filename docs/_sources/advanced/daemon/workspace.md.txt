# Workspace

Workspace is the entrypoint for all objects in JinaD. It primarily represents 4 pieces.

1. **Docker Image**

   All objects created by JinaD are containerized. Workspace is responsible for building the base image. You can
   customize each image with the help of a `.jinad` file and a `requirements.txt` file.

2. **Docker Network**

   Workspace is also responsible for managing a private `bridge` network for all child containers. This provides network
   isolation from other workspaces, while allowing all containers inside the same workspace to communicate.

3. **Local work directory**

   All the files used to manage a Jina object or created by a Jina object are stored here. This directory is exposed to
   all child containers. These can be:
    - config files (e.g.- Flow/Executor YAML, Python modules etc),
    - data written by your Executor
    - `.jinad` file
    - `requirements.txt` file

4. **Special files**

    - `.jinad` is an optional file defining how the base image is built. Following arguments are supported.

      ```ini
      build = default                 ; NOTE: devel/default, (gpu: to be added).
      python = 3.7                    ; NOTE: 3.7, 3.8, 3.9 allowed.
      jina = 2.0.rc7                  ; NOTE: to be added.
      ports = 45678                   ; NOTE: comma separated ports to be mapped.
      run = "python app.py 45678"     ; NOTE: command to start a Jina project on remote.
      ```

      You can also deploy an end-to-end Jina project on remote using the following steps.
        - Include a `.jinad` file with `run` set to your default entrypoint (e.g. - `python app.py`)
        - Upload all your files including `.jinad` during workspace creation.
        - This will deploy a custom container with your project

    - `requirements.txt` defines all python packages to be installed using `pip` in the base image.

      ```text
      annoy
      torch>=1.8.0
      tensorflow
      ```


## Create a workspace ([redoc](https://api.jina.ai/daemon/#operation/_create_workspaces_post))

Create a directory (say `awesome_project`) on local which has all your files (`yaml`, `py_modules`, `requirements.txt`
, `.jinad` etc.)

```python
from daemon.clients import JinaDClient

client = JinaDClient(host=HOST, port=PORT)
my_workspace_id = client.workspaces.create(paths=['path_to_awesome_project'])
```


```text
     JinaDClient@16018[I]:uploading 3 file(s): flow.yml, requirements.txt, .jinad
  🌏 36f9d7f70145 DaemonWorker1 INFO  ---> 70578df55b1c
  🌏 36f9d7f70145 DaemonWorker1 INFO Step 4/7 : ARG PIP_REQUIREMENTS
  🌏 36f9d7f70145 DaemonWorker1 INFO  ---> Running in e1588f87b32c
  🌏 36f9d7f70145 DaemonWorker1 INFO Removing intermediate container e1588f87b32c
  🌏 36f9d7f70145 DaemonWorker1 INFO  ---> 9f715ea59f8a
  🌏 36f9d7f70145 DaemonWorker1 INFO Step 5/7 : RUN if [ -n "$PIP_REQUIREMENTS" ]; then         echo "Installing
  ${PIP_REQUIREMENTS}";         for package in ${PIP_REQUIREMENTS}; do             pip install "${package}";         done;     fi
  🌏 36f9d7f70145 DaemonWorker1 INFO  ---> Running in e9018896b366
  🌏 36f9d7f70145 DaemonWorker1 INFO Installing tinydb sklearn
  🌏 36f9d7f70145 DaemonWorker1 INFO Collecting tinydb
  🌏 36f9d7f70145 DaemonWorker1 INFO   Downloading tinydb-4.5.1-py3-none-any.whl (23 kB)
  🌏 36f9d7f70145 DaemonWorker1 INFO Requirement already satisfied: typing-extensions<4.0.0,>=3.10.0 in
  /usr/local/lib/python3.7/site-packages (from tinydb) (3.10.0.0)
  🌏 36f9d7f70145 DaemonWorker1 INFO Installing collected packages: tinydb
  🌏 36f9d7f70145 DaemonWorker1 INFO Successfully installed tinydb-4.5.1
  🌏 36f9d7f70145 DaemonWorker1 WARNING WARNING: Running pip as the 'root' user can result in broken permissions and conflicting
  behaviour with the system package manager. It is recommended to use a virtual environment instead:
  https://pip.pypa.io/warnings/venv
  🌏 36f9d7f70145 DaemonWorker1 INFO Collecting sklearn
  🌏 36f9d7f70145 DaemonWorker1 INFO   Downloading sklearn-0.0.tar.gz (1.1 kB)
  🌏 36f9d7f70145 DaemonWorker1 INFO Collecting scikit-learn
  🌏 36f9d7f70145 DaemonWorker1 INFO   Downloading scikit_learn-0.24.2-cp37-cp37m-manylinux2010_x86_64.whl (22.3 MB)
  🌏 36f9d7f70145 DaemonWorker1 INFO Collecting joblib>=0.11
  🌏 36f9d7f70145 DaemonWorker1 INFO   Downloading joblib-1.0.1-py3-none-any.whl (303 kB)
  🌏 36f9d7f70145 DaemonWorker1 INFO Requirement already satisfied: numpy>=1.13.3 in /usr/local/lib/python3.7/site-packages (from
  scikit-learn->sklearn) (1.21.1)
  🌏 36f9d7f70145 DaemonWorker1 INFO Collecting scipy>=0.19.1
  🌏 36f9d7f70145 DaemonWorker1 INFO   Downloading scipy-1.7.0-cp37-cp37m-manylinux_2_5_x86_64.manylinux1_x86_64.whl (28.5 MB)
  🌏 36f9d7f70145 DaemonWorker1 INFO Collecting threadpoolctl>=2.0.0
  🌏 36f9d7f70145 DaemonWorker1 INFO   Downloading threadpoolctl-2.2.0-py3-none-any.whl (12 kB)
  🌏 36f9d7f70145 DaemonWorker1 INFO Building wheels for collected packages: sklearn
  🌏 36f9d7f70145 DaemonWorker1 INFO   Building wheel for sklearn (setup.py): started
  🌏 36f9d7f70145 DaemonWorker1 INFO   Building wheel for sklearn (setup.py): finished with status 'done'
  🌏 36f9d7f70145 DaemonWorker1 INFO   Created wheel for sklearn: filename=sklearn-0.0-py2.py3-none-any.whl size=1309 sha256=ac85019415e0eeebf468e2f71c43d8ff9b78131eaaccce89e34bb5ba8a2473ca
  🌏 36f9d7f70145 DaemonWorker1 INFO Successfully built sklearn
  🌏 36f9d7f70145 DaemonWorker1 INFO Installing collected packages: threadpoolctl, scipy, joblib, scikit-learn, sklearn
  🌏 36f9d7f70145 DaemonWorker1 INFO Successfully installed joblib-1.0.1 scikit-learn-0.24.2 scipy-1.7.0 sklearn-0.0 threadpoolctl-2.2.0
  🌏 36f9d7f70145 DaemonWorker1 WARNING WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager. It is recommended to
  use a virtual environment instead: https://pip.pypa.io/warnings/venv
  🌎  Workspace: Creating...    JinaDClient@16018[I]:jworkspace-480ec0d8-ea02-4adb-8e02-04cd27962863 created successfully
```


## Get details of a workspace ([redoc](https://api.jina.ai/daemon/#operation/_list_workspaces__id__get))

```python
from daemon.clients import JinaDClient

client = JinaDClient(host=HOST, port=PORT)
client.workspaces.get(my_workspace_id)
```

```json
{
  "time_created": "2021-07-26T17:31:29.326049",
  "state": "ACTIVE",
  "metadata": {
    "image_id": "97b0cb4860",
    "image_name": "jworkspace:480ec0d8-ea02-4adb-8e02-04cd27962863",
    "network": "8dcd21b98a",
    "workdir": "/tmp/jinad/jworkspace-480ec0d8-ea02-4adb-8e02-04cd27962863",
    "container_id": None,
    "managed_objects": []
  },
  "arguments": {
    "files": ["flow.yml", "requirements.txt", ".jinad"],
    "jinad": {
      "build": "default",
      "dockerfile": "/usr/local/lib/python3.7/site-packages/daemon/Dockerfiles/default.Dockerfile"
    },
    "requirements": "tinydb sklearn"
  }
}
```

## List all workspaces ([redoc](https://api.jina.ai/daemon/#operation/_get_items_workspaces_get))

```python
client.workspaces.list()
```

```json
{
  "jworkspace-2b017b8f-19af-4d78-9364-6404447d91ac": {
    ...
  },
  "jworkspace-8fec6449-2824-4913-9c06-3d0ec1314674": {
    ...
  },
  "jworkspace-41dbe23a-9ecd-4e84-8df2-8dd6295a55b4": {
    ...
  },
  "jworkspace-0cc90166-5ce2-4702-9d30-0ff8f3598a9f": {
    ...
  },
  "jworkspace-be53f490-549a-4335-831a-5fb13a1de754": {
    ...
  },
  "jworkspace-48319ab9-6c36-4e2d-b687-dd0ab498cb4f": {
    ...
  }
}
```


## Delete a workspace ([redoc](https://api.jina.ai/daemon/#operation/_delete_workspaces__id__delete))

```python
success_deleted = client.workspaces.delete(id=workspace_id)
assert success_deleted
```
