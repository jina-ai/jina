# {octicon}`typography` Text

Text is everywhere and it is easily accesible. Neural search with text is probably the first application one can think of. From fuzzy string matching to question-answering, you can leverage Jina to build all kinds of text-based neural search solution in just minutes. By leveraging the state-of-the-art natural language processing and pretrained models, you can easily use Jina to bring the text intelligence of your app to the next level.

In this chapter, we provide some tutorials to help you get started with different text-related tasks. But before that, let's recap our knowledege on `Document` and see how *in general* Jina is able to handle text data.

## Textual Document

Representing text in Jina is easy. Simply do:
```python
from jina import Document

d = Document(text='hello, world.')
```

```bash
{'id': '1b00cab2-3738-11ec-a7d6-1e008a366d48', 'mime_type': 'text/plain', 'text': 'hello, world.'}
```

If your text data is big and can not be written inline, or it comes from a URI, then you can also define `uri` first and load the text into Document later.

```python
from jina import Document

d = Document(uri='https://www.w3.org/History/19921103-hypertext/hypertext/README.html')
d.convert_uri_to_text()
```

```bash
{'id': 'c558c262-3738-11ec-861b-1e008a366d48', 'uri': 'https://www.w3.org/History/19921103-hypertext/hypertext/README.html', 'mime_type': 'text/plain', 'text': '<TITLE>Read Me</TITLE>\n<NEXTID 7>\n<H1>WorldWideWeb distributed code</H1>See the CERN <A NAME=2 HREF=Copyright.html>copyright</A> .  This is the README file which you get when\nyou unwrap one of our tar files. These files contain information about\nhypertext, hypertext systems, and the WorldWideWeb project. If you\nhave taken this with a .tar file, you will have only a subset of the\nfiles.<P>\nTHIS FILE IS A VERY ABRIDGED VERSION OF THE INFORMATION AVAILABLE\nON THE WEB.   IF IN DOUBT, READ THE WEB DIRECTLY. If you have not\ngot any browser installed, do this by telnet to info.cern.ch (no username\nor password).\n<H2>Archive Directory structure</...'}
```

And of course, you can have characters from different languages.

```python
from jina import Document

d = Document(text='👋	नमस्ते दुनिया!	你好世界！こんにちは世界！	Привет мир!')
```

```bash
{'id': '225f7134-373b-11ec-8373-1e008a366d48', 'mime_type': 'text/plain', 'text': '👋\tनमस्ते दुनिया!\t你好世界！こんにちは世界！\tПривет мир!'}
```

## Segment long documents

Often times when you index/search textual document, you don't want to consider thousands of words as one document, some finer granularity would be nice. You can do these by leveraging `chunks` of `Document`. For example, let's segment this simple document by `!` mark:

```python
from jina import Document

d = Document(text='👋	नमस्ते दुनिया!	你好世界!こんにちは世界!	Привет мир!')

d.chunks.extend([Document(text=c) for c in d.text.split('!')])
```

```bash
{'id': '6a863d84-373c-11ec-97cc-1e008a366d48', 'chunks': [{'id': '6a864158-373c-11ec-97cc-1e008a366d48', 'mime_type': 'text/plain', 'text': '👋\tनमस्ते दुनिया', 'granularity': 1, 'parent_id': '6a863d84-373c-11ec-97cc-1e008a366d48'}, {'id': '6a864202-373c-11ec-97cc-1e008a366d48', 'mime_type': 'text/plain', 'text': '\t你好世界', 'granularity': 1, 'parent_id': '6a863d84-373c-11ec-97cc-1e008a366d48'}, {'id': '6a8642a2-373c-11ec-97cc-1e008a366d48', 'mime_type': 'text/plain', 'text': 'こんにちは世界', 'granularity': 1, 'parent_id': '6a863d84-373c-11ec-97cc-1e008a366d48'}, {'id': '6a864324-373c-11ec-97cc-1e008a366d48', 'mime_type': 'text/plain', 'text': '\tПривет мир', 'granularity': 1, 'parent_id': '6a863d84-373c-11ec-97cc-1e008a366d48'}, {'id': '6a8643a6-373c-11ec-97cc-1e008a366d48', 'mime_type': 'text/plain', 'text': '', 'granularity': 1, 'parent_id': '6a863d84-373c-11ec-97cc-1e008a366d48'}], 'mime_type': 'text/plain', 'text': '👋\tनमस्ते दुनिया!\t你好世界!こんにちは世界!\tПривет мир!'}
```

Which creates five sub-documents under the original documents and stores them under `.chunks`. To see that more clearly, you can visualize it via `d.plot()`

```{figure} sample-chunks.svg
:align: center
:width: 80%
```

That's all you need to know for textual data. Good luck with building text search solution in Jina!

```{toctree}
:hidden:

../../tutorials/fuzzy-grep
../../tutorials/chatbot
```
