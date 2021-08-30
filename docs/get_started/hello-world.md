# Jina "Hello, World!" 👋🌍

Just starting out? Try Jina's "Hello, World" - `jina hello --help`

## 👗 Fashion Image Search

<a href="https://docs.jina.ai/">
<img align="right" width="25%" src="https://github.com/jina-ai/jina/blob/master/.github/images/hello-world.gif?raw=true" />
</a>

A simple image neural search demo for [Fashion-MNIST](https://hanxiao.io/2018/09/28/Fashion-MNIST-Year-In-Review/). No
extra dependencies needed, simply run:

```bash
jina hello fashion  # more options in --help
```

...or even easier for Docker users, **no install required**:

```bash
docker run -v "$(pwd)/j:/j" jinaai/jina hello fashion --workdir /j && open j/hello-world.html
 replace "open" with "xdg-open" on Linux
```

<details>
<summary>Click here to see console output</summary>

<p align="center">
  <img src="https://github.com/jina-ai/jina/blob/master/.github/images/hello-world-demo.png?raw=true" alt="hello world console output">
</p>


</details>
This downloads the Fashion-MNIST training and test dataset and tells Jina to index 60,000 images from the training set.
Then it randomly samples images from the test set as queries and asks Jina to retrieve relevant results.
The whole process takes about 1 minute.

<br><br>

#### Use Jina Hub Executors

You can run the `jina hello fashion` demo using a different embedding method. To do so:

-
    1) Clone the repository with  `jina hello fork fashion <your_project_folder>`. In `your_project_folder` you will
       have a file `app.py`  that you can change to leverage other embedding methods.

-
    2) Change lines 74 to 79 from `app.py` to define a different `Flow`. For example, you can
       use  [ImageTorchEncoder](https://github.com/jina-ai/executor-image-torch-encoder)
       changing

        ```python
       f = (
            Flow()
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
       Note two details:
        - The line `uses='jinahub+docker://ImageTorchEncoder` allows downloading
          `ImageTorchEncoder` from Jina Hub and use it in the `Flow`.
        - The line `uses_with={'model_name': 'alexnet'}` allows a user to specify an attribute of the
          class `ImageTorchEncoder`. In this case attribute `'model_name'` takes value `'alexnet'`.

-
    3) Run `python <your_project_folder>/app.py` to execute.

<br><br><br><br>

## 🤖 Covid-19 Chatbot

<a href="https://docs.jina.ai/">
<img align="right" width="25%" src="https://github.com/jina-ai/jina/blob/master/.github/images/helloworld-chatbot.gif?raw=true" />
</a>

For NLP engineers, we provide a simple chatbot demo for answering Covid-19 questions. To run that:

```bash
pip install "jina[chatbot]"

jina hello chatbot
```

This downloads [CovidQA dataset](https://www.kaggle.com/xhlulu/covidqa) and tells Jina to index 418 question-answer
pairs with MPNet. The index process takes about 1 minute on CPU. Then it opens a web page where you can input questions
and ask Jina.

<br><br>

#### Use Jina Hub Executors

You can run the `jina hello chatbot` demo using a different embedding method. As an example, you can
use [TransformerTorchEncoder](https://github.com/jina-ai/executor-transformer-torch-encoder). To do so:

-
    1) Clone the repository with  `jina hello fork chatbot <your_project_folder>`. In the repository you will
       have `app.py`  which you can change to leverage other embedding methods.

-
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
  .add(
      uses='jinahub+docker://TransformerTorchEncoder',
      parallel=args.parallel,
      uses_with={
       'pretrained_model_name_or_path': 'sentence-transformers/paraphrase-mpnet-base-v2'
      },
  )
  .add(uses=MyIndexer, workspace=args.workdir)
  ```
Note two details:
    - The line `uses='jinahub+docker://TransformerTorchEncoder'` allows downloading
      `TransformerTorchEncoder` from Jina Hub and use it in the `Flow`.
    - The line `uses_with={'pretrained_model_name_or_path': 'sentence-transformers/paraphrase-mpnet-base-v2'}` allows a
      user to specify an attribute of the class `ImageTorchEncoder`. In this case
      attribute `'pretrained_model_name_or_path'` takes value `'sentence-transformers/paraphrase-mpnet-base-v2'`.

-
    3) Run `python <your_project_folder>/app.py` to execute.

<br><br><br><br>

## 🪆 Multimodal Document Search

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

#### Use Jina Hub Executors

You can run the `jina hello fashion` demo using a different embedding method. For example, you can
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
