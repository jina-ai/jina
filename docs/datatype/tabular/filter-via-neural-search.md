(filter-row)=
# Filter Table Rows by Attributes

```{tip}
Find the full source code and run [TagsHasher](https://hub.jina.ai/executor/683nxytg/) on Jina Hub.
```


Big news, one can use Jina to filter table rows by their attributes! Such an amazing feature that only exists since... 47 years ago, aka SQL! Jina as a neural search framework surely won't implement a SQL database from scratch. The question here is: is it possible to leverage what we learned about neural search: embedding, indexing, nearest-neighbour matching to enable similar feature like SQL, e.g. filter, select?

Yes! Jina can do this. In this article, I will give you a walkthrough on how to filter the tabular data using Jina and without SQL (also no GPT-3). Let's call this mini-project as the neuretro-SQL.

## Feature hashing

The first thing you want to learn is feature hashing. I already gave a tutorial {ref}`at here<feature-hasing>`. I strongly recommend you to read that first before continue.

In general, feature hashing is a great way to embed **unbounded** number of features into fixed-size vectors. We will leverage the same idea here to embed the columns of the tabular data into fixed-size vectors.

## Load CSV as DocumentArray

Let's look at an example CSV file. Here I use a [film dataset](https://perso.telecom-paristech.fr/eagan/class/igr204/data/film.csv) that looks like the following:  

```{figure} film-dataset.png
```

Let's load the data from the web and put them into a DocumentArray:

```python
import io

from jina import Document, DocumentArray
from jina.types.document.generators import from_csv

# Load some online CSV file dataset
src = Document(
    uri='https://perso.telecom-paristech.fr/eagan/class/igr204/data/film.csv'
).load_uri_to_text('iso8859')
da = DocumentArray(from_csv(io.StringIO(src.text), dialect='auto'))
```

```text
<jina.types.arrays.document.DocumentArray (length=1660) at 5697295312>
```

Here we use Document API to download the data, convert it into the right charset, and load it via our CSV API as a DocumentArray.

Looks like we got 1660 Documents in total, let's take one sample from it and take a look:

```text
print(da[5].json())
```

```json
{
  "id": "16a9745c-3d99-11ec-a97f-1e008a366d49",
  "tags": {
    "*Image": "NicholasCage.png",
    "Actor": "Gere, Richard",
    "Actress": "Adams, Brooke",
    "Awards": "No",
    "Director": "Malick, Terrence",
    "Length": "94",
    "Popularity": "14",
    "Subject": "Drama",
    "Title": "Days of Heaven",
    "Year": "1978"
  }
}
```

It looks like this Document has two non-empty attributes `id` and `tags`, and all values in `tags` correspond to the column value we have in the CSV data. Now our task is clear: we want to filter Documents from this DocumentArray according to their values in `.tags`, but no SQL, pure Jina, pure neural search.

## Embed columns as vectors

To embed columns into vectors, we first notice that each "column-item" in `.tags` is actually a `Tuple[str, Any]` pair. The first part, a string, represents the column title, e.g. "Actor", "Actress", "Director". We can simply reuse our {ref}`previous hash function<str-hash>`:

```python
import hashlib

h = lambda x: int(hashlib.md5(str(x).encode('utf-8')).hexdigest(), base=16) % 256

h('Actor')
h('Director')
h('Length')
```

```text
163
111
117
```
Now that we have indices, the actual value on that index, namely the `Any` part of that `Tuple[str, Any]` pair needs some extra thought. First, some values are numbers like integers or floats, they are a good hash by themselves (e.g. 1996 is 1996, equal numbers are identity in semantics with no collision), so they do not need another hash function. Boolean values are the same, 0 and 1 are pretty representative. Strings can be handled in the same way above. What about lists, tuples and dicts? We can serialize them into JSON strings and then apply our string hash. The final hash function looks like the following:

```python
def _any_hash(self, v):
    try:
        return int(v)  # parse int parameter
    except ValueError:
        try:
            return float(v)  # parse float parameter
        except ValueError:
            if not v:
                # ignore it when the parameter is empty
                return 0
            if isinstance(v, str):
                v = v.strip()
                if v.lower() in {'true', 'yes'}:  # parse boolean parameter
                    return 1
                if v.lower() in {'false', 'no'}:
                    return 0
            if isinstance(v, (tuple, dict, list)):
                v = json.dumps(v, sort_keys=True)

    return int(self.hash(str(v).encode('utf-8')).hexdigest(), base=16)
```

