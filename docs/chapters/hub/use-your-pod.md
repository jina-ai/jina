# Use Your Pod Image

## Use the Pod image via Docker CLI

The most powerful way to use this Pod image is via Docker CLI directly:

```bash
docker run --rm -p 55555:55555 -p 55556:55556 jinaai/hub.examples.mwu_encoder --port-in 55555 --port-out 55556
```

Note, the exposure of ports `-p 55555:55555 -p 55556:55556` is required for other Pods (local/remote) to communicate this Pod. One may also want to use `--network host` and let the Pod share the network layer of the host.
 
All parameters supported by `jina pod --help` can be followed after `docker run jinaai/hub.examples.mwu_encoder`.

One can mount a host path to the container via `--volumes` or `-v`. For example, to override the internal YAML config, one can do

```bash
# assuming $pwd is the root dir of this repo 
docker run --rm -v $(pwd)/hub/example/mwu_encoder_ext.yml:/ext.yml jinaai/hub.examples.mwu_encoder --uses /ext.yml
```

```text
MWUEncoder@ 1[S]:look at me! im from an external yaml!
MWUEncoder@ 1[S]:initialize MWUEncoder from a yaml config
 BasePea-0@ 1[I]:setting up sockets...
 BasePea-0@ 1[I]:input tcp://0.0.0.0:36109 (PULL_BIND) 	 output tcp://0.0.0.0:58191 (PUSH_BIND)	 control over tcp://0.0.0.0:52365 (PAIR_BIND)
 BasePea-0@ 1[S]:ready and listening
```

To override the predefined entrypoint via `--entrypoint`, e.g.

```bash
docker run --rm --entrypoint "jina" jinaai/hub.examples.mwu_encoder check
```

## Use the Pod image via Jina CLI

Another way to use the Pod image is simply give it to `jina pod` via `--image`,
```bash
jina pod --image jinaai/hub.examples.mwu_encoder
```

```text
🐳 MWUEncoder@ 1[S]:look at me! im from internal yaml!
🐳 MWUEncoder@ 1[S]:initialize MWUEncoder from a yaml config
🐳 BasePea-0@ 1[I]:setting up sockets...
🐳 BasePea-0@ 1[I]:input tcp://0.0.0.0:59608 (PULL_BIND) 	 output tcp://0.0.0.0:59609 (PUSH_BIND)	 control over tcp://0.0.0.0:59610 (PAIR_BIND)
ContainerP@69041[S]:ready and listening
🐳 BasePea-0@ 1[S]:ready and listening
```

Note the 🐳 represents that the log is piping from a Docker container.

See `jina pod --help` for more usage.

## Use the Pod image via Flow API

Finally, one can use it via Flow API as well, e.g.

```python
from jina.flow import Flow

f = (Flow()
        .add(name='my-encoder', image='jinaai/hub.examples.mwu_encoder',
             volumes='./abc', uses='hub/examples/mwu-encoder/mwu_encoder_ext.yml', 
             port_in=55555, port_out=55556)
        .add(name='my-indexer', uses='indexer.yml'))
```