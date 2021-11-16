# Use Hub Executors in Hello World

```{article-info}
:avatar: avatars/david.jpg
:avatar-link: https://jobs.jina.ai
:avatar-outline: muted
:author: David @ Jina AI
:date: Aug. 10, 2021
```


이제 허브에서 퍼블릭 Executor를 사용하는 방법을 이해하셨으니 지나에서 세 가지 헬로월드 데모를 통해 학습 연습을 해보도록 하겠습니다..

## 허브 실행기를 사용하기 위해 `jina hello fashion` 수정하세요 

1)  `jina hello fork fashion <your_project_folder>`로 저장소를 복제하세요.  `your_project_folder`에서 당신은 다른 메서드를 임베딩 할수있는 파일 `app.py` 가질 것입니다.

2)  다른 'Flow`정의하기 위해서 `app.py`에서 74줄을 79줄로 바꾸세요. 예를들어, 당신은
    [ImageTorchEncoder](https://github.com/jina-ai/executor-image-torch-encoder):를 사용할수 있습니다

   ```python
   f = (
      Flow()
      .add(uses='jinahub+docker://ImageTorchEncoder',
         uses_with={'model_name': 'alexnet'},
         replicas=2)
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
    
3) 실행하기위해  `python <your_project_folder>/app.py`를 돌려주세요.

## 허브 실행기를 사용하기 위해 `jina hello chatbot` 수정하세요 
 

예를들어, 당신은
 [TransformerTorchEncoder](https://github.com/jina-ai/executor-transformer-torch-encoder) 사용할 수 있습니다. To do so:

1) `jina hello fork chatbot <your_project_folder>`로 저장소를 복제하세요.  `your_project_folder`에서 당신은 다른 메서드를 임베딩 할수있는 파일 `app.py` 가질 것입니다.

2) 다른 'Flow`정의하기 위해서 `app.py`에서 21줄을 25줄로 바꾸세요. Change it to:
    ```python
    Flow(cors=True)
    .add(uses=MyTransformer, replicas=args.replicas)
    .add(
        uses='jinahub+docker://TransformerTorchEncoder',
        replicas=args.replicas,
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

3) 실행하기위해 `python <your_project_folder>/app.py` 을 돌려주세요.
    


##  허브 실행기를 사용하기 위해 `jina hello mutlimodal` 수정하세요 

1)  `jina hello fork multimodal <your_project_folder>`로 저장소를 복제하세요. 저장소에서 당신은 
     당신은 다른 메서드를 임베딩 할수있는 파일 `flow-index.yml` and `flow-search.yml`를 가질 것 입니다.
    
2) index flow 와 search flow를 바꿔주세요.
   ````{tab} flow-index.yml
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
   ````
   
   ````{tab} flow-search.yml
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
   ````
3) 실행하기위해 `python <your_project_folder>/app.py`을 돌려주세요 .

