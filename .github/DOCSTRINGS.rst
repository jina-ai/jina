==================================
Docstring Guide
==================================

    “Code is more often read than written.”

    — Guido van Rossum


In Jina, we are aware that documentation is an important part of software, but we also think it is especially important for OpenSource. And for this reason, we try extra hard to have clear and extensive documentation for all of our source code. But, at the same time, we know this also takes time and effort, so we want to make things as easy as possible with this guide for you. In Jina we use the `Sphinx style <https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html>`_ and here are the guidelines you should follow:


What are docstrings?
----------------------------------------------------

First, we should define what are we talking about. A docstring is a string literal that we use to document elements of our code, such as functions, methods, modules, and classes. We do this to have a clear understanding about what are the details of each part of our code. We can see it more in detail in `PEP 257 <https://www.python.org/dev/peps/pep-0257/>`_. Jina recommends the following:

* Write docstrings for **public** *functions* and *classes*
* Optionally you can write docstrings for **private** *functions* and *classes*, but it's not mandatory

In Jina, we use **ReStructuredText** (`reST <https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html>`_), which is the default markup language used by `Sphinx <https://www.sphinx-doc.org/>`_. You can use *Markdown* too but we encourage you to use reST since *Markdown* doesn't contain rich markup.


One-line Docstrings
----------------------------------------------------

Use one-line docstrings when the description of the class/module/function fits in one line

We suggest the following guidelines:

* Define the Docstrings with triple-double quotes (""")
* Don't leave blank lines before your Docstring
* Start your text right after the triple-double quotes
* Write the Docstring as a command, not as a description (*Start Flow* instead of *This will start a flow*)


*****************************************************
One-line Docstrings Example
*****************************************************

.. highlight:: python
.. code-block:: python

    def does_magic():
        """Do magic"""
        print('Magic happens here')


Multi-line Docstrings
----------------------------------------------------

We use multi-line docstring for more complex functions or classes. And we suggest the following:

* Define the Docstrings with triple-double quotes (""")
* Don't leave blank lines before your Docstring
* Write the Docstring as a command, not as a description (*Start Flow* instead of *This will start a flow*). We should have a more detailed description here as compared to the one-line docstrings
* Use the same indentation line as with the triple-double quotes
* Leave a blank line after the docstring and before the rest of the function/class/method


Commonly used directives
----------------------------------------------------

You can use all the `Sphinx directives <https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html>`_. And here is an example of the most used ones:

* *.. note::* [description]
* *.. warning::* [description]
* *.. deprecated::* [version]
* *.. seealso::* [description]
* *.. highlight::* [language]
* *.. code-block::* [language] [description]
* *.. math::* [latex markup]


Deprecation warning
----------------------------------------------------

You should warn the user if an object (class, function, method) is deprecated.

* Specify in which version the object has been deprecated.
* Specify when this will be removed
* Recommend a proposed way to do it

To show this warning you can do it with the  *.. deprecated::* directive

Commonly used python field directives
----------------------------------------------------

This are the most common python field directives:

* Parameters:
    - *:param [ParamName]:* [ParamDescription]
    - *:type [ParamName]:* [ParamType](, optional)
* Return:
    - *:return:* [ReturnDescription]
    - *:rtype:* [ReturnType]
* Raises:
    - *:raises:* [ExceptionType]
* Deprecation
    - *.. deprecated::* version

You should warn the user if an object (class, function, method) has been deprecated.

* Specify in which version the object has been deprecated.
* Specify when this will be removed
* Recommend a proposed way to do it


Commonly used directives for cross-referencing
----------------------------------------------------

You can use the following for cross-referencing

* For classes: *:class:* [ClassName]
* For methods: *:meth:* [MethodName]
* For attributes: *:attr:* [AttributeName]
* For exceptions: *:exc:* [ExceptionName]
* For data: *:data:* [ModuleLevelVariable]


Use terms from a glossary
----------------------------------------------------

You can reference a term that is defined in the Glossary. You can do it like this:

*:term:* ` Magic`

You need to match exactly the term as in the Glossary. If you want to show different text in the topic, you can do it by including the term in angle brackets. You can do it like this:

*:term:* ` Another type of Magic <Magic>`


Documenting classes
----------------------------------------------------

