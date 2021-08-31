# {octicon}`mortar-board` Practice Your Learning

Now that you understand how to use public Executor from Hub, let's practice our learning with three hello-world demos in Jina.

## Modify `jina hello fashion` to use Hub executor

You can run the `jina hello fashion` demo using a different embedding method. To do so:

1) Clone the repository with  `jina hello fork fashion <your_project_folder>`. In `your_project_folder` you will
   have a file `app.py`  that you can change to leverage other embedding methods.

2) Change lines 74 to 79 from `app.py` to define a different `Flow`. For example, you can
   use  [ImageTorchEncoder](https://github.com/jina-ai/executor-image-torch-encoder)
   changing

   ```python
   f = (Flow()
      .add(uses=MyEncoder, parallel=2)
      .add(uses=MyIndexer, workspace=args.workdir)
      .add(uses=MyEvaluator)
   )
   ```

   with the flow

   ```python
   f = (
      Flow()
      .add(uses='jinahub+docker://ImageTorchEncoder',
         uses_with={'model_name': 'alexnet'},
         parallel=2)
      .add(uses=MyConverter)
      .add(uses=MyIndexer, workspace=args.workdir)
      .add(uses=MyEvaluator)
      )
   ```
   ````{admonition} Note
   :class: note
   The line `uses='jinahub+docker://ImageTorchEncoder` allows downloading
   `ImageTorchEncoder` from Jina Hub and use it in the `Flow`.
   ````
       
   ````{admonition} Note
   :class: note
   The line `uses_with={'model_name': 'alexnet'}` allows a user to specify an attribute of the
   class `ImageTorchEncoder`. In this case attribute `'model_name'` takes value `'alexnet'`.
   ````
   
3) Run `python <your_project_folder>/app.py` to execute.

## Modify `jina hello chatbot` to use Hub Executor



#### Use jina hub Executors

You can run the `jina hello chatbot` demo using a different embedding method. As an example, you can
use [TransformerTorchEncoder](https://github.com/jina-ai/executor-transformer-torch-encoder). To do so:

1) Clone the repository with  `jina hello fork chatbot <your_project_folder>`. In the repository you will
   have `app.py`  which you can change to leverage other embedding methods.

2) Change lines 21 to 25 from `app.py` to define a different `Flow`. Change
   ```python
   Flow(cors=True)
   .add(uses=MyTransformer, parallel=args.parallel)
   .add(uses=MyIndexer, workspace=args.workdir)
   ```
   with the flow

    ```python
    Flow(cors=True)
    .add(uses=MyTransformer, parallel=args.parallel)
    .add(s
        uses='jinahub+docker://TransformerTorchEncoder',
        parallel=args.parallel,
        uses_with={
            'pretrained_model_name_or_path': 'sentence-transformers/paraphrase-mpnet-base-v2'
        },
    )
    .add(uses=MyIndexer, workspace=args.workdir)
    ```
  
   ````{admonition} Note
   :class: note
   The line `uses='jinahub+docker://TransformerTorchEncoder'` allows downloading
   `TransformerTorchEncoder` from Jina Hub and use it in the `Flow`.
   ````
   ````{admonition} Note
   :class: note
   The line `uses_with={'pretrained_model_name_or_path': 'sentence-transformers/paraphrase-mpnet-base-v2'}` allows a
   user to specify an attribute of the class `ImageTorchEncoder`. In this case
   attribute `'pretrained_model_name_or_path'` takes value `'sentence-transformers/paraphrase-mpnet-base-v2'`.
   ````

3) Run `python <your_project_folder>/app.py` to execute.
    


## Modify `jina hello mutlimodal` to use Hub Executor

You can run the `jina hello multimodal` demo using a different embedding method. For example, you can
use  [ImageTorchEncoder](https://github.com/jina-ai/executor-image-torch-encoder). To do so:

1) Clone the repository with  `jina hello fork multimodal <your_project_folder>`. In the repository you will
   have `flow-index.yml` and `flow-search.yml`  which you can change to leverage other embedding methods.
    
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
3) Run `python <your_project_folder>/app.py` to execute.
