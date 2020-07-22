A Minimum Working Example
=========================

This dummy encoder embeds everything to a 3-dimensional vector. You only need two files:

.. highlight:: python
.. code-block:: python
   :caption: mwu.py

    import numpy as np

    from jina.executors.encoders import BaseEncoder


    class MWUEncoder(BaseEncoder):

        def __init__(self, greetings: str, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._greetings = greetings

        def encode(self, data: Any, *args, **kwargs):
            self.logger.info('%s %s' % (self._greetings, data))
            return np.random.random([data.shape[0], 3])

And,

.. highlight:: yaml
.. code-block:: yaml
   :caption: mwu.yml

    !MWUEncoder
    with:
      greetings: hello there!
    metas:
      name: my-mwu-encoder
      py_modules: mwu.py
      workspace: ./


To use that in Flow API,

.. highlight:: python
.. code-block:: python

    from jina.flow import Flow

    f = (Flow()
        .add(name='dummyEncoder', uses='mwu.yml'))

    # test it with dry run
    with f:
        f.dry_run()

You can also use it as a Pod image, please refer `Jina Hub <https://github.com/jina-ai/jina-hub/>`_ for details.