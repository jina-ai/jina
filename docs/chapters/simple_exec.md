# Built-in Simple Executors and Reserved `uses` in Jina


## What is Simple Executor?

In Jina we have several built-in some *simple* executors. They are called simple for two reasons:

- It only requires a YAML config, no Python code is required;
- It inherits from `BaseExecutor` directly, its logic thus fully relies on the drivers.

For example, the built-in `_clear` executor is defined as:

```yaml
!BaseExecutor
with: {}
metas:
  name: clear
requests:
  on:
    [SearchRequest, TrainRequest, IndexRequest]:
      - !ReqPruneDriver {}
    ControlRequest:
      - !ControlReqDriver {}
```

It uses `ReqPruneDriver` to prune the request. That's it.

Another example, in Flow API the `join` method (waiting multiple Pods to finish) is implemented with `_merge` Simple Executor, which is specified by 
```yaml
!BaseExecutor
with: {}
metas:
  name: merge
requests:
  on:
    [SearchRequest, TrainRequest, IndexRequest]:
      - !MergeDriver {}
    ControlRequest:
      - !ControlReqDriver {}
```

And in Flow API implementation:

```python
def join(self, needs: Union[Tuple[str], List[str]], *args, **kwargs) -> 'Flow':
    """
    Add a blocker to the flow, wait until all peas defined in `needs` completed.

    :param needs: list of service names to wait
    :return: the modified flow
    """
    if len(needs) <= 1:
        raise FlowTopologyError('no need to wait for a single service, need len(needs) > 1')
    return self.add(name='joiner', uses='_merge', needs=needs, *args, **kwargs)

```


## What are the reserved `uses`?

To help users quickly use these patterns, we reserved the following keywords for the `uses`. They all start with underscore.

| Reserved Name | Description |
| --- | --- |
| `_clear` | Clear request body from a message |
| `_forward` | Forward the message to the downstream |
| `_route` | Use load-balancing algorithm to route message to the downstream |
| `_logforward` | Like `_forward`, but print the message |
| `_merge` | Merge the envelope of all collected messages, often used in the tail of a Pod |
| `_merge_topk` | Merge the top-k search results (both doc and chunk level) of all collected messages, often used in the tail of a Pod |
| `_merge_topk_chunks` | Merge the top-k search results (chunk level only) of all collected messages, often used in the tail of a Pod |
| `_merge_topk_docs` | Merge the top-k search results (doc level only) of all collected messages, often used in the tail of a Pod |


## How to use built-in Simple Executors?

You can directly use this executor by specifying `--uses=_clear`, or use it in `--uses-after` after collecting results from replicas.

Where ever you need to use `uses` in Jina, you can take any one from the table to fill in.