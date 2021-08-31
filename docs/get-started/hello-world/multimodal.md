# Multimodal document search

<a href="https://youtu.be/B_nH8GCmBfc">
<img align="right" width="25%" src="https://github.com/jina-ai/jina/blob/master/.github/images/helloworld-multimodal.gif?raw=true" />
</a>

A multimodal-document contains multiple data types, e.g. a PDF document often contains figures and text. Jina lets you
build a multimodal search solution in just minutes. To run our minimum multimodal document search demo:

```bash
pip install "jina[demo]"

jina hello multimodal
```

This downloads [people image dataset](https://www.kaggle.com/ahmadahmadzada/images2000) and tells Jina to index 2,000
image-caption pairs with MobileNet and MPNet. The index process takes about 3 minute on CPU. Then it opens a web page
where you can query multimodal documents. We have prepared [a YouTube tutorial](https://youtu.be/B_nH8GCmBfc) to walk
you through this demo.

