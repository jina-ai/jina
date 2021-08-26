## 5. Use in Jina Flow

It will pull Executor automatically if you didn't pull it before.

### 5.1 Using docker images

Use the prebuilt images from `Hubble` in your python codes,

```python
from jina import Flow

# SECRET must be provided for private Executor
f = Flow().add(uses='jinahub+docker://<UUID>[:<SECRET>][/<TAG>]')
```

If there is no `/<TAG>` provided when using, it by default equals to `/latest`, which means using the `latest` tag.

**Attention:**

If you are a Mac user, please use `host.docker.internal` as your url when you want to connect a local port from Executor
docker container.

For
example: [`jinahub+docker://PostgreSQLStorage`](https://github.com/jina-ai/executor-indexers/tree/main/jinahub/indexers/storage/PostgreSQLStorage)
will connect PostgreSQL server which was started at local. Then you must use it with:

```python
from jina import Flow, Document

f = Flow().add(uses='jinahub+docker://PostgreSQLStorage', 
               uses_with={'hostname': 'host.docker.internal'})
with f:
    resp = f.post(on='/index', inputs=Document(), return_results=True)
    print(f'{resp}')
```

### 5.2 Using source codes

Use the source codes from `Hubble` in your python codes,

```python
from jina import Flow

f = Flow().add(uses='jinahub://<UUID>[:<SECRET>][/<TAG>]')
```

### 5.3 Override Default Parameters

It is possible that the default parameters of the published Executor may not be ideal for your use case. You can override
any of these parameters by passing `uses_with` and `uses_metas` as parameters.

```python
from jina import Flow

f = Flow().add(uses='jinahub://<UUID>[:<SECRET>][/<TAG>]', 
               uses_with={'param1': 'new_value'},
               uses_metas={'name': 'new_name'})
```

This way, the Executor will work with the overrode parameters.
