What is a JEP?
==============

JEP stands for Jina Enhancement Proposal. A JEP is a design document providing information to the JIna community, or describing a new feature for Jina or its processes or environment. The JEP should provide a concise technical specification of the feature and a rationale for the feature.

We learn from the `PEP standard <https://www.python.org/dev/peps/pep-0001/#what-is-a-pep>`_ and intend JEPs to be the primary mechanisms for proposing major new features, for collecting community input on an issue, and for documenting the design decisions that have gone into Python. The JEP author is responsible for building consensus within the community and documenting dissenting opinions.

.. contents:: Table of Contents
   :depth: 2


Who should write JEP?
---------------------

The JEP process begins with a new idea for Jina. It is highly recommended that a single JEP contain a single key proposal or new idea. Small enhancements or patches often don't need a JEP and can be injected into the Jina development workflow with a Github submission to the Jina issue tracker.

The following scenarios may require a JEP:

- Adding a new module that affects how Jina works or interacts with users;
- Refactoring multiple modules and touched more than 500 lines of codes;
- Changing the core part of Jina and it will hurt the backward comparability.


JEP File Format
---------------
JEPs are UTF-8 encoded text files using the `reStructuredText format <https://www.python.org/dev/peps/pep-0001/#id19>`_. ReStructuredText allows for rich markup that is still quite easy to read, but also results in good-looking and functional HTML.


JEP Header Template
-------------------

.. highlight:: rst
.. code-block:: rst

    :Author: <list of authors' real names and optionally, emails>
    :Created: Feb. 24, 2020
    :Status: <Draft | Active | Accepted | Provisional | Deferred | Rejected |
           Withdrawn | Final | Superseded>
    :Related JEPs: <jep numbers in the format of JEP-%d>
    :Created on Jina VCS version: <short hex vcs>
    :Merged to Jina VCS version: <short hex vcs>
    :Released in Jina version: <version number>
    :Discussions: <Github issue's address>

    .. contents:: Table of Contents
       :depth: 2


Suggested Sections
------------------

.. highlight:: rst
.. code-block:: rst

    Abstract
    --------

    [A short (~200 word) description of the technical issue being addressed.]


    Motivation
    ----------

    [Clearly explain why the existing code is inadequate to address the problem that the JEP solves.]


    Rationale
    ---------

    [Describe why particular design decisions were made.]


    Specification
    -------------

    [Describe the syntax and semantics of any new feature.]


    Backwards Compatibility
    -----------------------

    [Describe potential impact and severity on pre-existing code.]


    Security Implications
    ---------------------

    [How could a malicious user take advantage of this new feature?]


    Reference Implementation
    ------------------------

    [Link to any existing implementation and details about its state, e.g. proof-of-concept.]


    Open Issues
    -----------

    [Any points that are still being decided/discussed.]


    References
    ----------

    [A collection of URLs used as references through the JEP.]


Current JEPs
============

.. toctree::
   :maxdepth: 1

   jep-1/main
   jep-2/main
