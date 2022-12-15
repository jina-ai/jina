# Fashion image search

A simple image neural search demo for [Fashion-MNIST](https://hanxiao.io/2018/09/28/Fashion-MNIST-Year-In-Review/). No
extra dependencies needed, simply run:

```bash
jina hello fashion
```

````{tip}
...or even easier for Docker users, **no install required**:

```bash
docker run -v "$(pwd)/j:/j" jinaai/jina hello fashion --workdir /j && open j/hello-world.html
 replace "open" with "xdg-open" on Linux
```

````

```{figure} ../../../.github/2.0/hello-fashion-1.png
:align: center
```

This downloads the Fashion-MNIST training and test dataset and tells Jina to index 60,000 images from the training set.
Then it randomly samples images from the test set as queries and asks Jina to retrieve relevant results.
The whole process takes about 1 minute.

```{figure} ../../../.github/2.0/hello-fashion-2.png
:align: center
```