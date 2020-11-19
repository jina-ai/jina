# Creating a Remote Jina Pod from Console


This tutorial guides you to run a Jina Pod remotely and communicate with it via console.

Before the start, make sure to read ["Understanding Pea and Pod in Jina"](https://docs.jina.ai/chapters/101/.sphinx.html#pea). 

## Terminologies

- *Workflow*: a set of connected pods for accomplishing certain task, e.g. indexing, searching, extracting. 
- *Remote*, *local instance*, *local machine*: the place where you want to run the pod, the place offers better computational capability or larger storage. For example, one may want to run an encode pod on the remote GPU instance.  
- *Local*, *local instance*, *local machine*: the place of your entrypoint and the rest parts of your workflow.

## Prerequisites

- Both remote and local needs to have Jina installed.
- The local needs to know the IP address/host name of the remote.
- The ports on the remote (in the range of `49152-65535`) must be public accessible.

## Steps

### 1. Start a Pod on the Remote
To make the example as simple as possible, we do not equip any executor to the pod. In the remote console, type:
 
```bash
jina pod
```
  
```text
BaseExecut@8042[C]:initialize BaseExecutor from a yaml config
BasePea-0@8042[I]:setting up sockets...
BasePea-0@8042[I]:input tcp://0.0.0.0:55141 (PULL_BIND) 	 output tcp://0.0.0.0:34733 (PUSH_BIND)	 control over tcp://0.0.0.0:40093 (PAIR_BIND)
BasePea-0@8042[C]:ready and listening
```

After it reaches to `ready and listening`, the remote pod is ready to use. The port numbers are important for the local to connect to it. In this example we write down `55141`, `34733` and `40093` for future reference. If you want to have fixed port numbers everytime, please use `--port-in`, `--port-out`, `--port-ctrl` to specify them. More information can be found [in the documentation](/tba).

### 2. Test the Network Connectivity

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

If you have double checked the list and the problem is still not resolved, then consider to [create an issue in our Github project page](https://github.com/jina-ai/jina/issues/new).

## What's next?

You many also want to checkout the following articles.

