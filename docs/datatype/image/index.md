# {octicon}`image` Image

Images and pictures are probably the most intuitive data for a lot of people. Comparing to textual data, image data is more universal and easier to comprehend. Neural search on image can be fun: from good-old content-based image retrieval to text2image or image2text cross-modality retrieval. With Jina, one can build all kinds of fancy applications on image data. In this chapter, we will introduce you common tasks that can be built with Jina.

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
d.convert_image_uri_to_blob()

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

## Simple preprocessing on image data

Jina offers some functions to help you preprocess the image data. You can resize it (i.e. downsampling/upsampling) and normalize it; you can switch the channel axis of the `.blob` to meet certain requirements of other framework; and finally you can chain all these preprocessing steps together in one line. For example, before feeding data into a Pytorch-based ResNet Executor, the image needs to be normalized and the color axis should be at first, not at the last. You can do this via:

```python
from jina import Document

d = (
    Document(uri='apple.png')
    .convert_image_uri_to_blob()
    .resize_image_blob(224, 224)
    .normalize_image_blob()
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

Yep, this looks uneatable. That's often what you give to the deep learning algorithm. 