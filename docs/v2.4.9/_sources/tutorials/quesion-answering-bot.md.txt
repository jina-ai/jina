# Question-Answering Chatbot for Documentation 

```{article-info}
:avatar: avatars/gregor.jpg
:avatar-link: https://jobs.jina.ai
:avatar-outline: muted
:author: Gregor @ Jina AI
:date: November 3, 2021
```

This tutorial will take you through the process of creating a question-answering chatbot. 
This is an inherently difficult task, due to the fuzziness of human language and the infinite number of questions one could ask.

One way to solve this is by predicting answers using a neural network that was trained on pairs of questions and their corresponding answers. In many cases such a dataset is not available, like in the case of most software documentation. Let's say we want to build a chatbot to answer questions about the Jina documentation. What if I told you that there is a way to reframe this task as a search problem and that this would alleviate the need for a large dataset of matching questions and answers?

How, you ask? *Let me explain!*

## Overview 
Our approach to the problem leverages the [Doc2query method](https://arxiv.org/pdf/1904.08375.pdf), which, form a piece of text, predicts different questions the text could potentially answer. For example, given a sentence such as `Jina is an open source framework for neural search.`, the model predicts questions such as `What is Jina?` or `Is Jina open source?`.

The idea here is to predict several questions for every part of the original text document, in our case the Jina documentation. Then we use an encoder to create a vector representation for each of the predicted questions. These representations are stored and provide the index for our body of text. When a user prompts the bot with a question, we encode it in the same way we encoded our generated questions. Now we can run a similarity search on the encodings. The encoding of the user's query is compared with the encodings in our index to find the closes match.

Since we know what part of the original text was used to generate the question, that was most similar to the user's query, we can return the original text as an answer to the user.

Now that you have a general idea of what we will be doing, the following section will show you how to define our `Flow`s in Jina. Then we will take a look at how to implement the necessary `Executor`s for our search-based question-answering system.  

## Indexing the text document 
Let's imagine we extracted a bunch of sentences from Jina's documentation and stored them in a `DocumentArray`, as shown below. 

```python
example_sentences = [
    "Document is the basic data type that Jina operates with",
    "Executor processes a DocumentArray in-place", 
    ...,
    "Jina uses the concept of a flow to tie different executors together"
]

docs = DocumentArray([Document(content=sentence) for sentence in example_sentences])
```

As described in the last section, we first need to predict potential questions for each of the elements in the `DocumentArray`. Then we have to use another model to create vector encodings from the predicted questions. Finally, we store them as the index. 

At this point we have enough information to start defining our `Flows`.

*Without further ado, let's build!*

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

## Searching of the user's query against the index

After having defined the `Flow` for indexing our document, we are now ready to work on answering user queries. Incoming queries also need to be encoded. For that, we use the same encoder that we used for encoding our generated questions. Then we need `SimpleIndexer` to perform similarity search, in order to retrieve generated questions and eventually answers the query. 

The flow for searching is much simpler than the one for indexing and looks like this: 

``` python
query_flow = Flow(
    # Create vector representations from query
    ).add(name="query_transformer", uses=TextEncoder
    # Search the index for matching generated questions
    ).add(name="query_indexer", uses=MyIndexer)

with query_flow: 
    indexing_flow.post(on="/query", inputs=user_queries, on_done=print)
```

Now that we have seen the overall structure of the approach and have defined our `Flows`, we can code up the `Executor`s.

## Building the Executor to Generate Potential Questions 

The first `Executor`, thatÏ we implement, is the `QuestionGenerator`. It is a wrapper around the model that predicts potential questions, which a given piece of text can answer.

Apart from that, it just loops over all provided parts of input text. After potential questions are predicted for each of the inputs, they are stored as `chunks` alongside the original text. 

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

We try to give credit where credit is due and want to mention the paper, that introduced the doc2query approach [here](https://arxiv.org/pdf/1904.08375.pdf).

## Building the Encoder
The next step is to build the `Executor`, which we will use to create vector representations from human-readable text. 

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
Similar to the `QuestionGenerator` the `TextEncoder` is simply a wrapper around the SentenceTransformer from the sentence_transformer package. When provided with a `DocumentArray` containing text, it will encode the text of each element and store the result in the `embedding` attribute it creates.

Now let's move on to the last part and create the indexer. 

## Putting it Together with the Indexer
The indexer is the only one of our `Executor`s that can handle more than one task. 
Namely, the indexing and the search.

When it is used to perform indexing, `index()` is called. This stores all provided documents, together with their embeddings, as a `DocumentArrayMemmap`. 

However, when the `SimpleIndexer` is used to handle an incoming query, the `search()` function is called, it performs similarity search and ranks the results. 


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

The ranking of the results is thereby represented in the order of the matches inside the `matches` object. Hence, to provide the answer to the user, we could use a little helper function that gets the `id` of the best-fitting match and searches the index for the sentence with this `id`. 

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

We have now seen how to implement a question-answering bot using Jina without the need for a large dataset of matching questions and answers. In practice, we would need to experiment with several parameters, such as the initial extraction of answers from the original text. In this tutorial, we made the assumption that every sentence will be one potential answer. However, in reality, it is likely that some user queries will require multiple sentences or complete paragraphs to answer.
