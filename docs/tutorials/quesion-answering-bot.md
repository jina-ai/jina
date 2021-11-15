# 문서화를 위한 질의응답 챗봇 

```{article-info}
:avatar: avatars/gregor.jpg
:avatar-link: https://jobs.jina.ai
:avatar-outline: muted
:author: Gregor @ Jina AI
:date: November 3, 2021
```

이 튜토리얼은 질의응답 챗봇을 생성하는 과정을 안내합니다. 이것은 인간 언어의 모호함과 한 사람이 할 수 있는 무한한 질문으로 인해 본질적으로 어려운 작업입니다.

이 문제를 해결하는 한 가지 방법은 한 쌍의 질문과 답변에 대해 훈련된 신경망을 사용하여 답변을 예측하는 것입니다. 대부분의 소프트웨어 문서와 같이 데이터 세트를 사용할 수 없는 경우가 많습니다. Jina 문서에 대한 질문에 답하기 위해 챗봇을 구축하고 싶다고 가정해 보겠습니다. 제가 만약 이 작업을 검색 문제로 재구성할 수 있는 방법이 있고, 이렇게 하면 서로 일치하는 질문과 답변으로 구성된 대규모 데이터 세트의 필요성을 줄일 수 있다고 말하면 어떻게 될까요?

어떻게? 라고 물으신다면 *제가 설명해 드리겠습니다!*

