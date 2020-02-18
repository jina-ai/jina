FAQ for Developers
------------------

#. What coding style are you using?

    We follow :pep:`8` coding style with type-hint. We use `flake8` to do the lint.

#. What is difference between :file:`extra-requirements.txt` and :file:`requirements.txt`, should I add new dependency to :file:`requirements.txt`?

    Jina only requires very few dependencies as described in :file:`setup.py`. Please keep the content empty (with a `.`) in :file:`requirements.txt`, so that ``pip`` won't be confused when installing the dependencies.

    :file:`extra-requirements.txt` is the executor-specific dependency which Jina does not require but some certain executor may do. They are collected here so that one can cherry pick the dependencies via :command:`pip install jina[xyz]`.

    More information about this trick can be `found in this blog post <https://hanxiao.io/2019/11/07/A-Better-Practice-for-Managing-extras-require-Dependencies-in-Python>`_ .