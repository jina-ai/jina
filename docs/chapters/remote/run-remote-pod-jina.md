# Creating a Remote Jina Pod via Jina Gateway 
   
   
This tutorial guides you to run a customized Jina Pod on the remote via a local Jina command line interface.

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

### 2. Spawn a Remote Pod from the Local Jina

Here we assume the remote is in the intranet and its IP address is `192.168.31.76`. In the local console, type:

```bash
jina pod --host 192.168.31.76 --port-expose 41851
```

If everything goes well, then you should be able to see following logs in the local console:
```text
SpawnPodHe@31786[C]:connected to the gateway at 192.168.31.76:41851!
RemotePod@31786[C]:ready and listening
🌏  BasePea-0@8233[I]:setting up sockets...
🌏  BasePea-0@8233[I]:input tcp://0.0.0.0:61980 (PULL_BIND) 	 output tcp://0.0.0.0:61981 (PUSH_BIND)	 control over tcp://0.0.0.0:61982 (PAIR_BIND)
🌏  BasePea-0@8233[C]:ready and listening
```

The emoji 🌏 indicates that this line is a log record synced from the remote. If you now have access to the remote console, you can see the remote console has the same log. 

### 3. Test the Network Connectivity

To test the connectivity between your local Jina and the remote Pod you just spawned. Note that the `ping` always goes to the control port, not the gRPC port. 
 
In the local console:
```bash
JINA@32699[I]:ping tcp://192.168.31.76:61982 at 0 round takes 0.004 secs
JINA@32699[I]:ping tcp://192.168.31.76:61982 at 1 round takes 0.004 secs
JINA@32699[I]:ping tcp://192.168.31.76:61982 at 2 round takes 0.004 secs
JINA@32699[C]:avg. latency: 4 ms
```

If everything goes well, then you should be able to see something like:
```text
JINA@30100[I]:ping tcp://192.168.31.76:40093 at 0 round takes 0.027 secs
JINA@30100[I]:ping tcp://192.168.31.76:40093 at 1 round takes 0.021 secs
JINA@30100[I]:ping tcp://192.168.31.76:40093 at 2 round takes 0.021 secs
JINA@30100[C]:avg. latency: 23 ms
```

If you have access to the remote screen, you can observe how the Pod reacts to the request. The logs will be synced to local cosnsole in real-time. 

Congratulations! You now have a remote Pod that can be connected.

## Troubleshooting Checklist

- [ ] Is the remote address correct?
- [ ] Do you add `--allow-spawn` when starting the remote gateway?
- [ ] Is the `--port-expose` in your local command matching with the `--port-expose` of the remote gateway?
- [ ] Are the remote ports public accessible (e.g. Security Group on AWS, firewall blacklist)?
- [ ] Is the remote address an internal IP address and not publicly accessible? 
- [ ] Is the local connected to internet?
- [ ] Is the gateway already occupied by a spawned pod?

    Currently there is a limitation that a gateway allows **no more than one** spawned pod running. If you now open another local session and do `jina pod --host 192.168.31.76 --port-expose 41851` again, it will fail and throws a timeout error. To solve it, you have to go to the first local session and end it with <kbd>Ctrl</kbd>+<kbd>C</kbd>. The remote pod will be terminated automatically and you can restart a new local session.

If you have double checked the list and the problem is still not resolved, then consider to [create an issue in our Github project page](https://github.com/jina-ai/jina/issues/new).

## What's next?

You many also want to checkout the following articles.

