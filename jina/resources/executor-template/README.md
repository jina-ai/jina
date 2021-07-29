# {{exec_name}}

{{exec_description}}

## Usage

#### via Docker image (recommended)

```python
from jina import Flow
	
f = Flow().add(uses='jinahub+docker://{{exec_name}}')
```

#### via source code

```python
from jina import Flow
	
f = Flow().add(uses='jinahub://{{exec_name}}')
```

- To override `__init__` args & kwargs, use `.add(..., uses_with: {'key': 'value'})`
- To override class metas, use `.add(..., uses_metas: {'key': 'value})`