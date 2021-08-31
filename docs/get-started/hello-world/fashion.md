## 👗 Fashion image search

````{sidebar} Fashion Demo

```{figure} ../../.github/images/hello-world.gif
:align: center
:scale: 30%
:target: https://docs.jina.ai/
```
````

A simple image neural search demo for [Fashion-MNIST](https://hanxiao.io/2018/09/28/Fashion-MNIST-Year-In-Review/). No
extra dependencies needed, simply run:

```bash
pip install "jina[demo]"
jina hello fashion  # more options in --help
```

...or even easier for Docker users, **no install required**:

```bash
docker run -v "$(pwd)/j:/j" jinaai/jina hello fashion --workdir /j && open j/hello-world.html
 replace "open" with "xdg-open" on Linux
```

<details>
<summary>Click to see console output</summary>

<p align="center">
  <img src="https://github.com/jina-ai/jina/blob/master/.github/images/hello-world-demo.png?raw=true" alt="hello world console output">
</p>


</details>
This downloads the Fashion-MNIST training and test dataset and tells Jina to index 60,000 images from the training set.
Then it randomly samples images from the test set as queries and asks Jina to retrieve relevant results.
The whole process takes about 1 minute.

<br><br>

#### Use jina hub Executors

You can run the `jina hello fashion` demo using a different embedding method. To do so:

1) Clone the repository with  `jina hello fork fashion <your_project_folder>`. In `your_project_folder` you will
   have a file `app.py`  that you can change to leverage other embedding methods.

2) Change lines 74 to 79 from `app.py` to define a different `Flow`. For example, you can
   use  [ImageTorchEncoder](https://github.com/jina-ai/executor-image-torch-encoder)
   changing

   ```python
   f = (Flow()
      .add(uses=MyEncoder, parallel=2)
      .add(uses=MyIndexer, workspace=args.workdir)
      .add(uses=MyEvaluator)
   )
   ```

   with the flow

   ```python
   f = (
      Flow()
      .add(uses='jinahub+docker://ImageTorchEncoder',
         uses_with={'model_name': 'alexnet'},
         parallel=2)
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
   
3) Run `python <your_project_folder>/app.py` to execute.
    

````{admonition} See Also
:class: seealso

{ref}`JinaHub <hub-cookbook>`
````
