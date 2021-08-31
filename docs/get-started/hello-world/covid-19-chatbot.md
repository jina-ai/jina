# Covid-19 chatbot

For NLP engineers, we provide a simple chatbot demo for answering Covid-19 questions. To run that:

```bash
pip install "jina[demo]"

jina hello chatbot
```

```{figure} ../../../.github/2.0/hello-chatbot-1.png
:align: center
```

This downloads [CovidQA dataset](https://www.kaggle.com/xhlulu/covidqa) and tells Jina to index 418 question-answer
pairs with MPNet. The index process takes about 1 minute on CPU. Then it opens a web page where you can input questions
and ask Jina.

```{figure} ../../../.github/2.0/hello-chatbot-2.png
:align: center
```