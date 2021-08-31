## 🤖 Covid-19 chatbot

<a href="https://docs.jina.ai/">
<img align="right" width="25%" src="https://github.com/jina-ai/jina/blob/master/.github/images/helloworld-chatbot.gif?raw=true" />
</a>

For NLP engineers, we provide a simple chatbot demo for answering Covid-19 questions. To run that:

```bash
pip install "jina[demo]"

jina hello chatbot
```

This downloads [CovidQA dataset](https://www.kaggle.com/xhlulu/covidqa) and tells Jina to index 418 question-answer
pairs with MPNet. The index process takes about 1 minute on CPU. Then it opens a web page where you can input questions
and ask Jina.

<br><br>

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
    
