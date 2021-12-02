## Building Flows
### Indexing
Now, after creating executors, it's time to use them in order to build an index Flow and index our data.

#### Building the index Flow
We create a Flow object and add executors one after the other with the right parameters:

1. YoloV5Segmenter: We should also specify the device
2. CLIPImageEncoder: It also receives the device parameter. And since we only encode the chunks, we specify 
`'traversal_paths': ['c']`
3. SimpleIndexer: We need to specify the workspace parameter
4. LMDBStorage: We also need to specify the workspace parameter. Furthermore, the executor can run in parallel to the 
other branch. We can achieve this using `needs='gateway'`. Finally, we set `default_traversal_paths` to `['r']`
5. A final executor which just waits for both branches.

After building the index Flow, we can plot it to verify that we're using the correct architecture.

```python
from jina import Flow
index_flow = Flow().add(uses=YoloV5Segmenter, name='segmenter', uses_with={'device': device}) \
  .add(uses=CLIPImageEncoder, name='encoder', uses_with={'device': device, 'traversal_paths': ['c']}) \
  .add(uses=SimpleIndexer, name='chunks_indexer', workspace='workspace') \
  .add(uses=LMDBStorage, name='root_indexer', workspace='workspace', needs='gateway', uses_with={'default_traversal_paths': ['r']}) \
  .add(name='wait_both', needs=['root_indexer', 'chunks_indexer'])
index_flow.plot()
```

```{figure} index_flow.svg
:align: center
```

Now it's time to index the dataset that we have downloaded. Actually, we will index images inside the `images` folder.
This helper function will convert image files into Jina Documents and yield them:

```python
from glob import glob
from jina import Document

def input_generator():
    for filename in glob('images/*.jpg'):
        doc = Document(uri=filename, tags={'filename': filename})
        doc.load_uri_to_image_blob()
        yield doc
```

The final step in this section is to send the input documents to the index Flow. Note that indexing can take a while:

```python
  with index_flow:
      input_docs = input_generator()
      index_flow.post(on='/index', inputs=input_docs, show_progress=True)
```

```text
Using cache found in /root/.cache/torch/hub/ultralytics_yolov5_master
Using cache found in /root/.cache/torch/hub/ultralytics_yolov5_master
⠏ 4/6 waiting segmenter encoder to be ready...YOLOv5 🚀 2021-10-29 torch 1.9.0+cu111 CPU

⠋ 4/6 waiting segmenter encoder to be ready...Fusing layers... 
⠼ 4/6 waiting segmenter encoder to be ready...Model Summary: 213 layers, 7225885 parameters, 0 gradients
Adding AutoShape... 
           Flow@1858[I]:🎉 Flow is ready to use!
	🔗 Protocol: 		GRPC
	🏠 Local access:	0.0.0.0:44619
	🔒 Private network:	172.28.0.2:44619
	🌐 Public address:	34.73.118.227:44619
⠦       DONE ━━╸━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0:01:11  0.0 step/s 2 steps done in 1 minute and 11 seconds
```

### Searching:
Now, let's build the search Flow and use it in order to find sample query images.

Our Flow contains the following executors:

1. CLIPImageEncoder: It receives the device parameter. This time, since we want to encode root query documents, 
we specify that `'traversal_paths': ['r']`
2. SimpleIndexer: We need to specify the workspace parameter
3. SimpleRanker
4. LMDBStorage: First we specify the workspace parameter. Then we need to use different traversal paths. This time 
we will be traversing matches: `'default_traversal_paths': ['m']`

```python
from jina import Flow
device = 'cpu'
query_flow = Flow().add(uses=CLIPImageEncoder, name='encoder', uses_with={'device': device, 'traversal_paths': ['r']}) \
  .add(uses=SimpleIndexer, name='chunks_indexer', workspace='workspace') \
  .add(uses=SimpleRanker, name='ranker') \
  .add(uses=LMDBStorage, workspace='workspace', name='root_indexer', uses_with={'default_traversal_paths': ['m']})
```

Let's plot our Flow

```python
query_flow.plot()
```

```{figure} query_flow.svg
:align: center
```

Finally, we can start querying. We will use images inside the `query` folder.
For each image, we will create a Jina Document. Then we send our documents to the query Flow and receive the response. 

For each query document, we can print the image and its top 3 search results

```python
import glob
with query_flow:
    docs = [Document(uri=filename) for filename in glob.glob('query/*.jpg')]
    for doc in docs:
        doc.load_uri_to_image_blob()
    resp = query_flow.post('/search', docs, return_results=True)
for doc in resp[0].docs:
    print('query:')
    plt.imshow(doc.blob)
    plt.show()
    print('results:')
    show_docs(doc.matches)
```

Sample results:
```text
query:
```
```{figure} query.png
:align: center
```

```text
results:
```
```{figure} result_1.png
:align: center
```
```{figure} result_2.png
:align: center
```
```{figure} result_3.png
:align: center
```

Congratulations !

The approach that we've adopted could effectively match the small bird image against bigger images containing birds.

Again, the full source code of this tutorial is available in this [google colab notebook](https://colab.research.google.com/drive/1gKNhJYl_qfy-ZKoEF7mMED6K1a4-CXHP?usp=sharing).

Feel free to try it !

