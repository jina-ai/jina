# Document
<h3> 1. What can kind of data can a Document contain? </h3>
<ul>
<p> <input type="checkbox"> Just plain text </p>
<p> <input type="checkbox"> Numpy array </p>
<p> <input type="checkbox"> Any kind of data </p>
</ul>
<details>
<summary>Reveal explanation</summary>
<p>
<p><a href="https://docs.jina.ai/fundamentals/document/document-api/#document-content">A Document can contain <em>any</em> kind of data that can be stored digitally</a>. Text, graphics, audio, video, amino acids, 3D meshes, Numpy arrays, you name it.</p>

</p>
</details>
<h3> 2. Given a Document <code>doc</code>, what does <code>doc.content</code> refer to? </h3>
<ul>
<p> <input type="checkbox"> <code>doc.buffer</code> </p>
<p> <input type="checkbox"> <code>doc.blob</code> </p>
<p> <input type="checkbox"> <code>doc.text</code> </p>
<p> <input type="checkbox"> Any of the above as long as the field is not empty </p>
</ul>
<details>
<summary>Reveal explanation</summary>
<p>
<p><a href="https://docs.jina.ai/fundamentals/document/document-api/#document-content"><code>doc.content</code></a> is an alias that points to whatever attribute contains data. At any given point only <code>.buffer</code>, <code>.blob</code> or <code>.text</code> can contain data. Setting one of these attributes will unset any of the others that were previously in use.</p>

</p>
</details>
<h3> 3. How do you convert <code>doc.uri</code> to <code>doc.blob</code>? </h3>
<ul>
<p> <input type="checkbox"> <pre><code class="language-python">from jina.Document import convert_uri_to_blob

doc = Document(uri=&quot;foo.txt&quot;)
doc.blob = convert_uri_to_blob(doc)
</code></pre>
 </p>
<p> <input type="checkbox"> <pre><code class="language-python">from jina.Document import blob

doc = Document(uri=&quot;foo.txt&quot;)
doc.blob = blob(doc.uri)
</code></pre>
 </p>
<p> <input type="checkbox"> <pre><code class="language-python">doc = Document(uri=&quot;foo.txt&quot;)
doc.convert_uri_to_blob()
</code></pre>
 </p>
</ul>
<details>
<summary>Reveal explanation</summary>
<p>
<p>Converting to a blob is a built-in method of a <code>Document</code> object (as are many other <a href="https://docs.jina.ai/fundamentals/document/document-api/#conversion-from-uri-to-content"><code>.convert_x_to_y</code> methods</a>)</p>

</p>
</details>
<h3> 4. In what format is a Document&#39;s embedding? </h3>
<ul>
<p> <input type="checkbox"> An array (<code>numpy.ndarray</code>, Scipy sparse array, TensorFlow/PyTorch sparse array, etc) </p>
<p> <input type="checkbox"> Byte string </p>
<p> <input type="checkbox"> Protobuf </p>
<p> <input type="checkbox"> Plain text </p>
</ul>
<details>
<summary>Reveal explanation</summary>
<p>
<p>An embedding is a multi-dimensional representation of a Document. <a href="https://docs.jina.ai/fundamentals/document/document-api/#document-embedding">You can assign any Numpy ndarray as a Document’s embedding or use other array formats for sparse embeddings</a>.</p>

</p>
</details>
<h3> 5. What&#39;s the most efficient way to create a <code>DocumentArray</code> from a directory of images? </h3>
<pre><code class="language-python">from jina import DocumentArray
from jina.types.document.generators import from_files

