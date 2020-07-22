*************************
Jina "Hello, World!" 👋🌍
*************************

As a starter, we invite you to try Jina's "Hello, World" - a simple demo of image neural search for [Fashion-MNIST](https://hanxiao.io/2018/09/28/Fashion-MNIST-Year-In-Review/). No extra dependencies needed, simply do:

.. highlight:: bash
.. code-block:: bash

    jina hello-world


...or even easier for Docker users, *no any install required*, simply:


.. highlight:: bash
.. code-block:: bash

    docker run -v "$(pwd)/j:/j" jinaai/jina:devel hello-world --workdir /j --logserver && open j/hello-world.html


.. image:: hello-world-demo.png
   :width: 70%
   :align: center


It downloads Fashion-MNIST training and test data and tells Jina to *index* 60,000 images from the training set. Then, it randomly samples images from the test set as *queries*, asks Jina to retrieve relevant results. After about 1 minute, it will open a webpage and show results like this:


.. image:: hello-world.gif
   :width: 70%
   :align: center

And the implementation behind? As simple as it should be:

.. confval:: Python API

    .. highlight:: python
    .. code-block:: python

        from jina.flow import Flow

        f = Flow.load_config('index.yml')

        with f:
            f.index(input_fn)

.. confval:: YAML spec

    .. highlight:: yaml
    .. code-block:: yaml

        !Flow
        pods:
          chunk_seg:
            uses: helloworld.crafter.yml
            replicas: $REPLICAS
            read_only: true
          doc_idx:
            uses: helloworld.indexer.doc.yml
          encode:
            uses: helloworld.encoder.yml
            needs: chunk_seg
            replicas: $REPLICAS
          chunk_idx:
            uses: helloworld.indexer.chunk.yml
            replicas: $SHARDS
            separated_workspace: true
          join_all:
            uses: _merge
            needs: [doc_idx, chunk_idx]
            read_only: true

.. confval:: Flow in Dashboard

    .. image:: hello-world-flow.png
       :align: center

All big words you can name: computer vision, neural IR, microservice, message queue, elastic, replicas & shards happened in just one minute!

View "Hello World" in Jina Dashboard
====================================


.. highlight:: bash
.. code-block:: bash

    pip install "jina[sse]"

    jina hello-world --logserver


or if you use Docker:



.. highlight:: bash
.. code-block:: bash


    docker run -p 5000:5000 -v $(pwd)/tmp:/workspace jinaai/jina:devel hello-world --workdir /workspace --logserver && open tmp/hello-world.html



More Options on "Hello, World"
==============================

Intrigued? Play with different options via:


.. highlight:: bash
.. code-block:: bash

    jina hello-world --help



.. argparse::
   :noepilog:
   :ref: jina.main.parser.get_main_parser
   :prog: jina
   :path: hello-world



