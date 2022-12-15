(audio-type)=
# {octicon}`unmute` Audio

Sound, or audio signals are signals that vibrate in the audible frequency range. When someone talks, it generates air
pressure signals; when you play music, the speaker converts electrical energy into mechanical energy. The mechanical
energy compresses air and converts the motion into sound energy. Your ear takes in these air pressure differences and
communicates with the brain. That's how audio works in the real world and we call it analog audio.

Digital audio data can be a soundbite, music, a ringtone, a background noise. It often comes in `.wav`, `.mp3`
formats, where the sound waves are digitized by sampling them at discrete intervals. There are many interesting neural
search tasks on audio data: music recommendations, similarity search for audio files, matching voice commands, voice
synthesis for chatbot. Before you start to build solutions with Jina, let's recap some fundamental knowledge about audio
data.

## Sampling rate

Sampling rate determines the sound frequency range (corresponding to pitch) which can be represented in the digital
waveform. It represents the quality of your audio data. Typical sampling frequencies are 8KHz, 16KHz and 44.1KHz. 1Hz
means one sample per second, so obviously higher sampling frequencies mean more samples per second and therefore better
signal quality.

```{figure} sampling-rate.jpeg
:align: center
:width: 80%
```

Different data loaders, mediums and file formats might have different sample rate requirements. For example, typical
studio recording audio has 192KHz. To make this recording as a CD, it should be resampled to CD sampling rate of
44.1KHz.

Fun fact, human ear can hear up to ~20KHz. Higher frequencies convey some emotions, and are useful for identification of
the speaker. In particular, if it is a human voice, then it is still intelligible at much lower sampling rate even when
higher frequencies are lost.

And you really don't want to hear a 4KHz music.

## Quantization

Another important concept in audio data is quantization. It is the process of reducing the infinite number precision of
an audio sample to a finite precision as defined by a particular number of bits. In the majority of the cases, 16 bits
per sample are used to represent each quantized sample, which means that there are 2{sup}`16` levels for the quantized
signal. Quantization also forms the core of essentially all lossy compression algorithms.

Following image depicts a simple wave quantized in 2bits (left) and 3bits (right).

```{figure} 2-3bit-quant.png
:align: center
:width: 80%
```

Let's listen to some soundbites and feel how quantization affects the audio quality. In this example, the original audio file
is at 16-bit, 44.1KHz.

<audio controls>
  <source src="../../_static/download.wav" type="audio/wav">
Your browser does not support the audio element.
</audio>

Now, we keep the sampling rate at 44.1KHz but reduce the number of bits used in quantization:


<table>
  <tr>
    <th>Quantization</th>
    <th>Audio</th>
  </tr>
  <tr>
    <td>8-bit</td>
    <td><audio controls><source src="../../_static/download%20(1).wav" type="audio/wav"></audio></td>
  </tr>
  <tr>
    <td>6-bit</td>
    <td><audio controls><source src="../../_static/download%20(2).wav" type="audio/wav"></audio></td>
  </tr>
<tr>
    <td>4-bit</td>
    <td><audio controls><source src="../../_static/download%20(3).wav" type="audio/wav"></audio></td>
  </tr>
<tr>
    <td>3-bit</td>
    <td><audio controls><source src="../../_static/download%20(4).wav" type="audio/wav"></audio></td>
  </tr>
<tr>
    <td>2-bit</td>
    <td><audio controls><source src="../../_static/download%20(5).wav" type="audio/wav"></audio></td>
  </tr>
</table>

Don't be flattered if you still recognize the 2-bit version. It is easy only because it is a human voice, which we are very good at recognizing. Try again with a music.

## Load `.wav` file 

You can use Jina Document API to load a wav file as a Document.

```python
from jina import Document

d = Document(uri='toy.wav').load_uri_to_audio_blob()

print(d.blob.shape, d.blob.dtype)
```

```text
(30833,) float32
```

## Save as `.wav` file

You can save Document `.blob` as a `.wav` file:

```python
d.dump_audio_blob_to_file('toy.wav')
```


## Example

Let's load the "hello" audio file, reverse it and finally save it.

```python
from jina import Document

d = Document(uri='hello.wav').load_uri_to_audio_blob()
d.blob = d.blob[::-1]
d.dump_audio_blob_to_file('olleh.wav')
```

<table>
  <tr>
    <th>hello.wav</th>
    <th>olleh.wav</th>
  </tr>
  <tr>
    <td><audio controls><source src="../../_static/hello.wav" type="audio/wav"></audio></td>
    <td><audio controls><source src="../../_static/olleh.wav" type="audio/wav"></audio></td>
  </tr>
</table>


## Other tools & libraries for audio data

By no means you are restricted to use Jina native methods for audio processing. Here are some command-line tools, programs and libraries to use for more advanced handling of audio data:

- [`FFmpeg`](https://ffmpeg.org) is a free, open-source project for handling multimedia files and streams. 
- [`pydub`](https://github.com/jiaaro/pydub): manipulate audio with a simple and easy high level interface
- [`librosa`](https://librosa.github.io/librosa/): a python package for music and audio analysis.
- [`pyAudioAnalysis`](https://github.com/tyiannak/pyAudioAnalysis): for IO or for more advanced feature extraction and signal analysis.


```{toctree}
:hidden:

similar-audio-search/index
```