# Use Hub Executors in Hello World

```{article-info}
:avatar: avatars/david.jpg
:avatar-link: https://jobs.jina.ai
:avatar-outline: muted
:author: David @ Jina AI
:date: Aug. 10, 2021
```


이제 허브에서 퍼블릭 Executor를 사용하는 방법을 이해하셨으니 지나에서 세 가지 헬로월드 데모를 통해 학습 방법을 연습해 보겠습니다.



## Hub 실행기를 사용하기위해 '지나 헬로 패션' 을 수정하세요



1) 저장소를 복제하세요  `jina hello fork fashion <your_project_folder>`.  `your_project_folder`에서 다른 임베딩 방식을 활용하기 위해 변경할 수 있는 파일 app.py을 갖게 됩니다.

2) 74~79줄을 바꿔주세요. 예를들어 당신은  [ImageTorchEncoder](https://github.com/jina-ai/executor-image-torch-encoder):을 사용할 수있습니다

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
   
3)  `python <your_project_folder>/app.py` 를  .

## Hub 실행기를 사용하기위해 '지나 헬로 패션' 을 수정하세요


As an example, you can
use [TransformerTorchEncoder](https://github.com/jina-ai/executor-transformer-torch-encoder). To do so:

1) Clone the repository with  `jina hello fork chatbot <your_project_folder>`. In the repository you will
   have `app.py`  which you can change to leverage other embedding methods.

2) Change lines 21 to 25 from `app.py` to define a different `Flow`. Change it to:
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

3) Run `python <your_project_folder>/app.py` to execute.
    


## Hub 실행기를 사용하기위해 '지나 헬로 패션' 을 수정하세요

1) '지나 헬로 포크 멀티모달 <your_project_folder>를 사용하여 저장소 복제 리포지토리에서 다음 작업을 수행합니다.
'flow-index.yml' 및 'flow-search.yml'을 가지고 있으며, 이 경우 다른 임베디를 활용하도록 변경할 수 있습니다.
    
2) 그에 따라 인덱스 흐름 및 검색 정보를 수정하세요.
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
3) 실행할 'deloping <your_project_folder>/app.py'을 실행합니다.
