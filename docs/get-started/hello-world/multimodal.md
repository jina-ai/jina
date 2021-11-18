# Multimodal search

```{tip}
We have a [Youtube video](https://youtu.be/B_nH8GCmBfc) explaining this demo in detail. 
```

````{important}
This demo requires extra dependencies. Please install them via:

```bash
pip install "jina[demo]"
```

````

A multimodal-document contains multiple data types, e.g. a PDF document often contains figures and text. Jina lets you
build a multimodal search solution in just minutes. To run our minimum multimodal document search demo:

```bash
jina hello multimodal
```


```{figure} ../../../.github/2.0/hello-multimodal-1.png
:align: center
```

This downloads the [people image dataset](https://www.kaggle.com/ahmadahmadzada/images2000) and tells Jina to index 2,000
image-caption pairs with MobileNet and MPNet. The indexing process takes about three minutes on CPU. Then it opens a web page
where you can query multimodal documents. We have prepared [a YouTube tutorial](https://youtu.be/B_nH8GCmBfc) to walk
you through this demo.


```{figure} ../../../.github/2.0/hello-multimodal-2.png
:align: center
```
