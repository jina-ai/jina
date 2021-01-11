Jina YAML Syntax Reference
==========================

Jina configurations use YAML syntax, and must have either a ``.yml`` or ``.yaml`` file extension. If you're new to YAML and want to learn more, see `Learn YAML in five minutes. <https://www.codeproject.com/Articles/1214409/Learn-YAML-in-five-minutes>`_

.. note::
    In many Jina YAML config files, you often see ``!Tag`` such as ``!Flow``, ``!MyEncoder``. Note that ``!Tag`` is valid YAML 1.0 syntax, it represents a language-specific serialization and object, e.g. ``!ruby/symbol``, ``!python/list``. Tags such as ``!Flow`` have been registered inside the Jina YAML parser, and therefore they are readable. However, if you copy-paste this YAML file into an arbitrary online YAML validator, it will most likely report it as **invalid**. The reason is that those tags aren't registered at those online YAML validator.

.. toctree::

   flow
   executor
   compound-executor
   driver
   substitute