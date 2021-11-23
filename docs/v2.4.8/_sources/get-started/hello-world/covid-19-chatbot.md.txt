(chatbot-helloworld)=
# Covid-19 chatbot

````{important}
This demo requires extra dependencies. Please install them via:

```bash
pip install "jina[demo]"
```

````

For NLP engineers, we provide a simple chatbot demo for answering Covid-19 questions. To run that:

```bash
jina hello chatbot
```

```{figure} ../../../.github/2.0/hello-chatbot-1.png
:align: center
```

This downloads the [CovidQA dataset](https://www.kaggle.com/xhlulu/covidqa) and tells Jina to index 418 question-answer
pairs with MPNet. The indexing process takes about one minute on CPU. Then it opens a web page where you can input questions
and ask Jina.

```{figure} ../../../.github/2.0/hello-chatbot-2.png
:align: center
```