If you apply this directly, you will get extremely big integers on the embedding values. Too big that you don't even want to look at or store it (for numerical and stability reason). So we need to bound it. Remember in full-text feature hashing example, we introduced `n_dim` to "horizontally" bound the dimensions of the embedding vector. We can follow the same spirit and introduce another variable `max_val` to "vertically" bound the dimensions of the vector:

```python
from jina import Executor
import hashlib

class TagsHasher(Executor):
    def __init__(self, n_dim: int = 256, max_val: int = 65536, sparse: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.n_dim = n_dim
        self.max_val = max_val
        self.hash = hashlib.md5
        self.sparse = sparse
```

Here we give a larger number to `max_val` then to `n_dim`. This is because the likelihood of a collision happens on vertical direction is in general much higher than on horizontal direction (otherwise, it implies there are more variants on the column name than on the column value, which then suggests the table-maker to simply "transpose" the whole table for better readability).

The final embedding procedure is then very simple:

```python
@requests
def encode(self, docs: DocumentArray, **kwargs):
    if self.sparse:
        from scipy.sparse import csr_matrix

    for idx, doc in enumerate(docs):
        if doc.tags:
            idxs, data = [], []  # sparse
            table = np.zeros(self.n_dim)  # dense
            for k, v in doc.tags.items():
                h = self._any_hash(k)
                sign_h = np.sign(h)
                col = h % self.n_dim
                val = self._any_hash(v)
                sign_v = np.sign(val)
                val = val % self.max_val
                idxs.append((0, col))
                val = sign_h * sign_v * val
                data.append(val)
                table[col] += val

            if self.sparse:
                doc.embedding = csr_matrix(
                    (data, zip(*idxs)), shape=(1, self.n_dim)
                )
            else:
                doc.embedding = table
```

## Put all together

Let's encode our loaded DocumentArray:
```python
from jina import Executor

th = Executor.load_config('jinahub://TagsHasher')

th.encode(da)
```

Now let's build some filters as Document:

```python
filters = [
    {"Subject": "Comedy"},
    {"Year": 1987},
    {"Subject": "Comedy", "Year": 1987}
]

qa = DocumentArray([Document(tags=f) for f in filters])
```

Encode the filter with `TagsHasher` to get the embeddings.

```python
th.encode(qa)
```

Now that we have embeddings for both indexed docs `da` (i.e. our film CSV table), and the query docs `qa` (our filters), we can use `.match` function to find nearest neighbours.

```python
qa.match(da, limit=5, exclude_self=True, metric='jaccard', use_scipy=True)
```

Note that here I use Jaccard distance instead of the  cosine distance. This is because the closeness of the value on each feature is meaningless, as the value is the result of a hash function. Whereas in `FeatureHashser`'s example, the value represents the term frequency of a word, so it was meaningful there. This needs to be kept in mind when using `TagsHasher`.

Finally, let's see some results. Here I only print top-5 matches.

```python
for d in qa:
    print('my filter is:', d.tags.json())
    for m in d.matches:
        print(m.tags.json())
```

````{tab} "Subject": "Comedy"

