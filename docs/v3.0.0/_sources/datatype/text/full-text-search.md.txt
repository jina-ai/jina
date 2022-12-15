# Full Text Search via Feature Hashing

```{tip}
Find the full source code and run [FeatureHasher](https://hub.jina.ai/executor/7skg25gs/) on Jina Hub.
```

Full-text search often indicates solutions that are based on good-old term-frequency. Can Jina do that? Yes! And you know you come to the right community when we skip the question of why and directly comes to how. Jokes asides, there are real-world use cases that have such requirement. In practice, not all text are necessarily to be embedded via heavy DNN, some texts such as keywords, phrases, simple sentences, source codes, commands, especially those semi-structured text are probably better by searching as-is.

This article will introduce you the basic idea of feature hashing, and how to use it for full text search.

## Good-old term frequency

Let's look at an example and recap what the term frequency is about. Say you have two sentences:

```text
i love jina
but does jina love me
```

If you apply term-frequency methodology, you first have to build a dictionary.
```text
{'i': 1, 'love': 2, 'jina': 3, 'but': 4, 'does': 5, 'me': 6}
```

And then convert the original sentences into 5-dimensional vectors:
```text
[1, 1, 1, 0, 0, 0]
[0, 1, 1, 1, 1, 1]
```

Note that this vector does not need to be 0-1 only, you can add term-frequency on each element. In the search time, you simply compute cosine distance of between your query vector and those indexed vectors.

The problem of this approach is the dimension of the final vector is **unbounded** and proportional to the vocabulary size, which you can not really grantee to be consistent during index and search time. In practice, this approach will easily result in 10K-dim sparse vector which are not really easy to store and compute.

This is basically the methodology we used in the first tutorial. 

(feature-hashing)=
## Feature hashing

Feature hashing is a fast and space-efficient way of turning arbitrary features into fixed-length vectors. It works by applying a hash function to the features and using their hash values as indices directly, rather than looking the indices up in an associative array.

Comparing to term-frequency, feature hashing defines a **bounded** embedding space, which is kept fixed and not increased with a growing data set. When using feature hashing, you can completely forget about vocabulary or feature set. They are irrelevant to the algorithm.

Let's see how it works. We first define the number of dimensions we want embed our text into, say 256.

Then we need a function that maps any word into [0, 255] so that each word will correspond to one column. For example,

(str-hash)=
```python
import hashlib

h = lambda x: int(hashlib.md5(str(x).encode('utf-8')).hexdigest(), base=16) % 256

h('i')
h('love')
h('jina')
```

```text
65
126
7
```

Here `h()` is our hash function, it is the essence of feature hashing. You are free to construct other hash functions: as long as they are fast, deterministic and yield few collisions.

Now that we have the indices, we can simply encode `i love jina` sentence as:
```python
import numpy as np

embed = np.zeros(256)
embed[65] = 1
embed[126] = 1
embed[7] = 1
```

Again, `embed` does not need to be 0-1 only, you can add term-frequency of each word on the element. You may also use sparse array to store the embedding to get better space-efficiency.

That's it. Very simple right?

## Build FeatureHasher executor

Let's write everything we learned into an Executor. The full source code can be [found here](https://hub.jina.ai/executor/7skg25gs/) 


Let's first add basic arguments to the `init` function:

```python
import hashlib
from typing import Tuple
from jina import Executor

class FeatureHasher(Executor):
    def __init__(self, n_dim: int = 256, sparse: bool = False, text_attrs: Tuple[str, ...] = ('text',), **kwargs):
        super().__init__(**kwargs)
        self.n_dim = n_dim
        self.hash = hashlib.md5
        self.text_fields = text_attrs
        self.sparse = sparse
```

`n_dim` plays the trade-off between space and hash effectiveness. An extreme case such as `n_dim=1` will force all words mapping into the same index which is really bad. A super large `n_dim` avoids most of the collisions yet not very space-efficient. In case you don't know what is the best option, just go with `256`. It is often good enough. 


Next we add our embedding algorithm to `encode()` and bind it with `@request`. This serves the core logic of the FeatureHasher.