## 개요 
문제에 대한 접근 방법으로는 [Doc2query 방법](https://arxiv.org/pdf/1904.08375.pdf)를 활용합니다. 이 방법은 텍스트를 형성하고, 텍스트가 잠재적으로 대답할 수 있는 다양한 질문을 예측합니다. 예를 들어 `Jina is an open source framework for neural search.` 와 같은 문장이 있다면, 모델은 `What is Jina?` 나 `Is Jina open source?` 와 같은 질문을 예측합니다.

여기서 아이디어는 원본 텍스트 문서의 모든 부분에 대한 몇 가지 질문을 예측하는 것입니다(우리의 경우는 Jina 문서). 그런 다음 인코더를 사용하여 예측된 각 질문에 대한 벡터 표현을 만듭니다. 이러한 표현은 저장되어 텍스트의 본문에 대한 인덱스를 제공합니다. 사용자가 봇에 질문을 던지면, 생성된 질문을 인코딩한 것과 같은 방식으로 인코딩합니다. 이제 인코딩에 대해 유사성 검색을 실행할 수 있습니다. 사용자 쿼리의 인코딩을 색인의 인코딩과 비교하여 일치하는 항목을 찾습니다.

사용자의 쿼리와 가장 유사한 질문을 생성하는 데 사용된 원본 텍스트의 부분을 알고 있으므로 사용자에게 원본 텍스트를 답변으로 반환할 수 있습니다.

이제 당신은 우리가 무엇을 할 것인지에 대한 일반적인 아이디어를 얻었으므로 다음 섹션에서는 Jina에서 `Flow` 를 정의하는 방법을 볼 것입니다.
그런 다음 검색 기반 질의응답 시스템에 필요한 `Executor` 의 구현 방법을 살펴보겠습니다.

## 텍스트 문서 인덱싱하기 
아래에 보이는 것과 같이 우리는 Jina의 문서에서 한 무더기의 문장을 추출하고, `DocumentArray` 에 저장했다고 가정해 봅시다.

```python
example_sentences = [
    "Document is the basic data type that Jina operates with",
    "Executor processes a DocumentArray in-place", 
    ...,
    "Jina uses the concept of a flow to tie different executors together"
]

docs = DocumentArray([Document(content=sentence) for sentence in example_sentences])
```

지난 섹션에서 설명했듯이, 우리는 먼저 `DocumentArray` 의 각 요소에 대한 잠재적인 질문을 예측해야 합니다. 그런 다음 예측된 질문에서 벡터 인코딩을 생성하기 위해 다른 모델을 사용해야 합니다. 마지막으로 이것을 인덱스로 저장합니다. 

이제 우리는 `Flows` 정의를 시작하기에 충분한 정보를 가졌습니다. 

*거두절미하고, 이제 만들어봅시다!*

``` python
indexing_flow = Flow(
# Generate potential questions using doc2query
).add(name="question_transformer", 
      uses=QuestionGenerator, 
      uses_with={"random_seed": 12345}
# Create vector representations for generated questions 
).add(name="text_encoder", 
      uses=TextEncoder, 
      uses_with={"parameters": {"traversal_paths": ["c"]}}
# Store embeddings for all generated questions as index
).add(name="my_indexer", 
      uses=MyIndexer
)

with indexing_flow: 
    # Run the indexing on all extracted sentences
    indexing_flow.post(on="/index", inputs=docs, on_done=print)
```

## 인덱스에 대한 사용자 쿼리 검색

문서 인덱싱을 위한 `Flow` 를 정의했으면 이제 사용자 질의에 대답할 준비가 되었습니다. 수신 쿼리도 인코딩해야 합니다. 이를 위해 생성된 질문을 인코딩하는 데 사용했던 것과 동일한 인코더를 사용합니다. 그런 다음 유사성 검색을 수행하고, 생성된 질문을 검색하여 최종적으로 질문에 답하기 위해 `SimpleIndexer` 가 필요합니다.

검색 flow는 인덱싱 flow보다 훨씬 간단하며 다음과 같습니다: 

``` python
query_flow = Flow(
    # Create vector representations from query
    ).add(name="query_transformer", uses=TextEncoder
    # Search the index for matching generated questions
    ).add(name="query_indexer", uses=MyIndexer)

with query_flow: 
    indexing_flow.post(on="/query", inputs=user_queries, on_done=print)
```

이제 우리는 접근 방식의 전체적인 구조를 보았고, 우리의 `Flows` 를 정의했으며, `Executor` 를 코딩할 수 있습니다.

## 잠재적인 질문을 생성하기 위한 Executor 구축

우리가 구현한 첫 번째 `Executor` 는 `QuestionGenerator` 이다. 이것은 주어진 텍스트가 대답할 수 있는 잠재적인 질문을 예측하는 모델 주변의 wrapper입니다.

그 외에도 입력 텍스트의 제공된 모든 부분을 반복합니다. 각 입력에 대해 잠재적인 질문이 예측된 후에 원본 텍스트와 함께 `chunks` 로 저장됩니다. 

``` python 
class QuestionGenerator(Executor): 

    @requests
    def doc2query(self, docs: DocumentArray, **kwargs):
        """Generates potential questions for each answer"""
        
        # Load pretrained doc2query models
        self._tokenizer = T5Tokenizer.from_pretrained(
            'castorini/doc2query-t5-base-msmarco')
        self._model = T5ForConditionalGeneration.from_pretrained(
            'castorini/doc2query-t5-base-msmarco')

        for d in docs:
            input_ids = self._tokenizer.encode(
                d.content, return_tensors='pt')
            # Generte potential queries for each piece of text
            outputs = self._model.generate(
                input_ids=input_ids,
                max_length=64,
                do_sample=True,
                num_return_sequences=10,
            )
            # Decode the outputs ot text and store them 
            for output in outputs:
                question = self._tokenizer.decode(
                    output, skip_special_tokens=True).strip()
                d.chunks.append(Document(text=question))
```

우리는 합당한 곳에 크레딧을 제공하기 위해 doc2query 접근 방식을 도입한 논문을 [here](https://arxiv.org/pdf/1904.08375.pdf)에서 언급하고자 합니다.

## 인코더 구축
다음 단계는 사람이 읽을 수 있는 텍스트에서 벡터 표현을 만드는 데 사용할 `Executor` 의 구축을 위한 것입니다. 

```python 
class TextEncoder(Executor):

    def __init__(self): 
        self.model = SentenceTransformer(
            'paraphrase-mpnet-base-v2', device="cpu", cache_folder=".")

    @requests(on=['/search', '/index'])
    def encode(self, docs: DocumentArray, 
               traversal_paths: Tuple[str] = ('r',), **kwargs):
        """Wraps encoder from sentence-transformers package"""   
        target = docs.traverse_flat(traversal_paths)
 
        with torch.inference_mode():
            embeddings = self.model.encode(target.texts)
            target.embeddings = embeddings
```
`QuestionGenerator` 와 유사하게 `TextEncoder` 는 단순히 sentence_transformer 패키지의 SentenceTransformer를 감싸는 wrapper입니다.텍스트가 포함된 `DocumentArray` 가 제공되면, 이것은 각 요소의 텍스트를 인코딩하고 `embedding` 속성에 결과를 저장합니다. 

이제 마지막 부분으로 이동하여 인덱서를 생성해 보겠습니다.

## 인덱서와 함께 사용하기

인덱서는 우리의 `Executor` 중 하나 이상의 작업을 처리할 수 있는 유일한 것입니다. 즉, 인덱싱 및 검색입니다.

인덱싱을 수행할 때 `index()` 가 호출됩니다. 이것은 제공된 모든 문서와 그것의 임베딩을 `DocumentArrayMemmap`으로 저장합니다.

그러나 `SimpleIndexer` 가 들어오는 쿼리를 처리하기 위해 사용될 때 `search()` 함수가 호출되고, SimpleIndexer는 유사성을 검색하고 결과의 순위를 지정합니다.

```python 
class SimpleIndexer(Executor):
    """Simple indexer class"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._docs = DocumentArrayMemmap(".")

    @requests(on='/index')
    def index(self, docs: 'DocumentArray', **kwargs):
        # Stores the index in attribute
        if docs:
            self._docs.extend(docs)

    @requests(on='/search')
    def search(self, docs: 'DocumentArray', **kwargs):
        """Append best matches to each document in docs"""

        # Match query agains the index using cosine similarity
        docs.match(
            DocumentArray(self._docs),
            metric='cosine',
            normalization=(1, 0),
            limit=100,
            traversal_rdarray=['c'],
        )

        for d in docs:
            match_similarity = defaultdict(float)
            # For each match 
            for m in d.matches:
                # Get cosine similarity
                match_similarity[m.parent_id] = m.scores['cosine'].value

            sorted_similarities = sorted(
                match_similarity.items(), key=lambda v: v[1], reverse=True)
            
            # Rank the matches by similarity
            for k, v in sorted_similarities:
                m = Document(self._docs[k], copy=True)
                d.matches.append(m)
                if len(d.matches) >= 10:
                    break
            d.pop('embedding')
```

결과의 순위는 `matches` 객체 안의 일치 순서로 표시됩니다. 따라서 사용자에게 답변을 제공하기 위해, 가장 적합한 일치의 `id` 를 가져오고 이 `id` 를 가진 문장의 인덱스를 검색하는 작은 도우미 함수를 사용할 수 있습니다.

```python 
best_matching_id = user_queries[0].matches[0].id

def get_answer(docs, best_matching_id): 
    """Get the answer for most similar question"""
    ret = None
    for doc in docs:
        # Search all questions for each sentence
        for c in doc.chunks: 
            # Get the question that fits best
            if c.id == best_matching_id:   
                # Return the answer to best fitting question
                ret = doc.text
    return ret
# Prints the answer text to our question
print(get_answer(docs, best_matching_id))
```

이제 우리는 Jina를 사용하여 서로 일치하는 질문과 답변으로 구성된 대규모 데이터 세트 없이 질의응답 봇을 구현하는 방법을 보았습니다. 실제로 우리는 원본 텍스트에서 답변을 초기 추출하는 것과 같이 여러 매개변수를 실험해 보아야 합니다. 이 튜토리얼에서는 모든 문장이 하나의 잠재적인 답변이 될 것이라고 가정했습니다. 그러나 실제로는 일부 사용자 쿼리는 응답하기 위해 여러 문장이나 완전한 단락이 필요할 수 있습니다.
