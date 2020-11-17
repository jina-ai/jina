# Creating a Remote Jina Pod via Flow API

   
This tutorial guides you to run a Jina Pod remotely via Flow API.

Before the start, make sure to read ["Understanding Pea and Pod in Jina"](https://docs.jina.ai/chapters/101/.sphinx.html#pea) and ["Jina Flow API"](https://docs.jina.ai/chapters/flow/index.html). 

## Terminologies

- *Workflow*: a set of connected pods for accomplishing certain task, e.g. indexing, searching, extracting.
- *Flow API*: a pythonic way for users to construct workflows in Jina with clean, readable idioms. 
- *Remote*, *local instance*, *local machine*: the place where you want to run the pod, the place offers better computational capability or larger storage. For example, one may want to run an encode pod on the remote GPU instance.  
- *Local*, *local instance*, *local machine*: the place of your entrypoint and the rest parts of your workflow.

## Prerequisites

- Both remote and local needs to have Jina installed.
- The local needs to know the IP address/host name of the remote.
- The ports on the remote (in the range of `49152-65535`) must be public accessible.

## Steps

### 1. Let the Remote Jina Listen 
We start a Jina gateway to listen on the spawning request. By default, this feature is not enabled, one can simply type the following in the remote console:
 
```bash
jina gateway --allow-spawn
```
  
```text
GatewayPea@8233[W]:SECURITY ALERT! this gateway allows SpawnRequest from remote Jina
GatewayPea@8233[C]:gateway is listening at: 0.0.0.0:41851
```

After it reaches to `gateway is listening`, the remote Jina is ready. The port number is important for the local to connect to it. In this example we write down `41851`. If you want to have fixed port number everytime, please use `--port-expose` to specify it. More information can be found [in the documentation](/tba).

### 2. Build a Simple Index Flow 

Here we assume the remote is in the intranet and its IP address is `192.168.31.76`.

To build a simple flow, we add a `NumpyIndexer` with three replicas (i.e. shards).

Locally, we write:

```python
from jina.flow import Flow
from jina.enums import FlowOptimizeLevel

f = (Flow(optimize_level=FlowOptimizeLevel.IGNORE_GATEWAY)
     .add(uses='yaml/test-index.yml',
          replicas=3, separated_workspace=True,
          host='192.168.31.76', port_expose=41851))
```

Note that `yaml/test-index.yml` should exist on the remote `192.168.31.76`, not at local.

The YAML config we used here is as following:
```yaml
!NumpyIndexer
with:
  index_filename: tmp2
metas:
  name: test2
requests:
  on:
    SearchRequest:
      - !VectorSearchDriver
        with:
          method: query
    IndexRequest:
      - !VectorIndexDriver
        with:
          method: add
    ControlRequest:
      - !ControlReqDriver {}
```

### 3. Run the Flow and Index Data

Locally, we write:
```python
with f:
    f.index(input_fn=random_docs(1000), in_proto=True)

def random_docs(num_docs, chunks_per_doc=5, embed_dim=10):
    import numpy as np
    from jina.proto import jina_pb2
    c_id = 0
    for j in range(num_docs):
        d = jina_pb2.Document()
        for k in range(chunks_per_doc):
            c = d.chunks.add()
            c.embedding.CopyFrom(array2pb(np.random.random([embed_dim])))
            c.chunk_id = c_id
            c.doc_id = j
            c_id += 1
        yield d
```

While its running, you should observe the following log on both local and remote:
```text
GatewayPea@54104[C]:gateway is listening at: 0.0.0.0:53174
GatewayPea@54101[C]:gateway is listening at: 0.0.0.0:53178
SpawnDictP@54101[C]:connected to the gateway at 192.168.31.76:44444!
RemotePars@54101[C]:ready and listening
🌏     router@5927[I]:setting up sockets...
      Flow@54101[I]:2 Pods (i.e. 1 Peas) are running in this Flow
      Flow@54101[C]:flow is now ready for use, current build_level is GRAPH
🌏     router@5927[I]:input tcp://0.0.0.0:53179 (PULL_BIND) 	 output tcp://0.0.0.0:53184 (PUSH_BIND)	 control over tcp://0.0.0.0:53183 (PAIR_BIND)
🌏     router@5927[C]:ready and listening
🌏     router@5927[I]:setting up sockets...
  PyClient@54101[C]:connected to the gateway at 0.0.0.0:53178!
index [=                   ]  elapsed: 0.0s  batch:        0 @ 0.0/s index ...	🌏     router@5927[I]:input tcp://0.0.0.0:53185 (PULL_BIND) 	 output tcp://0.0.0.0:53180 (PUSH_BIND)	 control over tcp://0.0.0.0:53186 (PAIR_BIND)
🌏     router@5927[C]:ready and listening
🌏     pod0-0@5927[I]:setting up sockets...
🌏     pod0-0@5927[I]:input tcp://0.0.0.0:53184 (PULL_CONNECT) 	 output tcp://0.0.0.0:53185 (PUSH_CONNECT)	 control over tcp://0.0.0.0:53187 (PAIR_BIND)
🌏     pod0-0@5927[C]:ready and listening
🌏     pod0-1@5927[I]:setting up sockets...
🌏     pod0-1@5927[I]:input tcp://0.0.0.0:53184 (PULL_CONNECT) 	 output tcp://0.0.0.0:53185 (PUSH_CONNECT)	 control over tcp://0.0.0.0:53188 (PAIR_BIND)
🌏     pod0-1@5927[C]:ready and listening
🌏     pod0-2@5927[I]:setting up sockets...
🌏     pod0-2@5927[I]:input tcp://0.0.0.0:53184 (PULL_CONNECT) 	 output tcp://0.0.0.0:53185 (PUSH_CONNECT)	 control over tcp://0.0.0.0:53189 (PAIR_BIND)
🌏     pod0-2@5927[C]:ready and listening
GatewayPea@54101[I]:setting up sockets...
GatewayPea@54101[I]:input tcp://192.168.31.76:53180 (PULL_CONNECT) 	 output tcp://192.168.31.76:53179 (PUSH_CONNECT)	 control over ipc:///var/folders/hw/gpxkv2_n1fv0_cvxs6vjbc540000gn/T/tmp0vbyq01v (PAIR_BIND)
🌏     router@5927[I]:received "index" from gateway▸⚐
🌏     router@5927[I]:received "index" from gateway▸⚐
🌏     pod0-1@5927[I]:received "index" from gateway▸router▸⚐
🌏     router@5927[I]:received "index" from gateway▸⚐
🌏     router@5927[I]:received "index" from gateway▸⚐
🌏     pod0-2@5927[I]:received "index" from gateway▸router▸⚐
🌏     pod0-0@5927[I]:received "index" from gateway▸router▸⚐
🌏     router@5927[I]:received "index" from gateway▸⚐
🌏     router@5927[I]:received "index" from gateway▸⚐
🌏     pod0-0@5927[I]:received "index" from gateway▸router▸⚐
🌏     pod0-1@5927[I]:received "index" from gateway▸router▸⚐
🌏     router@5927[I]:received "index" from gateway▸router▸pod0-1▸⚐
index [=                   ]  elapsed: 10.8s  batch:        1 @ 0.1/s 🌏     router@5927[I]:received "index" from gateway▸⚐
🌏     pod0-2@5927[I]:received "index" from gateway▸router▸⚐
🌏     router@5927[I]:received "index" from gateway▸⚐
GatewayPea@54104[C]:terminated
🌏     pod0-0@5927[I]:received "index" from gateway▸router▸⚐
🌏     router@5927[I]:received "index" from gateway▸router▸pod0-0▸⚐
🌏     router@5927[I]:received "index" from gateway▸⚐
index [==                  ]  elapsed: 44.9s  batch:        2 @ 0.0/s 🌏     pod0-1@5927[I]:received "index" from gateway▸router▸⚐
🌏     router@5927[I]:received "index" from gateway▸router▸pod0-2▸⚐
index [===                 ]  elapsed: 50.3s  batch:        3 @ 0.1/s 🌏     router@5927[I]:received "index" from gateway▸⚐
🌏     pod0-0@5927[I]:received "control" from ctl▸⚐
🌏     pod0-0@5927[I]:bytes_sent: 8 KB bytes_recv:7 KB
🌏     pod0-0@5927[I]:break from the event loop
🌏     pod0-0@5927[I]:dumped changes to the executor,  53s since last the save
🌏     router@5927[I]:received "index" from gateway▸router▸pod0-1▸⚐
🌏     router@5927[I]:received "control" from ctl▸⚐
🌏     router@5927[I]:bytes_sent: 27 KB bytes_recv:24 KB
🌏     router@5927[I]:break from the event loop
🌏     router@5927[I]:executor says there is nothing to save
🌏     router@5927[C]:terminated
index [====                ]  elapsed: 56.1s  batch:        4 @ 0.1/s 🌏     pod0-2@5927[I]:received "index" from gateway▸router▸⚐
🌏     router@5927[I]:received "index" from gateway▸router▸pod0-0▸⚐
index [=====               ]  elapsed: 57.2s  batch:        5 @ 0.1/s 🌏     router@5927[I]:received "index" from gateway▸router▸pod0-2▸⚐
🌏     pod0-1@5927[I]:received "control" from ctl▸⚐
index [======              ]  elapsed: 59.2s  batch:        6 @ 0.1/s     [70.448 secs]
```

### 4. Checkout the Index Files On the Remote

After everything is done, checkout the working directory on the remote. And it should give you

```text
├── test2-0
│   ├── test2.bin
│   └── tmp2
├── test2-1
│   ├── test2.bin
│   └── tmp2
├── test2-2
│   ├── test2.bin
│   └── tmp2
```

Congratulations! You now have a remote Pod that can be connected.

## Troubleshooting Checklist

- [ ] Is the remote address correct?
- [ ] Are the remote ports public accessible (e.g. Security Group on AWS, firewall blacklist)?
- [ ] Is the remote address an internal IP address and not publicly accessible?
- [ ] Is the local connected to internet?
- [ ] Is remote Pod successfully started? You shall see a green highlighted `ready and listening` if it is successful.

## What's next?

You many also want to checkout the following articles.