```json
{
  "*Image": "NicholasCage.png",
  "Actor": "Chase, Chevy",
  "Actress": "",
  "Awards": "No",
  "Director": "",
  "Length": "",
  "Popularity": "82",
  "Subject": "Comedy",
  "Title": "Valkenvania",
  "Year": "1990"
}
{
  "*Image": "paulNewman.png",
  "Actor": "Newman, Paul",
  "Actress": "",
  "Awards": "No",
  "Director": "",
  "Length": "",
  "Popularity": "28",
  "Subject": "Comedy",
  "Title": "Secret War of Harry Frigg, The",
  "Year": "1968"
}
{
  "*Image": "NicholasCage.png",
  "Actor": "Murphy, Eddie",
  "Actress": "",
  "Awards": "No",
  "Director": "",
  "Length": "",
  "Popularity": "56",
  "Subject": "Comedy",
  "Title": "Best of Eddie Murphy, Saturday Night Live, The",
  "Year": "1989"
}
{
  "*Image": "NicholasCage.png",
  "Actor": "Mastroianni, Marcello",
  "Actress": "",
  "Awards": "No",
  "Director": "Fellini, Federico",
  "Length": "",
  "Popularity": "29",
  "Subject": "Comedy",
  "Title": "Ginger & Fred",
  "Year": "1993"
}
{
  "*Image": "NicholasCage.png",
  "Actor": "Piscopo, Joe",
  "Actress": "",
  "Awards": "No",
  "Director": "",
  "Length": "60",
  "Popularity": "14",
  "Subject": "Comedy",
  "Title": "Joe Piscopo New Jersey Special",
  "Year": "1987"
}
```
````
````{tab} "Year": 1987.0
```json
{
  "*Image": "NicholasCage.png",
  "Actor": "",
  "Actress": "Madonna",
  "Awards": "No",
  "Director": "",
  "Length": "50",
  "Popularity": "75",
  "Subject": "Music",
  "Title": "Madonna Live, The Virgin Tour",
  "Year": "1987"
}
{
  "*Image": "NicholasCage.png",
  "Actor": "Piscopo, Joe",
  "Actress": "",
  "Awards": "No",
  "Director": "",
  "Length": "60",
  "Popularity": "14",
  "Subject": "Comedy",
  "Title": "Joe Piscopo New Jersey Special",
  "Year": "1987"
}
{
  "*Image": "NicholasCage.png",
  "Actor": "Everett, Rupert",
  "Actress": "",
  "Awards": "No",
  "Director": "",
  "Length": "95",
  "Popularity": "25",
  "Subject": "Drama",
  "Title": "Hearts of Fire",
  "Year": "1987"
}
{
  "*Image": "NicholasCage.png",
  "Actor": "Lambert, Christopher",
  "Actress": "Sukowa, Barbara",
  "Awards": "No",
  "Director": "Cimino, Michael",
  "Length": "",
  "Popularity": "41",
  "Subject": "Drama",
  "Title": "Sicilian, The",
  "Year": "1987"
}
{
  "*Image": "NicholasCage.png",
  "Actor": "Hubley, Whip",
  "Actress": "",
  "Awards": "No",
  "Director": "Rosenthal, Rick",
  "Length": "98",
  "Popularity": "87",
  "Subject": "Action",
  "Title": "Russkies",
  "Year": "1987"
}
```
````
````{tab} { "Subject": "Comedy", "Year": 1987.0}
```json
{
  "*Image": "NicholasCage.png",
  "Actor": "Piscopo, Joe",
  "Actress": "",
  "Awards": "No",
  "Director": "",
  "Length": "60",
  "Popularity": "14",
  "Subject": "Comedy",
  "Title": "Joe Piscopo New Jersey Special",
  "Year": "1987"
}
{
  "*Image": "NicholasCage.png",
  "Actor": "Murphy, Eddie",
  "Actress": "",
  "Awards": "No",
  "Director": "Murphy, Eddie",
  "Length": "90",
  "Popularity": "51",
  "Subject": "Comedy",
  "Title": "Eddie Murphy Raw",
  "Year": "1987"
}
{
  "*Image": "NicholasCage.png",
  "Actor": "McCarthy, Andrew",
  "Actress": "Cattrall, Kim",
  "Awards": "No",
  "Director": "Gottlieb, Michael",
  "Length": "",
  "Popularity": "23",
  "Subject": "Comedy",
  "Title": "Mannequin",
  "Year": "1987"
}
{
  "*Image": "NicholasCage.png",
  "Actor": "Williams, Robin",
  "Actress": "",
  "Awards": "No",
  "Director": "Levinson, Barry",
  "Length": "120",
  "Popularity": "37",
  "Subject": "Comedy",
  "Title": "Good Morning, Vietnam",
  "Year": "1987"
}
{
  "*Image": "NicholasCage.png",
  "Actor": "Boys, The Fat",
  "Actress": "",
  "Awards": "No",
  "Director": "Schultz, Michael",
  "Length": "86",
  "Popularity": "69",
  "Subject": "Comedy",
  "Title": "Disorderlies",
  "Year": "1987"
}
```
````

Not bad!