(image-type)=
# {octicon}`image` Image

````{tip}

To enable the full feature of Document API on image, you need to install `Pillow` and `matplotlib`.

```shell
pip install matplotlib pillow
```
````

Images and pictures are probably the most intuitive data for a lot of people. Comparing to textual data, image data is more universal and easier to comprehend. Neural search on image can be fun: from good-old content-based image retrieval to text2image or image2text cross-modality retrieval. With Jina, one can build all kinds of fancy applications on image data. In this chapter, we will introduce some common tasks that can be built with Jina.

Before we get started, let's recap what we know about image data.



## Image is `ndarray`

Image data is often just `ndarray`. Strictly speaking, not any `ndarray` but an `ndarray` with `ndim=2` or `ndim=3` and `dtype=uint8`. Each element in that `ndarray` represents the pixel value between 0 and 255 on certain **channel** at certain **position**. For example, a colored JPG image of 256x300 can be represented as an `ndarray` [256, 300, 3]. Why 3 in the last dimension? Because it represents R, G, B channels of each pixel. Some image has different number of channels. For example, a PNG with transparent background has 4 channels, where the extra channel represents opacity. A gray-scale image has only one channel, which represents the luminance.

In summary, an image can be stored as `.blob` in `Document`. But how do we get there?

## Load image data

You can load image data by specifying the image URI and then convert it into `.blob` using Document API

```{figure} apple.png
:align: center
:scale: 30%
```

```python
from jina import Document

d = Document(uri='apple.png')
d.load_uri_to_image_blob()

print(d.blob)
print(d.blob.shape)
```

```text
[[[255 255 255]
  [255 255 255]
  [255 255 255]
  ...
  [255 255 255]]]
(618, 641, 3)
```

## Simple image processing

Jina provides some functions to help you preprocess the image data. You can resize it (i.e. downsampling/upsampling) and normalize it; you can switch the channel axis of the `.blob` to meet certain requirements of other framework; and finally you can chain all these preprocessing steps together in one line. For example, before feeding data into a Pytorch-based ResNet Executor, the image needs to be normalized and the color axis should be at first, not at the last. You can do this via:

```python
from jina import Document

d = (
    Document(uri='apple.png')
    .load_uri_to_image_blob()
    .set_image_blob_shape(shape=(224, 224))
    .set_image_blob_normalization()
    .set_image_blob_channel_axis(-1, 0)
)

print(d.blob)
print(d.blob.shape)
```


```text
[[[2.2489083 2.2489083 2.2489083 ... 2.2489083 2.2489083 2.2489083]
  [2.2489083 2.2489083 2.2489083 ... 2.2489083 2.2489083 2.2489083]
  [2.2489083 2.2489083 2.2489083 ... 2.2489083 2.2489083 2.2489083]
  ...
  [2.64      2.64      2.64      ... 2.64      2.64      2.64     ]
  [2.64      2.64      2.64      ... 2.64      2.64      2.64     ]
  [2.64      2.64      2.64      ... 2.64      2.64      2.64     ]]]
(3, 224, 224)
```

You can also dump `.blob` back to a PNG image so that you can see.

```python
d.dump_image_blob_to_file('apple-proc.png', 0)
```

Note that the channel axis is now switched to 0 because the previous preprocessing steps we just conducted. 

```{figure} apple-proc.png
:align: center
:scale: 30%
```

Yep, this looks uneatable. That's often what you give to the deep learning algorithms. 

## Display image sprite

An image sprites is a collection of images put into a single image. When working with a `DocumentArray` of image `Documents`, you can directly view the image sprites via `plot_image_sprites`. This gives you a quick view of the dataset that you are working with:

```python
from jina import DocumentArray
from jina.types.document.generators import from_files

da = DocumentArray(from_files('/Users/hanxiao/Downloads/left/*.jpg'))
da.plot_image_sprites('sprite-img.png')
```

```text
⠇       DONE ━╸━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0:00:23 100% ETA: 0 seconds 40 steps done in 23 seconds
```

Depending on the number of images, this could take a while. But after that, you get a very nice overview of your `DocumentArray` as follows:

```{figure} sprite-img.png
:align: center
:width: 70%
```

## Segment large complicated image into small ones

A large complicated image is hard to search, as it may contain too many elements and interesting information and hence hard to define the search problem in the first place. Take the following image as an example, 

```{figure} complicated-image.jpeg
:align: center
:width: 80%
```

It contains rich information in details, and it is complicated as there is no single salience interest in the image. The user may want to hit this image by searching for "Krusty Burger" or "Yellow schoolbus". User's real intention is hard guess, which highly depends on the applications. But at least what we can do is using Jina to breakdown this complicated image into simpler ones. One of the simplest approaches is to cut the image via sliding windows.

```python
from jina import Document

d = Document(uri='docs/datatype/image/complicated-image.jpeg')
d.load_uri_to_image_blob()
print(d.blob.shape)

d.convert_image_blob_to_sliding_windows(window_shape=(64, 64))
print(d.blob.shape)
```

```text
(792, 1000, 3)
(180, 64, 64, 3)
```

As one can see, it converts the single image blob into 180 image blobs, each with the size of (64, 64, 3). You can also add all 180 image blobs into the chunks of this `Document`, simply do:

```python
d.convert_image_blob_to_sliding_windows(window_shape=(64, 64), as_chunks=True)

print(d.chunks)
```

```text
ChunkArray has 180 items (showing first three):
{'id': '7585b8aa-3826-11ec-bc1a-1e008a366d48', 'mime_type': 'image/jpeg', 'blob': {'dense': {'buffer': 'H8T0H8T0H8T0H8T0H8T0H8T0H8T0H8T0H8T0H8T0H8T0H8T0H8T0H8T0H8T0H8T0H8T0H8T0H8T0H8T0H8T0H8T0H8T0H8T0H8T0H8T0 ...
```

Let's now use image sprite to see how these chunks look like:

```python
d.chunks.plot_image_sprites('simpsons-chunks.png')
```

```{figure} simpsons-chunks.png
:align: center
:width: 80%
```

Hmm, doesn't change so much. This is because we scan the whole image using sliding windows with no overlap (i.e. stride). Let's do a bit oversampling:

```python
d.convert_image_blob_to_sliding_windows(window_shape=(64, 64), strides=(10, 10), as_chunks=True)
d.chunks.plot_image_sprites('simpsons-chunks-stride-10.png')
```

```{figure} simpsons-chunks-stride.png
:align: center
:width: 80%
```

Yep, that definitely looks better.


```{toctree}
:hidden:

image2image
text2image
small-images-inside-big-images/index
```