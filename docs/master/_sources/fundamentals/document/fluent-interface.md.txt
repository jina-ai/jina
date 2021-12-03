# Fluent Interface

Jina provides a simple fluent interface for `Document` that allows one to process (often preprocess) a Document object by chaining methods. For example to read an image file as `numpy.ndarray`, resize it, normalize it and then store it to another file; one can simply do:

```python
from jina import Document

d = (
    Document(uri='apple.png')
    .load_uri_to_image_blob()
    .set_image_blob_shape((64, 64))
    .set_image_blob_normalization()
    .dump_image_blob_to_file('apple1.png')
)
```

```{figure} apple.png
:scale: 20%

Original `apple.png`
```

```{figure} apple1.png
:scale: 50%

Processed `apple1.png`
```

````{important}
Note that, chaining methods always modify the original Document in-place. That means the above example is equivalent to:

```python
from jina import Document

d = Document(uri='apple.png')

(d.load_uri_to_image_blob()
  .set_image_blob_shape((64, 64))
  .set_image_blob_normalization()
  .dump_image_blob_to_file('apple1.png'))
```
````

## Parallelization

Fluent interface is super useful when processing a large {class}`~jina.DocumentArray` or {class}`~jina.DocumentArrayMemmap`. One can leverage {meth}`~jina.types.arrays.mixins.parallel.ParallelMixin.map` to speed up things quite a lot. 

The following example shows the time difference on preprocessing ~6000 image Documents.

```python
from jina import DocumentArray
from jina.logging.profile import TimeContext

docs = DocumentArray.from_files('*.jpg')

def foo(d):
    return (d.load_uri_to_image_blob()
            .set_image_blob_normalization()
            .set_image_blob_channel_axis(-1, 0))

with TimeContext('map-process'):
    for d in docs.map(foo, backend='process'):
        pass

with TimeContext('map-thread'):
    for d in docs.map(foo, backend='thread'):
        pass

with TimeContext('for-loop'):
    for d in docs:
        foo(d)
```

```text
map-process ...	map-process takes 5 seconds (5.55s)
map-thread ...	map-thread takes 10 seconds (10.28s)
for-loop ...	for-loop takes 18 seconds (18.52s)
```

## Methods

All the following methods can be chained.


<!-- fluent-interface-start -->
### Convert
Provide helper functions for {class}`Document` to support conversion between {attr}`.blob`, {attr}`.text`
and {attr}`.buffer`.
- {meth}`~jina.types.document.mixins.convert.ConvertMixin.convert_blob_to_buffer`
- {meth}`~jina.types.document.mixins.convert.ConvertMixin.convert_buffer_to_blob`
- {meth}`~jina.types.document.mixins.convert.ConvertMixin.convert_uri_to_datauri`


### TextData
Provide helper functions for {class}`Document` to support text data.
- {meth}`~jina.types.document.mixins.text.TextDataMixin.convert_blob_to_text`
- {meth}`~jina.types.document.mixins.text.TextDataMixin.convert_text_to_blob`
- {meth}`~jina.types.document.mixins.text.TextDataMixin.dump_text_to_datauri`
- {meth}`~jina.types.document.mixins.text.TextDataMixin.load_uri_to_text`


### ImageData
Provide helper functions for {class}`Document` to support image data.
- {meth}`~jina.types.document.mixins.image.ImageDataMixin.convert_buffer_to_image_blob`
- {meth}`~jina.types.document.mixins.image.ImageDataMixin.convert_image_blob_to_buffer`
- {meth}`~jina.types.document.mixins.image.ImageDataMixin.convert_image_blob_to_sliding_windows`
- {meth}`~jina.types.document.mixins.image.ImageDataMixin.convert_image_blob_to_uri`
- {meth}`~jina.types.document.mixins.image.ImageDataMixin.dump_image_blob_to_file`
- {meth}`~jina.types.document.mixins.image.ImageDataMixin.load_uri_to_image_blob`
- {meth}`~jina.types.document.mixins.image.ImageDataMixin.set_image_blob_channel_axis`
- {meth}`~jina.types.document.mixins.image.ImageDataMixin.set_image_blob_inv_normalization`
- {meth}`~jina.types.document.mixins.image.ImageDataMixin.set_image_blob_normalization`
- {meth}`~jina.types.document.mixins.image.ImageDataMixin.set_image_blob_shape`


### AudioData
Provide helper functions for {class}`Document` to support audio data.
- {meth}`~jina.types.document.mixins.audio.AudioDataMixin.dump_audio_blob_to_file`
- {meth}`~jina.types.document.mixins.audio.AudioDataMixin.load_uri_to_audio_blob`


### BufferData
Provide helper functions for {class}`Document` to handle binary data.
- {meth}`~jina.types.document.mixins.buffer.BufferDataMixin.dump_buffer_to_datauri`
- {meth}`~jina.types.document.mixins.buffer.BufferDataMixin.load_uri_to_buffer`


### DumpFile
Provide helper functions for {class}`Document` to dump content to a file.
- {meth}`~jina.types.document.mixins.dump.DumpFileMixin.dump_buffer_to_file`
- {meth}`~jina.types.document.mixins.dump.DumpFileMixin.dump_uri_to_file`


### ContentProperty
Provide helper functions for {class}`Document` to allow universal content property access.
- {meth}`~jina.types.document.mixins.content.ContentPropertyMixin.dump_content_to_datauri`


### VideoData
Provide helper functions for {class}`Document` to support video data.
- {meth}`~jina.types.document.mixins.video.VideoDataMixin.dump_video_blob_to_file`
- {meth}`~jina.types.document.mixins.video.VideoDataMixin.load_uri_to_video_blob`


### SingletonSugar
Provide sugary syntax for {class}`Document` by inheriting methods from {class}`DocumentArray`
- {meth}`~jina.types.document.mixins.sugar.SingletonSugarMixin.embed`
- {meth}`~jina.types.document.mixins.sugar.SingletonSugarMixin.match`


### MeshData
Provide helper functions for {class}`Document` to support 3D mesh data and point cloud.
- {meth}`~jina.types.document.mixins.mesh.MeshDataMixin.load_uri_to_point_cloud_blob`


<!-- fluent-interface-end -->
