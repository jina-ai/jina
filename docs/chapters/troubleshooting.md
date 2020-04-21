# Troubleshooting

This page collects the solution to some errors you may encounter when using Jina. 

## `Exception iterating requests! often the case is that you define/send a bad input iterator to jina, please double check your input iterator`

As it said, often you have a badly written iterator. Use `next()` to check if the iterator pops up things you want.

Often the mistake is missing `()` when feeding to the flow. For example, the following is wrong and will cause that errors: 

```python
def bytes_gen():
    idx = 0
    for g in glob.glob(GIF_BLOB)[:num_docs]:
        with open(g, 'rb') as fp:
            # print(f'im asking to read {idx}')
            yield fp.read()
            idx += 1

with f.build() as fl:
    fl.index(bytes_gen, batch_size=8)
```

It should be:

```python
with f.build() as fl:
    fl.index(bytes_gen(), batch_size=8)
``` 


## `OSError: [Errno 24] Too many open files`

This often happens when `replicas`/`num_parallel` is set to a big number. Solution to that is to increase this (session-wise) allowance via:

```bash
ulimit -n 4096
```

## `objc[15934]: +[__NSPlaceholderDictionary initialize] may have been in progress in another thread when fork() was called.`

Probably MacOS only. 
```bash
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
```
 