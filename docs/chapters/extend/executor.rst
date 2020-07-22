Guideline When Adding New Executor
==================================

New deep learning model? New indexing algorithm? When the existing executors/drivers do not fit your requirement, and you can not find a useful one from `Jina Hub <https://hub.jina.ai>`_, you can simply extend Jina to what you need without even touching the Jina codebase.

In this chapter, we will show you the guideline of making an extension for a :class:`jina.executors.BaseExecutor`. Generally speaking, the steps are the following:

#. Decide which :class:`Executor` class to inherit from;
#. Override :meth:`__init__` and :meth:`post_init`;
#. Override the *core* method of the base class;
#. (Optional) implement the save logic.


Decide which :class:`Executor` class to inherit from
----------------------------------------------------

The list of executors supported by the current Jina can be found `here <https://docs.jina.ai/chapters/all_exec.html>`_. As one can see, all executors are inherited from :class:`jina.executors.BaseExecutor`. So do you want to inherit directly from :class:`BaseExecutor` for your extension as well? In general you don't. Rule of thumb, you always pick the executor that shares the similar logic to inherit.

If your algorithm is so unique and does not fit any any of the category below, you may want to `submit an issue for discussion <https://github.com/jina-ai/jina/issues/new>`_ before you start.

.. note:: Inherit from class ``X`` when ...

    * :class:`jina.executors.encoders.BaseEncoder`

      You want to represent the chunks as vector embeddings.

      * :class:`jina.executors.encoders.BaseNumericEncoder`

        You want to represent numpy array object (e.g. image, video, audio) as vector embeddings.

      * :class:`jina.executors.encoders.BaseTextEncoder`

        You want to represent string object as vector embeddings.

    * :class:`jina.executors.indexers.BaseIndexer`

      You want to save and retrieve vectors and key-value information from storage.

      * :class:`jina.executors.indexers.BaseVectorIndexer`

        You want to save and retrieve vectors from storage.

        * :class:`jina.executors.indexers.NumpyIndexer`

          You vector-indexer uses a simple numpy array for storage, you only want to specify the query logic.

      * :class:`jina.executors.indexers.BaseKVIndexer`

        You want to save and retrieve key-value pair from storage.

    * :class:`jina.executors.craters.BaseCrafter`

      You want to segment/transform the documents and chunks.

      * :class:`jina.executors.craters.BaseDocCrafter`

        You want to transform the documents by modifying some fields.

        * :class:`jina.executors.craters.BaseChunkCrafter`

          You want to transform the chunks by modifying some fields.

        * :class:`jina.executors.craters.BaseSegmenter`

          You want to segment the documents into chunks.

    * :class:`jina.executors.Chunk2DocRanker`

      You want to segment/transform the documents and chunks.

    * :class:`jina.executors.CompoundExecutor`

      You want to combine multiple executors in one.

Override :meth:`__init__` and :meth:`post_init`
------------------------------------------------

Override :meth:`__init__`
^^^^^^^^^^^^^^^^^^^^^^^^^

You can put simple type attributes that define the behavior of your ``Executor`` into :meth:`__init__`. Simple types represent all `pickle`-able types, including: integer, bool, string, tuple of simple types, list of simple types, map of simple type. For example,