doc_array = DocumentArray(from_files(&quot;image_dir/*.png&quot;))
</code></pre>
<pre><code class="language-python">from jina import Document, DocumentArray
import os

doc_array = DocumentArray()
for image in os.listdir(&quot;image_dir&quot;):
  doc_array.append(Document(uri=image))
</code></pre>
<pre><code class="language-python">from jina import DocumentArray

doc_array = DocumentArray(&quot;image_dir&quot;)
</code></pre>
<details>
<summary>Reveal explanation</summary>
<p>
<p>Many generators can be imported from <code>jina.types.document.generators</code> to easily create <code>DocumentArrays</code> of <a href="https://docs.jina.ai/fundamentals/document/document-api/#construct-from-json-csv-ndarray-and-files">different data types</a>.</p>

</p>
</details>
<h3> 6. What&#39;s the recommended way to add sub-Documents to <code>Document.chunks</code>? </h3>
<pre><code class="language-python">from jina import Document

root_document = Document(text=&#39;i am root&#39;)
root_document.chunks.append(Document(text=&#39;i am chunk 1&#39;))
root_document.chunks.extend([
   Document(text=&#39;i am chunk 2&#39;),
   Document(text=&#39;i am chunk 3&#39;),
])
</code></pre>
<pre><code class="language-python">from jina import Document

root_document = Document(
   text=&#39;i am root&#39;,
   chunks=[
      Document(text=&#39;i am chunk 2&#39;),
      Document(text=&#39;i am chunk 3&#39;),
   ]
)
</code></pre>
<details>
<summary>Reveal explanation</summary>
<p>
<p>When adding sub-Documents to Document.chunks, <a href="https://docs.jina.ai/fundamentals/document/document-api/#caveat-order-matters">do not create them in one line to keep recursive document structure correct</a>. This is because chunks use ref_doc to control its granularity, at chunk creation time, it didn’t know anything about its parent, and will get a wrong granularity value.</p>

</p>
</details>
<h3> 7. What&#39;s the recommended way to filter Documents from a <code>DocumentArray</code> that only contain a <code>city</code> tag beginning with &quot;B&quot;? </h3>
<pre><code class="language-python">d1 = Document(tags={&#39;city&#39;: &#39;Barcelona&#39;, &#39;phone&#39;: &#39;None&#39;})
d2 = Document(tags={&#39;city&#39;: &#39;Berlin&#39;, &#39;phone&#39;: &#39;648907348&#39;})
d3 = Document(tags={&#39;city&#39;: &#39;Paris&#39;, &#39;phone&#39;: &#39;None&#39;})
d4 = Document(tags={&#39;city&#39;: &#39;Brussels&#39;, &#39;phone&#39;: &#39;None&#39;})

docarray = DocumentArray([d1, d2, d3, d4])
regexes = {&#39;city&#39;: r&#39;B.*&#39;}
docarray_filtered = docarray.find(regexes=regexes)
</code></pre>
<pre><code class="language-python">d1 = Document(tags={&#39;city&#39;: &#39;Barcelona&#39;, &#39;phone&#39;: &#39;None&#39;})
d2 = Document(tags={&#39;city&#39;: &#39;Berlin&#39;, &#39;phone&#39;: &#39;648907348&#39;})
d3 = Document(tags={&#39;city&#39;: &#39;Paris&#39;, &#39;phone&#39;: &#39;None&#39;})
d4 = Document(tags={&#39;city&#39;: &#39;Brussels&#39;, &#39;phone&#39;: &#39;None&#39;})

docarray = DocumentArray([d1, d2, d3, d4])

filtered_docarray = DocumentArray()
for doc in docarray:
  if doc.tags[&quot;city&quot;][0] == &quot;B&quot;:
    filter_docarray.append(doc)
</code></pre>
<details>
<summary>Reveal explanation</summary>
<p>
<p>DocumentArray provides function <a href="https://docs.jina.ai/fundamentals/document/documentarray-api/#advanced-filtering-via-find">.find</a> that finds the Documents in the DocumentArray whose tag values match a dictionary of user provided regular expressions. Since a Document can have many tags, the function expects one regular expression for each tag that a user wants to consider.</p>

</p>
</details>
<h3> 8. When would you use <code>DocumentArrayMemmap</code> instead of <code>DocumentArray</code>? </h3>
<ul>
<p> <input type="checkbox"> <code>DocumentArrayMemmap</code> is just the name for <code>DocumentArray</code> in the internals of Jina code </p>
<p> <input type="checkbox"> When you need to index a large number of <code>Document</code>s and don&#39;t want to exhaust your memory </p>
<p> <input type="checkbox"> When you want to save disk space </p>
</ul>
<details>
<summary>Reveal explanation</summary>
<p>
<p>When your DocumentArray object contains a large number of Document, holding it in memory can be very demanding. You may want to use <a href="https://docs.jina.ai/fundamentals/document/documentarraymemmap-api/">DocumentArrayMemmap</a> to alleviate this issue.</p>

</p>
</details>
<h3> 9. Which of the following does <code>DocumentArrayMemmap</code> NOT support? </h3>
<ul>
<p> <input type="checkbox"> <code>append</code> </p>
<p> <input type="checkbox"> <code>split</code> </p>
<p> <input type="checkbox"> <code>shuffle</code> </p>
<p> <input type="checkbox"> <code>sort</code> </p>
</ul>
<details>
<summary>Reveal explanation</summary>
<p>
<p>The API of <code>DocumentArrayMemmap</code> is almost the same as <code>DocumentArray</code>, but with a <a href="https://docs.jina.ai/fundamentals/document/documentarraymemmap-api/#api-side-by-side-vs-documentarray">few key differences</a>.</p>

</p>
</details>
<h3> 10. How would you convert a <code>DocumentArray</code> to a <code>DocumentArrayMemmap</code>? </h3>
<pre><code class="language-python">from jina import Document, DocumentArray, DocumentArrayMemmap

doc_array = DocumentArray([Document(text=&#39;hello&#39;), Document(text=&#39;world&#39;)])

doc_array_memmap = DocumentArrayMemmap(doc_array)
</code></pre>
<pre><code class="language-python">from jina import Document, DocumentArray, DocumentArrayMemmap
from jina.DocumentArray import convert_to_document_array_memmap

doc_array = DocumentArray([Document(text=&#39;hello&#39;), Document(text=&#39;world&#39;)])

doc_array_memmap = convert_to_document_array_memmap(doc_array)
</code></pre>
<pre><code class="language-python">from jina import Document, DocumentArray, DocumentArrayMemmap

doc_array = DocumentArray([Document(text=&#39;hello&#39;), Document(text=&#39;world&#39;)])

doc_array_memmap = DocumentArrayMemmap()
for doc in doc_array:
  doc_array_memmap.append(doc)
</code></pre>
<details>
<summary>Reveal explanation</summary>
<p>
<p><a href="https://docs.jina.ai/fundamentals/document/documentarraymemmap-api/#convert-to-from-documentarray">Converting a <code>DocumentArray</code> to a <code>DocumentMemmapArray</code></a> is just a matter of <a href="https://www.w3schools.com/python/python_casting.asp">casting</a>.</p>

</p>
</details>
