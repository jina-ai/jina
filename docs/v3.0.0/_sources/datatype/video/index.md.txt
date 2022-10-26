(video-type)=
# {octicon}`device-camera-video` Video


````{tip}

To enable the full feature of Document API on video, you need to install `av`.

```shell
pip install av
```
````

Video data is a common asset consumed on daily basis: live stream on Youtube/TikTok, CCTV camera or fun meme gifs. 

Even though most applications of computer vision today center on images, thanks to those viral TikTokers, video data analysis has gained more attention recently, e.g. monitoring real-time video and analyzing archived video.

Comparing to static image, video allows for deeper situational understanding, because sequences of images provide new information about action. For example, we can track an obstacle through a sequence of images and understand its behavior to predict the next move. We can track a human pose, and understand the action taken with action classification.

Neural search on video often includes tasks such as in-video content search, video2video recommendation, video question-answering. Before you start to solve those tasks, let's take a quick tour on the video data format, and how Jina Document API can help you get started.


## Video as sequence of images

```{figure} flipbook-flip.gif
:width: 60%
```

Videos are nothing but a collection of a set of images. These images are called frames and can be combined to get the original video. An important concept here is the frame rate, which refers to the number of individual frames or images that are displayed per second of film or TV display. Movies and films are almost exclusively projected at 24 frames per second, or 24fps. The higher the frame rate, the smoother the video looks like and the bigger file size.

```{figure} framerate.gif
:width: 60%
```

In a nutshell, video processing can be seen as a sequence of operations done for each frame. Each frame includes processes of decoding, computation and encoding. Decoding is a conversion of the video frame from compressed format to the raw format. Computation is a certain operation which we need to do with the frame.

## Key frames

If video data is merely a sequence of frames, then how about converting the video to a collection of sequentially-numbered image files and process them one by one? Generating an image sequence has disadvantages: they can be large and unwieldy, and generating them can take some time. Besides, not all frames are equally useful or important. 

A key frame in video is a shot that defines the starting and ending points of any smooth transition. Subsequent frames, sometimes coined as the delta frames, only contain the information that has changed. Because only two or three key frames over the span of a second do not create the illusion of movement, the remaining frames are filled with "inbetweens".

Key frames will appear multiple times within a video, depending on how it was created or how it’s being streamed. A sequence of key frames defines which movement the viewer will see, whereas the position of the key frames on the film, video, or animation defines the timing of the movement. Extracting key frames from a video often gives a good representation of the video, as it preserves the salient feature of the video, while removes most of the repeated frames.





## Load video data

Let's use Jina Document API to load video this video:


<video controls width="60%">
<source src="../../_static/mov_bbb.mp4" type="video/mp4">
</video>


```python
from jina import Document

d = Document(uri='toy.mp4')
d.load_uri_to_video_blob()

print(d.blob.shape)
```

```text
(250, 176, 320, 3)
```

For video data, `.blob` is a 4-dim array, where the first dimension represents the frame id, or time. The last three dimensions represent the same thing as in image data. Here we got our `d.blob.shape=(250, 176, 320, 3)`, which means this video is sized in 176x320 and contains 250 frames. Based on the overall length of the video (10s), we can infer the framerate is around 250/10=25fps.

We can put each frame into a sub-Document in `.chunks` as use image sprite to visualize them.

```python
for b in d.blob:
    d.chunks.append(Document(blob=b))

d.chunks.plot_image_sprites('mov.png')
```

```{figure} mov_bbb.png
:align: center
:width: 70%
```

## Key frame extraction

From the sprite image one can observe our example video is quite redundant. Let's extract the key frames from this video and see:

```python
from jina import Document

d = Document(uri='toy.mp4')
d.load_uri_to_video_blob(only_keyframes=True)
print(d.blob.shape)
```

```text
(2, 176, 320, 3)
```

Looks like we only have two key frames, let's dump them into images and see what do they look like.

```python
for idx, c in enumerate(d.blob):
    Document(blob=c).dump_image_blob_to_file(f'chunk-{idx}.png')
```

```{figure} chunk-0.png
:align: center
:width: 40%
```

```{figure} chunk-1.png
:align: center
:width: 40%
```

Makes sense, right?

## Save as video file

One can also save a Document `.blob` as a video file. In this example, we load our `.mp4` video and store it into a 60fps video.

```python
from jina import Document

d = (
    Document(uri='toy.mp4')
    .load_uri_to_video_blob()
    .dump_video_blob_to_file('60fps.mp4', 60)
)
```

<video controls width="60%">
<source src="../../_static/60fps.mp4" type="video/mp4">
</video>


```{toctree}
:hidden:

../../tutorials/video-qa
../../tutorials/video-search
```
