````{tip}
To update `docarray` Protobuf:

```bash
cd docarrat
docker run -v $(pwd)/proto:/jina/proto jinaai/protogen
```


To update `jina` Protobuf:

```bash
docker run -v $(pwd)/jina/:/jina/ -v $(pwd)/docarray/:/docarray/ jinaai/protogen
```

````

```{include} docs.md
```