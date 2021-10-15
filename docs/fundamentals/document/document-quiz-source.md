# Document Quiz

### 1. What can kind of data can a Document contain?

- Just plain text
- Numpy array
- Any kind of data --correct-answer--

> [A Document can contain *any* kind of data that can be stored digitally](https://docs.jina.ai/fundamentals/document/document-api/#document-content). Text, graphics, audio, video, amino acids, 3D meshes, Numpy arrays, you name it.

### 2. Given a Document `doc`, what does `doc.content` refer to?

- `doc.buffer`
- `doc.blob`
- `doc.text`
- Any of the above as long as the field is not empty --correct-answer--

> [`doc.content`](https://docs.jina.ai/fundamentals/document/document-api/#document-content) is an alias that points to whatever attribute contains data. At any given point only `.buffer`, `.blob` or `.text` can contain data. Setting one of these attributes will unset any of the others that were previously in use.

### 3. How do you convert `doc.uri` to `doc.blob`?

-   ```python
    from jina.Document import convert_uri_to_blob

    doc = Document(uri="foo.txt")
    doc.blob = convert_uri_to_blob(doc)
    ```

-   ```python
    from jina.Document import blob

    doc = Document(uri="foo.txt")
    doc.blob = blob(doc.uri)
    ```

-   ```python
    doc = Document(uri="foo.txt")
    doc.convert_uri_to_blob()
    ```
    
    --correct-answer--


> Converting to a blob is a built-in method of a `Document` object (as are many other [`.convert_x_to_y` methods](https://docs.jina.ai/fundamentals/document/document-api/#conversion-from-uri-to-content))

### 4. In what format is a Document's embedding?

- An array (`numpy.ndarray`, Scipy sparse array, TensorFlow/PyTorch sparse array, etc) --correct-answer--
- Byte string
- Protobuf
- Plain text

> An embedding is a multi-dimensional representation of a Document. [You can assign any Numpy ndarray as a Document’s embedding or use other array formats for sparse embeddings](https://docs.jina.ai/fundamentals/document/document-api/#document-embedding).

### 5. What's the most efficient way to create a `DocumentArray` from a directory of images?

-   ```python
    from jina import DocumentArray
    from jina.types.document.generators import from_files

    doc_array = DocumentArray(from_files("image_dir/*.png"))
    ```
    --correct-answer--


-   ```python
    from jina import Document, DocumentArray
    import os

    doc_array = DocumentArray()
    for image in os.listdir("image_dir"):
      doc_array.append(Document(uri=image))
    ```

-   ```python
    from jina import DocumentArray

    doc_array = DocumentArray("image_dir")
    ```

> Many generators can be imported from `jina.types.document.generators` to easily create `DocumentArrays` of [different data types](https://docs.jina.ai/fundamentals/document/document-api/#construct-from-json-csv-ndarray-and-files).

### 6. What's the recommended way to add sub-Documents to `Document.chunks`?

-   ```python
    from jina import Document

    root_document = Document(text='i am root')
    root_document.chunks.append(Document(text='i am chunk 1'))
    root_document.chunks.extend([
      Document(text='i am chunk 2'),
      Document(text='i am chunk 3'),
    ])
    ```
    --correct-answer--

-   ```python
    from jina import Document

    root_document = Document(
      text='i am root',
      chunks=[
          Document(text='i am chunk 2'),
          Document(text='i am chunk 3'),
      ]
    )
    ```

> When adding sub-Documents to Document.chunks, [do not create them in one line to keep recursive document structure correct](https://docs.jina.ai/fundamentals/document/document-api/#caveat-order-matters). This is because chunks use ref_doc to control its granularity, at chunk creation time, it didn’t know anything about its parent, and will get a wrong granularity value.


### 7. What's the recommended way to filter Documents from a `DocumentArray` that only contain a `city` tag beginning with "B"?

-   ```python
    d1 = Document(tags={'city': 'Barcelona', 'phone': 'None'})
    d2 = Document(tags={'city': 'Berlin', 'phone': '648907348'})
    d3 = Document(tags={'city': 'Paris', 'phone': 'None'})
    d4 = Document(tags={'city': 'Brussels', 'phone': 'None'})

    docarray = DocumentArray([d1, d2, d3, d4])
    regexes = {'city': r'B.*'}
    docarray_filtered = docarray.find(regexes=regexes)
    ```
    --correct-answer--

-   ```python
    d1 = Document(tags={'city': 'Barcelona', 'phone': 'None'})
    d2 = Document(tags={'city': 'Berlin', 'phone': '648907348'})
    d3 = Document(tags={'city': 'Paris', 'phone': 'None'})
    d4 = Document(tags={'city': 'Brussels', 'phone': 'None'})

    docarray = DocumentArray([d1, d2, d3, d4])

    filtered_docarray = DocumentArray()
    for doc in docarray:
      if doc.tags["city"][0] == "B":
        filtered_docarray.append(doc)
    ```

> DocumentArray provides function [.find](https://docs.jina.ai/fundamentals/document/documentarray-api/#advanced-filtering-via-find) that finds the Documents in the DocumentArray whose tag values match a dictionary of user provided regular expressions. Since a Document can have many tags, the function expects one regular expression for each tag that a user wants to consider.


### 8. When would you use `DocumentArrayMemmap` instead of `DocumentArray`?

- `DocumentArrayMemmap` is just the name for `DocumentArray` in the internals of Jina code
- When you need to index a large number of `Document`s and don't want to exhaust your memory --correct-answer--
- When you want to save disk space

> When your DocumentArray object contains a large number of Document, holding it in memory can be very demanding. You may want to use [DocumentArrayMemmap](https://docs.jina.ai/fundamentals/document/documentarraymemmap-api/) to alleviate this issue.


### 9. Which of the following does `DocumentArrayMemmap` NOT support?

- `append`
- `split`
- `shuffle`
- `sort` --correct-answer--

> The API of `DocumentArrayMemmap` is almost the same as `DocumentArray`, but with a [few key differences](https://docs.jina.ai/fundamentals/document/documentarraymemmap-api/#api-side-by-side-vs-documentarray).

### 10. How would you convert a `DocumentArray` to a `DocumentArrayMemmap`?

-   ```python
    from jina import Document, DocumentArray, DocumentArrayMemmap

    doc_array = DocumentArray([Document(text='hello'), Document(text='world')])

    doc_array_memmap = DocumentArrayMemmap(doc_array)
    ```
    --correct-answer--

-   ```python
    from jina import Document, DocumentArray, DocumentArrayMemmap
    from jina.DocumentArray import convert_to_document_array_memmap

    doc_array = DocumentArray([Document(text='hello'), Document(text='world')])

    doc_array_memmap = convert_to_document_array_memmap(doc_array)
    ```

-   ```python
    from jina import Document, DocumentArray, DocumentArrayMemmap

    doc_array = DocumentArray([Document(text='hello'), Document(text='world')])

    doc_array_memmap = DocumentArrayMemmap()
    for doc in doc_array:
      doc_array_memmap.append(doc)
    ```

> [Converting a `DocumentArray` to a `DocumentMemmapArray`](https://docs.jina.ai/fundamentals/document/documentarraymemmap-api/#convert-to-from-documentarray) is just a matter of [casting](https://www.w3schools.com/python/python_casting.asp).