.. highlight:: python
.. code-block:: python

  from jina.executors.crafters import BaseSegmenter

  class GifPreprocessor(BaseSegmenter):
    def __init__(self, img_shape: int = 96, every_k_frame: int = 1, max_frame: int = None, from_bytes: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.img_shape = img_shape
        self.every_k_frame = every_k_frame
        self.max_frame = max_frame
        self.from_bytes = from_bytes

Remember to add ``super().__init__(*args, **kwargs)`` to your :meth:`__init__`. Only in this way you can enjoy many magic features, e.g. YAML support, persistence from the base class (and :class:`BaseExecutor`).


.. note::

    All attributes declared in :meth:`__init__` will be persisted during :meth:`save`  and :meth:`load`.


Override :meth:`post_init`
^^^^^^^^^^^^^^^^^^^^^^^^^^

So what if the data you need to load is not in simple type. For example, a deep learning graph, a big pretrained model, a gRPC stub, a tensorflow session, a thread? The you can put them into :meth:`post_init`.

Another scenario is when you know there is a better persistence method other than ``pickle``. For example, your hyperparameters matrix in numpy ``ndarray`` is certainly pickable. However, one can simply read and write it via standard file IO, and it is likely more efficient than ``pickle``. In this case, you do the data loading in :meth:`post_init`.

Here is a good example.


.. highlight:: python
.. code-block:: python

    from jina.executors.encoders import BaseTextEncoder

    class TextPaddlehubEncoder(BaseTextEncoder):

        def __init__(self,
                     model_name: str = 'ernie_tiny',
                     max_length: int = 128,
                     *args,
                     **kwargs):
            super().__init__(*args, **kwargs)
            self.model_name = model_name
            self.max_length = max_length


        def post_init(self):
            import paddlehub as hub
            self.model = hub.Module(name=self.model_name)
            self.model.MAX_SEQ_LEN = self.max_length


.. note::

    :meth:`post_init` is also a good place to introduce package dependency, e.g. ``import x`` or ``from x import y``. Naively, one can always put all imports upfront at the top of the file. However, this will throw an ``ModuleNotFound`` exception when this package is not installed locally. Sometimes it may break the whole system because of this one missing dependency.

    Rule of thumb, only import packages where you really need them. Often these dependencies are only required in :meth:`post_init` and the core method, which we shall see later.

Override the *core* method of the base class
--------------------------------------------

Each :class:`Executor` has a core method, which defines the algorithmic behavior of the :class:`Executor`. For making your own extension, you have to override the core method. The following table lists the core method you may want to override. Note some executors may have multiple core methods.


+----------------------+----------------------------+
|      Base class      |       Core method(s)       |
+----------------------+----------------------------+
| :class:`BaseEncoder` |       :meth:`encode`       |
+----------------------+----------------------------+
| :class:`BaseCrafter` | :meth:`craft`              |
+----------------------+----------------------------+
| :class:`BaseIndexer` | :meth:`add`, :meth:`query` |
+----------------------+----------------------------+
| :class:`BaseRanker`  | :meth:`score`              |
+----------------------+----------------------------+


Feel free to override other methods/properties as you need. But frankly, most of the extension can be done by simply overriding the core methods listed above. Nothing more. You can read the source code of our executors for details.


Implement the persistence logic
-------------------------------

If you don't override :meth:`post_init`, then you don't need to implement persistence logic. You get YAML and persistency support off-the-shelf because of :class:`BaseExecutor`. Simple crafters and rankers fall into this category.

If you override :meth:`post_init` but you don't care about persisting its state in the next run (when the executor process is restarted); or the state is simply unchanged during the run, then you don't need to implement persistence logic. Loading from a fixed pretrained deep learning model falls into this category.

Persistence logic is only required **when you implement customized loading logic in :meth:`post_init` and the state is changed during the run**. Then you need to override :meth:`__getstate__`. Many of the indexers fall into this category.


In the example below, the ``tokenizer`` is loaded in :meth:`post_init` and saved in :meth:`__getstate__`, whcih completes the persistency cycle.

.. highlight:: python
.. code-block:: python

    class CustomizedEncoder(BaseEncoder):

        def post_init(self):
            self.tokenizer = tokenizer_dict[self.model_name].from_pretrained(self._tmp_model_path)
            self.tokenizer.padding_side = 'right'

        def __getstate__(self):
            self.tokenizer.save_pretrained(self.model_abspath)
            return super().__getstate__()


How Can I Use My Extension
--------------------------

You can use the extension by specifying ``py_modules`` in the YAML file. For example, your extension Python file is called ``my_encoder.py``, which describes :class:`MyEncoder`. Then you can define a YAML file (say ``my.yml``) as follows:

.. highlight:: yaml
.. code-block:: yaml

    !MyEncoder
    with:
      greetings: hello im external encoder
    metas:
      py_modules: my_encoder.py

.. note::

    You can also assign a list of files to ``metas.py_modules`` if your Python logic is splitted over multiple files. This YAML file and all Python extension files should be put under the same directory.

Then simply use it in Jina CLI by specifying ``jina pod --uses=my.yml``, or ``Flow().add(uses='my.yml')`` in Flow API.


.. warning::

    If you use customized executor inside a :class:`jina.executors.CompoundExecutor`, then you only need to set ``metas.py_modules`` at the root level, not at the sub-component level.


I Want to Contribute it to Jina
-------------------------------

We are really glad to hear that! We have done quite some effort to help you contribute and share your extensions with others.

You can easily pack your extension and share it with others via Docker image. For more information, please check out `Jina Hub <https://hub.jina.ai>`_. Just make a pull request there and our CICD system will take care of building, testing and uploading.


