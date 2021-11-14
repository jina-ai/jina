# Run Quick Demos


Just starting out? Try our three well-designed "Hello, World" demos.


:::::{grid} 3
:gutter: 3


::::{grid-item-card} {octicon}`image;1.5em` Fashion image search
:link: fashion
:link-type: doc

Search over 60,000 images based on visual similarity.
+++
`jina hello fashion`
::::

::::{grid-item-card} {octicon}`comment-discussion;1.5em`  QA chatbot
:link: covid-19-chatbot
:link-type: doc

A simple BERT-based chatbot to answer Covid-related questions. 
+++
`jina hello chatbot`
::::


::::{grid-item-card} {octicon}`versions;1.5em` Multimodal search
:link: multimodal
:link-type: doc

Jointly search text and image in one query. 
+++
`jina hello multimodal`
::::

:::::

## Fork one and start building

If you find any hello-world demo interesting, you can simply fork its source code to your own directory via:

```bash
jina hello fork fashion ./myapp
```

You will get something like the following:

```text
           JINA@22299[L]:fashion project is forked to /Users/hanxiao/Documents/jina/myapp
           JINA@22299[I]:
    To run the project:
    ~$ cd /Users/hanxiao/Documents/jina/myapp
    ~$ python app.py
```

Now go to `myapp` folder, modify the code and run it again via `python app.py`. 

## Learn more about each demo

You can always run `jina hello --help` to get more details about each demo. For example:

```bash
jina hello chatbot --help
jina hello fashion --help
jina hello multimodal --help
```

If you prefer to learn by watching a video, watch [this video explanation](https://www.youtube.com/watch?v=zQqbXFY0Nco) by Jina community member Aleksa Gordic.


```{toctree}
:hidden:

fashion
covid-19-chatbot
multimodal
```
