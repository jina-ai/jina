# Build a Streaming API for a Large Language Model
```{include} ../../README.md
:start-after: <!-- start llm-streaming-intro -->
:end-before: <!-- end llm-streaming-intro -->
```

## Service Schemas
```{include} ../../README.md
:start-after: <!-- start llm-streaming-schemas -->
:end-before: <!-- end llm-streaming-schemas -->
```

```{admonition} Note
:class: note

Thanks to DocArray's flexibility, you can actually implement much more flexible services. For instance, you can use 
Tensor types to efficiently stream token logits back to the client and implement complex token sampling strategies on 
the client side.
```

## Service initialization
```{include} ../../README.md
:start-after: <!-- start llm-streaming-init -->
:end-before: <!-- end llm-streaming-init -->
```

## Implement the streaming endpoint

```{include} ../../README.md
:start-after: <!-- start llm-streaming-endpoint -->
:end-before: <!-- end llm-streaming-endpoint -->
```

## Serve and send requests
```{include} ../../README.md
:start-after: <!-- start llm-streaming-serve -->
:end-before: <!-- end llm-streaming-serve -->
```
