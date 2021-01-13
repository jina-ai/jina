# Creating a Remote Jina Pod from Console with jinad

## Prerequisites
Before the start, make sure you have read the [prerequisites for using jinad](https://docs.jina.ai/chapters/remote/jinad.html#prerequisites)

## Steps
In the simplest case, you may want to create a Pod on the remote. The most naive way is to log into the remote machine and [start a pod using `jina` CLI](https://docs.jina.ai/chapters/remote/run-remote-pod-console.html). To avoid logging into the remote machine every time, we can use `jinad` to do the same thing. Furthermore, `jinad` offers a session management for the running Pods on the remote and saves you from manually creating and deleting Pods.

Here we start a simple Pod with the default configuration `_logforward`. The Pod forwards received messages and print the messages out in the logs. On the local, you can run the following command to start a remote pod.

```bash
jina pod --uses _logforward --host 3.16.166.3 --port-expose 8000
```

```text
▶️  /Users/nanwang/.pyenv/versions/3.7.5/bin/jina pod --uses _logforward --host 3.16.166.3 --port-expose 8000
...
   JinadRuntime@68880[S]:created remote pod with id dcb5046e-554a-11eb-86b2-0ab9db700358
        BasePea@68861[S]:ready and listening
   JinadRuntime@68880[I]:🌏 Fetching streamed logs from remote id: dcb5046e-554a-11eb-86b2-0ab9db700358
   🌏 ZEDRuntime@68880[I]:input tcp://0.0.0.0:55223 (PULL_BIND) output tcp://0.0.0.0:55535 (PUSH_BIND) control over tcp://0.0.0.0:49993 (PAIR_BIND)
      🌏 BasePea@68880[I]:ready and listening
```

> Note: The logs starting with 🌏 are fetched from the remote Pod. Now we have already the Pod running remotely and we can check the connectivity.

```bash
jina ping 3.16.166.3 49993
```

```text
▶️  /Users/nanwang/.pyenv/versions/3.7.5/bin/jina ping 3.16.166.3 49993
...
           JINA@69179[I]:ping tcp://3.16.166.3:49993 at 2 round...
           JINA@69179[I]:ping tcp://3.16.166.3:49993 at 2 round takes 1 second (1.23s)
           JINA@69179[S]:avg. latency: 1343 ms
```

## What's next?

You many also want to checkout the following articles.
[Creating a Remote Pod via Flow APIs](https://docs.jina.ai/chapters/remote/create-remote-pod-flow.html) 
[Creating a Remote Flow](https://docs.jina.ai/chapters/remote/create-remote-flow.html) 
