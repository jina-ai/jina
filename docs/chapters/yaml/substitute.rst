Variable Substitution in YAML
=============================

In the YAML config, one can reference environment variables with ``$ENV``, or using ``{path.variable}`` to reference the variable defined inside the YAML. For example,

.. highlight:: yaml
.. code-block:: yaml

    components:
      - with:
          index_filename: metaproto
        metas:
          name: test_meta
          good_var:
            - 1
            - 2
          bad_var: ${{root.metas.name}}
      - with:
          index_filename: npidx
        metas:
          name: test_numpy
          bad_var: ${{root.components[0].metas.good_var[1]}}
          float_var: ${{root.float.val}}
          mixed: ${{root.float.val}}-${{root.components[0].metas.good_var[1]}}-${{root.metas.name}}
          mixed_env: ${{root.float.val}}-${{ ENV.ENV1 }}
          name_shortcut: ${{this.name}}
          random_id: ${{ context_var }}
          config_str: ${{ context_var2 }}
    metas:
      name: real-compound
    rootvar: 123
    float:
      val: 0.232

.. confval:: ${{ var }}

    The variable will be evaluated when calling :meth:`Flow.load_config`, :meth:`BaseExecutor.load_config`, :meth:`BaseDriver.load_config`, :meth:`JAML.load`. For example,

        .. highlight:: yaml
        .. code-block:: yaml

            !Flow
            with:
                name: ${{ context_var2 }}
                timeout_ready: ${{ context_var }}


        .. highlight:: python
        .. code-block:: python

            obj = Flow.load_config('my.yml',
                                    context={'context_var': 50,
                                            'context_var2': 'hello-world'})

.. confval:: ${{ root.var }}

    Referring to the top-level variable defined in the root named ``var``.

.. confval:: ${{ this.var }}

    Referring to the same-level variable named ``var``.

.. confval:: ${{ ENV.var }}

    Referring to the OS environment variable.

.. note::
    One must quote the string when using referenced values, i.e. ``'${{root.metas.name}}'`` but not ``{root.metas.name}``.
