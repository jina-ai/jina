# Using a Remote Jina Pod via Flow API

This tutorial guides you to run a Jina Pod remotely via Flow API.

Before the start, make sure to read ["Understanding Pea and Pod in Jina"](/tba) and ["Jina Flow API"](/tba). 

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
jina gateway --allow_spawn
```
  
```text
GatewayPea@8233[W]:SECURITY ALERT! this gateway allows SpawnRequest from remote Jina
GatewayPea@8233[C]:gateway is listening at: 0.0.0.0:41851
```

After it reaches to `gateway is listening`, the remote Jina is ready. The port number is important for the local to connect to it. In this example we write down `41851`. If you want to have fixed port number everytime, please use `--port_grpc` to specify it. More information can be found [in the documentation](/tba).

### 2. Build a Simple Index Flow 

Here we assume the remote is in the intranet and its IP address is `192.168.31.76`.

To verify the connectivity, we can use `jina ping` on the local.

In the local console:
```bash
jina ping 192.168.31.76 40093
```

If everything goes well, then you should be able to see something like:
```text
JINA@30100[I]:ping tcp://192.168.31.76:40093 at 0 round takes 0.027 secs
JINA@30100[I]:ping tcp://192.168.31.76:40093 at 1 round takes 0.021 secs
JINA@30100[I]:ping tcp://192.168.31.76:40093 at 2 round takes 0.021 secs
JINA@30100[C]:avg. latency: 23 ms
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

