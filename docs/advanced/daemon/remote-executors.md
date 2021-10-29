# Remote Executors

JinaD enables deploying Executors on remote machines. We can pass the remote host details using `host`and `port_jinad` arguments in the Flow syntax. Here are a few examples of using remote Executors.

## Executors from Hub

````{tab} Local (jinahub+docker)
```{code-block} python
from jina import Flow

f = Flow().add(uses='jinahub+docker://AdvancedExecutor')

```
````

````{tab} Remote (jinahub+docker)
```{code-block} python
---
emphasize-lines: 4,5
---
from jina import Flow

f = Flow().add(uses='jinahub+docker://AdvancedExecutor',
               host='1.2.3.4',
               port_jinad=8000)

```
````

````{tab} Local (jinahub)
```{code-block} python
from jina import Flow

f = Flow().add(uses='jinahub://AdvancedExecutor',
               install_requirements=True)

```
````

````{tab} Remote (jinahub)
```{code-block} python
---
emphasize-lines: 5,6
---
from jina import Flow

f = Flow().add(uses='jinahub://AdvancedExecutor',
               install_requirements=True,
               host='1.2.3.4',
               port_jinad=8000)

```
````

## Executors on different hosts

````{tab} Local
```{code-block} python
from jina import Flow

f = (
    Flow()
    .add(name='encoder',
         uses='jinahub+docker://AdvancedExecutor1')
    .add(name='indexer',
         uses='jinahub+docker://AdvancedExecutor2')
)

```
````

````{tab} Remote
```{code-block} python
---
emphasize-lines: 7,8,11,12
---
from jina import Flow

f = (
    Flow()
    .add(name='encoder',
         uses='jinahub+docker://AdvancedExecutor1',
         host='1.2.3.4',
         port_jinad=8000)
    .add(name='indexer',
         uses='jinahub+docker://AdvancedExecutor2',
         host='2.3.4.5',
         port_jinad=8000)
)

```
````

## File structures with remote Executors

```{important}
Read the best practices about managing [repository structure](../../fundamentals/executor/repository-structure).
```

For a simple project structure, for example,

```bash
.
├── project
│   ├── config.yml              # Defines `py_modules: my_executor.py`
│   └── my_executor.py          # Defines MyExecutor
```

````{tab} Using YAML
```{code-block} python
---
emphasize-lines: 7
---
from jina import Flow

PATH_TO_EXECUTOR_DIRECTORY = '/path/to/project/directory'
f = Flow().add(uses='config.yml',
               host='1.2.3.4',
               port_jinad=8000,
               upload_files=PATH_TO_EXECUTOR_DIRECTORY)

```
````

````{tab} Using py_modules
```{code-block} python
---
emphasize-lines: 8
---
from jina import Flow

PATH_TO_EXECUTOR_DIRECTORY = '/path/to/project/directory'
f = Flow().add(uses='MyExecutor',
               host='1.2.3.4',
               port_jinad=8000,
               py_modules='my_executors.py'
               upload_files=PATH_TO_EXECUTOR_DIRECTORY)

```
````

Suppose you have a complex project structure, for example,

```bash
.
├── project
│   ├── config.yml              # Defines `py_modules: executors/__init__.py`
│   └── executors
│       ├── __init__.py         # Imports MyExecutor from `my_executors.py`
│       ├── helper.py
│       ├── my_executor.py      # Defines MyExecutor
│       └── utils
│           ├── __init__.py
│           ├── data.py
│           └── io.py
│   ├── flow.yml
│   ├── requirements-index.txt  # Includes your pip dependencies
│   ├── requirements.txt
```

````{tab} Using YAML
```{code-block} python
---
emphasize-lines: 7
---
from jina import Flow

PATH_TO_EXECUTOR_DIRECTORY = '/path/to/project/directory'
f = Flow().add(uses='config.yml',
               host='1.2.3.4',
               port_jinad=8000,
               upload_files=PATH_TO_EXECUTOR_DIRECTORY)

```
````

````{tab} Using py_modules
```{code-block} python
---
emphasize-lines: 8
---
from jina import Flow

PATH_TO_EXECUTOR_DIRECTORY = '/path/to/project/directory'
f = Flow().add(uses='MyExecutor',
               host='1.2.3.4',
               port_jinad=8000,
               py_modules='executors/__init__.py'
               upload_files=PATH_TO_EXECUTOR_DIRECTORY)

```
````

```{hint}
1. Always pass the path to the directory via `upload_files`.
2. Always pass relative filepath wrt to the project in `py_modules` or `uses` or `config.yml`.
3. Keep your `requirements.txt` files on the root level.
```

## Using GPU with any remote Executor

````{tab} Without GPU
```{code-block} python
from jina import Flow

f = Flow().add(uses='TFExecutor',
               host='1.2.3.4',
               port_jinad=8000,
               ...)

```
````

````{tab} With GPU
```{code-block} python
---
emphasize-lines: 7
---
from jina import Flow

f = Flow().add(uses='TFExecutor',
               host='1.2.3.4',
               port_jinad=8000,
               ...,
               gpus='all')

```
````
