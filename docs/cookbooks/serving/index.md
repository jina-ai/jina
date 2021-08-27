# Serving Jina

Congrats! {octicon}`rocket;1em;sd-text-danger`

If you come to this page, most likely you have already built some cool stuff with Jina and now want to share it to the world. This cookbook will
guide you from basic serving for demo purpose to advanced serving in production.

## Minimum Working Example


<table>
<tr>
<td>
<b>Server</b>
</td>
<td>
<b>Client</b>
</td>
</tr>
<tr>
<td>

```python
from jina import Flow

f = Flow(protocol='grpc', port_expose=12345)
with f:
    f.block()
```

</td>
<td>

```python
from jina import Client, Document

c = Client(protocol='grpc', port_expose=12345)
c.post('/', Document())
```

</td>
</tr>
</table>

```{toctree}
:hidden:

flow-as-a-service
```