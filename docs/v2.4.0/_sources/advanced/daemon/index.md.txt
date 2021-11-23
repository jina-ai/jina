(daemon-cookbook)=
# Remote Executors and Flows via JinaD

`JinaD` is a [daemon](https://en.wikipedia.org/wiki/Daemon_(computing)) for deploying and managing Jina on remote via a
RESTful interface. It allows users to create/update/delete Executors and Flows on remote hosts. It achieves isolation of
deployments by defining a `workspace` for each Jina object, hence allowing a multi-tenant setup with parallel Flows on
the same host.


## Minimum working example

````{tab} Remote (1.2.3.4) 
```bash
# have docker installed
docker run --add-host host.docker.internal:host-gateway \
           -v /var/run/docker.sock:/var/run/docker.sock \
           -v /tmp/jinad:/tmp/jinad \
           -p 8000:8000 \
           --name jinad \
           -d jinaai/jina:master-daemon
```

````

````{tab} Local

```python
from jina import Flow

f = (Flow()
     .add(uses='mwu_encoder.yml',
          host='1.2.3.4:8000',
          upload_files=['mwu_encoder.py']))

with f:
    ...
```

````


```{toctree}
:hidden:

jinad-server
jinad-client
remote-executors
workspace
remote-flows
stream-remote-logs
development-using-jinad
```

