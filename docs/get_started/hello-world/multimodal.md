## 🪆 Multimodal document search

<a href="https://youtu.be/B_nH8GCmBfc">
<img align="right" width="25%" src="https://github.com/jina-ai/jina/blob/master/.github/images/helloworld-multimodal.gif?raw=true" />
</a>

A multimodal-document contains multiple data types, e.g. a PDF document often contains figures and text. Jina lets you
build a multimodal search solution in just minutes. To run our minimum multimodal document search demo:

```bash
pip install "jina[multimodal]"

jina hello multimodal
```

This downloads [people image dataset](https://www.kaggle.com/ahmadahmadzada/images2000) and tells Jina to index 2,000
image-caption pairs with MobileNet and MPNet. The index process takes about 3 minute on CPU. Then it opens a web page
where you can query multimodal documents. We have prepared [a YouTube tutorial](https://youtu.be/B_nH8GCmBfc) to walk
you through this demo.

<br><br>

#### Use jina hub Executors

You can run the `jina hello multimodal` demo using a different embedding method. For example, you can
use  [ImageTorchEncoder](https://github.com/jina-ai/executor-image-torch-encoder). To do so:

-
    1) Clone the repository with  `jina hello fork multimodal <your_project_folder>`. In the repository you will
       have `flow-index.yml` and `flow-search.yml`  which you can change to leverage other embedding methods.

-
    2) Change `<your_project_folder>/flow-index.yml` with
```yaml
   jtype: Flow
   version: '1'
   executors:
     - name: segment
       uses:
         jtype: Segmenter
         metas:
           workspace: $HW_WORKDIR
           py_modules:
             - my_executors.py
     - name: craftText
       uses:
         jtype: TextCrafter
         metas:
           py_modules:
             - my_executors.py
     - name: encodeText
       uses: 'jinahub+docker://TransformerTorchEncoder'
     - name: textIndexer
       uses:
         jtype: DocVectorIndexer
         with:
           index_file_name: "text.json"
         metas:
           workspace: $HW_WORKDIR
           py_modules:
             - my_executors.py
     - name: craftImage
       uses:
         jtype: ImageCrafter
         metas:
           workspace: $HW_WORKDIR
           py_modules:
             - my_executors.py
       needs: segment
     - name: encodeImage
       uses: 'jinahub+docker://ImageTorchEncoder'
       uses_with:
         use_default_preprocessing: False
     - name: imageIndexer
       uses:
         jtype: DocVectorIndexer
         with:
           index_file_name: "image.json"
         metas:
           workspace: $HW_WORKDIR
           py_modules:
             - my_executors.py
     - name: keyValueIndexer
       uses:
         jtype: KeyValueIndexer
         metas:
           workspace: $HW_WORKDIR
           py_modules:
             - my_executors.py
       needs: segment
     - name: joinAll
       needs: [ textIndexer, imageIndexer, keyValueIndexer ]
```
and `flow-search.yml` with
   ```yaml
   jtype: Flow
   version: '1'
   with:
     cors: True
     expose_crud_endpoints: True
   executors:
     - name: craftText
       uses:
         jtype: TextCrafter
         metas:
           py_modules:
             - my_executors.py
     - name: encodeText
       uses: 'jinahub+docker://TransformerTorchEncoder'
     - name: textIndexer
       uses:
         jtype: DocVectorIndexer
         with:
           index_file_name: "text.json"
         metas:
           workspace: $HW_WORKDIR
           py_modules:
             - my_executors.py
     - name: craftImage
       uses:
         jtype: ImageCrafter
         metas:
           workspace: $HW_WORKDIR
           py_modules:
             - my_executors.py
       needs: gateway
     - name: encodeImage
       uses: 'jinahub+docker://ImageTorchEncoder'
       uses_with:
         use_default_preprocessing: False
     - name: imageIndexer
       uses:
         jtype: DocVectorIndexer
         with:
           index_file_name: "image.json"
         metas:
           workspace: $HW_WORKDIR
           py_modules:
             - my_executors.py
     - name: weightedRanker
       uses:
         jtype: WeightedRanker
         metas:
           workspace: $HW_WORKDIR
           py_modules:
             - my_executors.py
       needs: [ textIndexer, imageIndexer ]
     - name: keyvalueIndexer
       uses:
         jtype: KeyValueIndexer
         metas:
           workspace: $HW_WORKDIR
           py_modules:
             - my_executors.py
       needs: weightedRanker
   ```
- 3) Run `python <your_project_folder>/app.py` to execute.
    

````{admonition} See Also
:class: seealso

{ref}`JinaHub <hub-cookbook>`
````
