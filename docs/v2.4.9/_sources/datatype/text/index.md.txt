(text-type)=
# {octicon}`typography` Text

Text is everywhere and it is easily accessible. Neural search with text is probably the first application one can think of. From fuzzy string matching to question-answering, you can leverage Jina to build all kinds of text-based neural search solution in just minutes. By leveraging the state-of-the-art natural language processing and pretrained models, you can easily use Jina to bring the text intelligence of your app to the next level.

In this chapter, we provide some tutorials to help you get started with different text-related tasks. But before that, let's recap our knowledge on `Document` and see how *in general* Jina is able to handle text data.

## Textual document

Representing text in Jina is easy. Simply do:
```python
from jina import Document

d = Document(text='hello, world.')
```

```text
{'id': '1b00cab2-3738-11ec-a7d6-1e008a366d48', 'mime_type': 'text/plain', 'text': 'hello, world.'}
```

If your text data is big and can not be written inline, or it comes from a URI, then you can also define `uri` first and load the text into Document later.

```python
from jina import Document

d = Document(uri='https://www.w3.org/History/19921103-hypertext/hypertext/README.html')
d.load_uri_to_text()
```

```text
{'id': 'c558c262-3738-11ec-861b-1e008a366d48', 'uri': 'https://www.w3.org/History/19921103-hypertext/hypertext/README.html', 'mime_type': 'text/plain', 'text': '<TITLE>Read Me</TITLE>\n<NEXTID 7>\n<H1>WorldWideWeb distributed code</H1>See the CERN <A NAME=2 HREF=Copyright.html>copyright</A> .  This is the README file which you get when\nyou unwrap one of our tar files. These files contain information about\nhypertext, hypertext systems, and the WorldWideWeb project. If you\nhave taken this with a .tar file, you will have only a subset of the\nfiles.<P>\nTHIS FILE IS A VERY ABRIDGED VERSION OF THE INFORMATION AVAILABLE\nON THE WEB.   IF IN DOUBT, READ THE WEB DIRECTLY. If you have not\ngot any browser installed, do this by telnet to info.cern.ch (no username\nor password).\n<H2>Archive Directory structure</...'}
```

And of course, you can have characters from different languages.

```python
from jina import Document

d = Document(text='👋	नमस्ते दुनिया!	你好世界！こんにちは世界！	Привет мир!')
```

```text
{'id': '225f7134-373b-11ec-8373-1e008a366d48', 'mime_type': 'text/plain', 'text': '👋\tनमस्ते दुनिया!\t你好世界！こんにちは世界！\tПривет мир!'}
```

## Segment long documents

Often times when you index/search textual document, you don't want to consider thousands of words as one document, some finer granularity would be nice. You can do these by leveraging `chunks` of `Document`. For example, let's segment this simple document by `!` mark:

```python
from jina import Document

d = Document(text='👋	नमस्ते दुनिया!	你好世界!こんにちは世界!	Привет мир!')

d.chunks.extend([Document(text=c) for c in d.text.split('!')])
```

```text
{'id': '6a863d84-373c-11ec-97cc-1e008a366d48', 'chunks': [{'id': '6a864158-373c-11ec-97cc-1e008a366d48', 'mime_type': 'text/plain', 'text': '👋\tनमस्ते दुनिया', 'granularity': 1, 'parent_id': '6a863d84-373c-11ec-97cc-1e008a366d48'}, {'id': '6a864202-373c-11ec-97cc-1e008a366d48', 'mime_type': 'text/plain', 'text': '\t你好世界', 'granularity': 1, 'parent_id': '6a863d84-373c-11ec-97cc-1e008a366d48'}, {'id': '6a8642a2-373c-11ec-97cc-1e008a366d48', 'mime_type': 'text/plain', 'text': 'こんにちは世界', 'granularity': 1, 'parent_id': '6a863d84-373c-11ec-97cc-1e008a366d48'}, {'id': '6a864324-373c-11ec-97cc-1e008a366d48', 'mime_type': 'text/plain', 'text': '\tПривет мир', 'granularity': 1, 'parent_id': '6a863d84-373c-11ec-97cc-1e008a366d48'}, {'id': '6a8643a6-373c-11ec-97cc-1e008a366d48', 'mime_type': 'text/plain', 'text': '', 'granularity': 1, 'parent_id': '6a863d84-373c-11ec-97cc-1e008a366d48'}], 'mime_type': 'text/plain', 'text': '👋\tनमस्ते दुनिया!\t你好世界!こんにちは世界!\tПривет мир!'}
```

Which creates five sub-documents under the original documents and stores them under `.chunks`. To see that more clearly, you can visualize it via `d.plot()`

```{figure} sample-chunks.svg
:align: center
:width: 80%
```

## Convert text into `ndarray`

Sometimes you may need to encode the text into a `numpy.ndarray` before further computation. We provide some helper functions in `Document` and `DocumentArray` that allow you to convert easily.

For example, we have a `DocumentArray` with three `Document`:
```python
from jina import DocumentArray, Document

da = DocumentArray([Document(text='hello world'), Document(text='goodbye world'), Document(text='hello goodbye')])
```

To get the vocabulary, you can use:
```python
vocab = da.get_vocabulary()
```

```text
{'hello': 2, 'world': 3, 'goodbye': 4}
```

The vocabulary is 2-indexed as `0` is reserved for padding symbol and `1` is reserved for unknown symbol.

One can further use this vocabulary to convert `.text` field into `.blob` via:

```python
for d in da:
    d.convert_text_to_blob(vocab)
    print(d.blob)
```

```text
[2 3]
[4 3]
[2 4]
```

When you have text in different length and you want the output `.blob` to have the same length, you can define `max_length` during converting:
```python
da = DocumentArray([Document(text='a short phrase'), Document(text='word'), Document(text='this is a much longer sentence')])
vocab = da.get_vocabulary()

for d in da:
    d.convert_text_to_blob(vocab, max_length=10)
    print(d.blob)
```

```text
[0 0 0 0 0 0 0 2 3 4]
[0 0 0 0 0 0 0 0 0 5]
[ 0  0  0  0  6  7  2  8  9 10]
```

You can get also use `.blobs` of `DocumentArray` to get all blobs in one `ndarray`.

```python
print(da.blobs)
````

```text
[[ 0  0  0  0  0  0  0  2  3  4]
 [ 0  0  0  0  0  0  0  0  0  5]
 [ 0  0  0  0  6  7  2  8  9 10]]
```

## Convert `ndarray` back to text

As a bonus, you can also easily convert an integer `ndarray` back to text based on some given vocabulary. This procedure is often termed as "decoding". 

```python
da = DocumentArray([Document(text='a short phrase'), Document(text='word'), Document(text='this is a much longer sentence')])
vocab = da.get_vocabulary()

# encoding
for d in da:
    d.convert_text_to_blob(vocab, max_length=10)

# decoding
for d in da:
    d.convert_blob_to_text(vocab)
    print(d.text)
```

```text
a short phrase
word
this is a much longer sentence
```

That's all you need to know for textual data. Good luck with building text search solution in Jina!

```{toctree}
:hidden:

../../tutorials/fuzzy-grep
full-text-search
../../tutorials/chatbot
../../tutorials/question-answering-bot
```
