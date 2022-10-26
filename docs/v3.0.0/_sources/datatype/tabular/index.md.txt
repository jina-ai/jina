(table-type)=
# {octicon}`table` Table


Many interesting data in computing are tabular in form, like a table. An  inbox is a list of messages. For each message, your inbox stores a bunch of information: its sender, the subject line, the conversation it’s part of, the body, and quite a bit more. A music playlist. For each song, your music player maintains a bunch of information: its name, the singer, its length, its genre, and so on. A filesystem folder or directory. For each file, your filesystem records a name, a modification date, size, and other information.

```{figure} email-tabular.png
:align: center
:width: 80%
```

Tabular data consists of rows and columns. For instance, each song or email message or file is a row. Each of their characteristics: e.g. the song title, the message subject, the filename, is a column. A given column has the same type, but different columns can have different types. For instance, an email message has a sender’s name, which is a string; a subject line, which is a string; a sent date, which is a date; whether it’s been read, which is a Boolean; and so on.


## Load CSV table

With `from_csv` API, one can easily load tabular data from `csv` file into a `DocumentArray`. For example, 

```text
Username;Identifier;First name;Last name
booker12;9012;Rachel;Booker
grey07;2070;Laura;Grey
johnson81;4081;Craig;Johnson
jenkins46;9346;Mary;Jenkins
smith79;5079;Jamie;Smith
```

```python
from jina import DocumentArray

da = DocumentArray.load_csv('toy.csv')
```

```text
DocumentArray has 5 items (showing first three):
{'id': 'ed9004bc-382c-11ec-847e-1e008a366d48', 'tags': {'Last name': 'Booker', 'Username': 'booker12', ' Identifier': '9012', 'First name': 'Rachel'}},
{'id': 'ed9009bc-382c-11ec-847e-1e008a366d48', 'tags': {'First name': 'Laura', 'Last name': 'Grey', ' Identifier': '2070', 'Username': 'grey07'}},
{'id': 'ed900dea-382c-11ec-847e-1e008a366d48', 'tags': {'Username': 'johnson81', 'Last name': 'Johnson', 'First name': 'Craig', ' Identifier': '4081'}}
```

One can observe that each row is loaded as a `Document` and the columns are loaded into `Document.tags`.

Let's change the column of this toy CSV and try it again:

```text
text;Identifier;First name;Last name
booker12;9012;Rachel;Booker
grey07;2070;Laura;Grey
johnson81;4081;Craig;Johnson
jenkins46;9346;Mary;Jenkins
smith79;5079;Jamie;Smith
```

```python
da = DocumentArray.load_csv('toy.csv')
```

```text
DocumentArray has 5 items (showing first three):
{'id': 'a4ef61c0-382d-11ec-8bc1-1e008a366d48', 'tags': {'Last name': 'Booker', 'First name': 'Rachel', ' Identifier': '9012'}, 'text': 'booker12'},
{'id': 'a4ef6a44-382d-11ec-8bc1-1e008a366d48', 'tags': {'First name': 'Laura', ' Identifier': '2070', 'Last name': 'Grey'}, 'text': 'grey07'},
{'id': 'a4ef6f80-382d-11ec-8bc1-1e008a366d48', 'tags': {' Identifier': '4081', 'Last name': 'Johnson', 'First name': 'Craig'}, 'text': 'johnson81'}
```

This time `text` column is directly loaded into `Document.text` attribute. In general, `from_csv` will try its best to resolve the column names of the table and map them into the corresponding Document attributes. If such attempt fails, one can always resolve the field manually via:

```python
from jina import DocumentArray

da = DocumentArray.load_csv('toy.csv', field_resolver={'Identifier': 'id'})
```

```text
DocumentArray has 5 items (showing first three):
{'id': '9012', 'tags': {'Last name': 'Booker', 'Username': 'booker12', 'First name': 'Rachel'}},
{'id': '2070', 'tags': {'Username': 'grey07', 'First name': 'Laura', 'Last name': 'Grey'}},
{'id': '4081', 'tags': {'Username': 'johnson81', 'First name': 'Craig', 'Last name': 'Johnson'}}
```

## Save as CSV file

Saving a `DocumentArray` as a `csv` file is easy.

```python
da.save_csv('tmp.csv')
```

One thing needs to be careful is that tabular data is often not good for representing nested `Document`. Hence, nested Document will be stored in flatten.

If your Documents contain tags, and you want to store each tag in a separate column, then you can do:

```python
from jina import DocumentArray, Document

da = DocumentArray([Document(tags={'english': 'hello', 'german': 'hallo'}),
                    Document(tags={'english': 'world', 'german': 'welt'})])

da.save_csv('toy.csv', flatten_tags=True)
```

````{tab} flatten_tags=True

```text
id,tag__english,tag__german
029388a4-3830-11ec-b6b2-1e008a366d48,hello,hallo
0293968c-3830-11ec-b6b2-1e008a366d48,world,welt
```
````
````{tab} flatten_tags=False

```text
id,tags
418de220-3830-11ec-aad8-1e008a366d48,"{'german': 'hallo', 'english': 'hello'}"
418dec52-3830-11ec-aad8-1e008a366d48,"{'english': 'world', 'german': 'welt'}"
```
````


```{toctree}
:hidden:

filter-via-neural-search
```
