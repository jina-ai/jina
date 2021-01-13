# Creating a Remote Jina Pod from Flow APIs with jinad
A common case of using Jina remotely is to have a Flow running locally with some pods on the remote. 

## Prerequisites
Before the start, make sure you have read the [prerequisites for using jinad](https://docs.jina.ai/chapters/remote/jinad.html#prerequisites)

## Steps
In the following codes, we create a Flow on the locale with two Pods. One of the Pods is set to be running on the remote. After building the Flow, we send one index request with two Documents to it.

```python
from jina import Flow
f = (Flow()
     .add(uses='_logforward')
     .add(uses='_logforward', host='3.16.166.3', port_expose=8000))
with f:
    f.index_lines(lines=['hello', 'jina'])
```

As shown in the logs below, `pod1` is running on the remote while `gateway` and `pod0` are running locally. `jinad` manages the creating and deleting of the `pod1` on the remote. 

```text
pod0/ZEDRuntime@69694[I]:input tcp://0.0.0.0:51317 (PULL_BIND) output tcp://3.16.166.3:51321 (PUSH_CONNECT) control over tcp://0.0.0.0:51316 (PAIR_BIND)
...
           pod0@69676[S]:ready and listening
...
         🌏 pod1@69696[I]:ready and listening
           Flow@69676[S]:🎉 Flow is ready to use, accepting gRPC request
           Flow@69676[I]:
	🖥️ Local access:	tcp://0.0.0.0:51327
	🔒 Private network:	tcp://192.168.1.9:51327
	🌐 Public address:	tcp://203.184.132.69:51327
         Client@69676[S]:connected to the gateway at 0.0.0.0:51327!
...
        gateway@69697[I]:send: 1 recv: 0 pending: 1
pod0/ZEDRuntime@69694[I]:recv IndexRequest  from gateway▸pod0/ZEDRuntime▸⚐
pod0/ZEDRuntime@69694[I]:#sent: 0 #recv: 1 sent_size: 0 Bytes recv_size: 423 Bytes
🌏 pod1/ZEDRuntime@69696[I]:recv IndexRequest  from gateway▸pod0/ZEDRuntime▸pod1/ZEDRuntime▸⚐
🌏 pod1/ZEDRuntime@69696[I]:#sent: 0 #recv: 1 sent_size: 0 Bytes recv_size: 508 Bytes
...
	✅ done in ⏱ 2 seconds 🐎 47.9/s
        gateway@69676[S]:terminated
...
           pod1@69676[S]:terminated
...
           pod0@69676[S]:terminated
...
```
## What's next?

You many also want to checkout the following articles.
[Creating a Remote Pod from Console](https://docs.jina.ai/chapters/remote/create-remote-pod-console-jinad.html)
[Creating a Remote Flow](https://docs.jina.ai/chapters/remote/create-remote-flow.html) 