In classes you don't need to specify a return type. But you should document the constructor parameters here. Use all parameters that are under **__init__** and document them in the class itself. Do not add any docstring to the **__init__** method.

*****************************************************
Multi-line docstrings example of a function
*****************************************************

.. highlight:: python
.. code-block:: python

    def does_complex_magic(param1: Document, param2: str):
        """
        Do complex magic

        .. note::
            This is an example note
        .. warning::
            This is a warning example
        .. highlight:: python
        .. code-block:: python
            print('This is a print example')

        :param param1: This is an example of a param1
        :type param1: :class:`Document`
        :param param2: This is an example of a param2
        :type param2: int
        :return: This is an example of what will be returned
        :rytpe: int
        :raises KeyError: raises an exception
        """

*****************************************************
Multi-line docstrings example of a class
*****************************************************

.. highlight:: python
.. code-block:: python

    class Magic:
        """
        :class:`Magic` is one of an example class

        It offers super cool enchanted elements
        You can specify how to create an object of this class, for example:

        To create a :class:`Magic` object, simply:

            .. highlight:: python
            .. code-block:: python
                magic_cat = Magic()

        :param param1: This is an example of a param1
        :type param1: int
        :param param2: This is an example of a param2
        :type param2: str
        """

        def __init__(self, param1: int, param2: str):
            # don't add anything to the constructor


Special Cases
----------------------------------------------------

*****************************************************
Dunder/Magic methods
*****************************************************

You don't have to document dunder/magic methods unless you change the semantic of the method.

*****************************************************
Property
*****************************************************

Sphinx ignores docstrings on property setters so all documentation for a property must be on the @property method.
Consequently, we also ignore the ``:return:`` via ``..  # noqa: DAR201``.

.. highlight:: python
.. code-block:: python

    @property
    def name(self):
        """
        The name of the document.


        ..  # noqa: DAR201
        :getter: Returns this document's name
        :setter: Sets this document's name
        :type: string
        """
        return self._name

*****************************************************
Private methods
*****************************************************

You can safely ignore docstring for private methods, such as methods started with ``_``.

*****************************************************
args and kwargs
*****************************************************

Each parameter in the signature must be documented, including ``*args`` and ``**kwargs``, but not ``self`` or ``cls``.

*****************************************************
The ``_init_`` method
*****************************************************

Put all the documentation in the class itself, including notes on the constructor.

Pre-commit hook
----------------------------------------------------

In Jina we use git's pre-commit hooks in order to make sure code is properly documented to match our style and high quality. The hook will automatically remind you to add docstrings to new code, or fix any unfit docstrings.

Follow the guide in [CONTRIBUTING.md](https://github.com/jina-ai/jina/blob/master/CONTRIBUTING.md) to install it.

*****************************************************
Disabling specific cases
*****************************************************

In some cases it is okay to disable linting. This is either due to our principles, or due to bugs or limitations in the linters.

1. We do not need to document exceptions in the docstrings. Use ``# noqa: DAR401``.
2. We do not need to document the return value in a ``@property`` method of a class. Use ``# noqa: DAR201``

Note: Please add two blank lines and two dots as the example below to ignore `# noqa` in sphinx autodoc.

.. highlight:: python
.. code-block:: python

    def dump(self, data: Union['BaseFlow', 'BaseExecutor', 'BaseDriver']) -> Dict:
        """Return the dictionary given a versioned flow object


        ..  # noqa: DAR401
        :param data: versioned flow object
        """
        raise NotImplementedError

Docstring Coverage
-------------------
We suggest leveraging `interrogate <https://github.com/econchick/interrogate>`_ to calculate the docstring coverage and find out missing docstrings.
You can create a configure file ``pyproject.toml`` with the following configurations.

.. highlight:: toml
.. code-block:: toml

    [tool.interrogate]
    ignore-init-method = false
    ignore-init-module = false
    ignore-magic = true
    ignore-semiprivate = true
    ignore-private = true
    ignore-property-decorators = false
    ignore-module = true
    fail-under = 75
    exclude = ["setup.py", "docs", "build"]
    ignore-regex = ["^get$", "^mock_.*", ".*BaseClass.*"]
    verbose = 0
    quiet = false
    whitelist-regex = []
    color = true

And run this command in terminal to acquire the docstring coverage report.

.. highlight:: bash
.. code-block:: bash

    interrogate -c jina/pyproject.toml -vv jina