```python
import numpy as np
from jina import DocumentArray, requests
    
    # ...
    
    @requests
    def encode(self, docs: DocumentArray, **kwargs):
        if self.sparse:
            from scipy.sparse import csr_matrix

        for idx, doc in enumerate(docs):
            all_tokens = doc.get_vocabulary(self.text_fields)
            if all_tokens:
                idxs, data = [], []  # sparse
                table = np.zeros(self.n_dim)  # dense
                for f_id, val in all_tokens.items():
                    h = int(self.hash(f_id.encode('utf-8')).hexdigest(), base=16)
                    col = h % self.n_dim
                    idxs.append((0, col))
                    data.append(np.sign(h) * val)
                    table[col] += np.sign(h) * val

                if self.sparse:
                    doc.embedding = csr_matrix((data, zip(*idxs)), shape=(1, self.n_dim))
                else:
                    doc.embedding = table
```

Here we use Document API `doc.get_vocabulary` to get all tokens and their counts in a `dict`. We then use the count, i.e. the term frequency as the value on certain index.


## Result

Let's take a look how to use it for full-text search. We first download the <Pride and Prejudice> and then cut it into non-empty sentences.

```python
from jina import Document, DocumentArray, Executor

# load <Pride and Prejudice by Jane Austen>
d = Document(uri='https://www.gutenberg.org/files/1342/1342-0.txt').load_uri_to_text()

# cut into non-empty sentences store in a DA
da = DocumentArray(Document(text=s.strip()) for s in d.text.split('\n') if s.strip())
```

Here we use Document API `load_uri_to_text` and store sentences in `da` as one DocumentArray.

Embed all of them with our FeatureHasher, and do a self-matching, take the top-5 results:
```python
exec = Executor.from_hub('jinahub://FeatureHasher')

exec.encode(da)

da.match(da, exclude_self=True, limit=5, normalization=(1, 0))
```

Let's print them
```python
for d in da:
    print(d.text)
    for m in d.matches:
        print(m.scores['cosine'], m.text)
    input()
```

```text
matching...
total sentences:  12153
﻿The Project Gutenberg eBook of Pride and Prejudice, by Jane Austen
<jina.types.score.NamedScore ('value',) at 5846290384> *** END OF THE PROJECT GUTENBERG EBOOK PRIDE AND PREJUDICE ***
<jina.types.score.NamedScore ('value',) at 5846288464> *** START OF THE PROJECT GUTENBERG EBOOK PRIDE AND PREJUDICE ***
<jina.types.score.NamedScore ('value',) at 5846289872> production, promotion and distribution of Project Gutenberg-tm
<jina.types.score.NamedScore ('value',) at 5846290000> Pride and Prejudice
<jina.types.score.NamedScore ('value',) at 5846289744> By Jane Austen


This eBook is for the use of anyone anywhere in the United States and
<jina.types.score.NamedScore ('value',) at 5846290000> This eBook is for the use of anyone anywhere in the United States and
<jina.types.score.NamedScore ('value',) at 5846289744> by the awkwardness of the application, and at length wholly
<jina.types.score.NamedScore ('value',) at 5846290000> Elizabeth passed the chief of the night in her sister’s room, and
<jina.types.score.NamedScore ('value',) at 5846289744> the happiest memories in the world. Nothing of the past was
<jina.types.score.NamedScore ('value',) at 5846290000> charities and charitable donations in all 50 states of the United
most other parts of the world at no cost and with almost no restrictions
<jina.types.score.NamedScore ('value',) at 5845950032> most other parts of the world at no cost and with almost no
<jina.types.score.NamedScore ('value',) at 5843094160> Pride and Prejudice
<jina.types.score.NamedScore ('value',) at 5845950032> Title: Pride and Prejudice
<jina.types.score.NamedScore ('value',) at 5845950352> With no expectation of pleasure, but with the strongest
<jina.types.score.NamedScore ('value',) at 5845763088> *** END OF THE PROJECT GUTENBERG EBOOK PRIDE AND PREJUDICE ***

whatsoever. You may copy it, give it away or re-use it under the terms
<jina.types.score.NamedScore ('value',) at 5845762960> restrictions whatsoever. You may copy it, give it away or re-use it
<jina.types.score.NamedScore ('value',) at 5845763088> man.
<jina.types.score.NamedScore ('value',) at 5845764624> Mr. Bennet came from it. The coach, therefore, took them the
<jina.types.score.NamedScore ('value',) at 5845713168> “I almost envy you the pleasure, and yet I believe it would be
<jina.types.score.NamedScore ('value',) at 5845764624> therefore, I shall be uniformly silent; and you may assure
```

In practice, you can implement matching and storing via an indexer inside `Flow`. 
This tutorial is only for demo purpose hence any non-feature hashing related ops are implemented without the Flow to avoid distraction.

Feature hashing is a simple yet elegant method not only for full-text search. It can be also used on tabular data, as we shall {ref}`see in this tutorial<filter-row>`. 
