JEP 2 --- Supporting Docker Container in Flow API
=================================================

:Author: Han Xiao (han.xiao@jina.ai)
:Created: Feb. 29, 2020
:Status: Draft
:Related JEPs:
:Created on Jina VCS version: ``@c66b4b9``
:Merged to Jina VCS version: TBA
:Released in Jina version: TBA
:Discussions: https://github.com/jina-ai/jina/issues/33

.. contents:: Table of Contents
   :depth: 2

Abstract
--------

We describe why and how we make :mod:`jina.flow` to support Docker container.


Motivation
----------

:mod:`jina.flow` serves as the primary interface for Jina's new users. It provides a set of friendly, easy-to-use API to organize a flow of microservices (aka, :class:`jina.peapods.pod.Pod`). It also provides basic orchestration abilities, such as start, scale up, flow pruning and terminate. This saves user quite some time as they would otherwise launch each :class:`jina.peapods.pod.Pod` and connect them manually.

In the current version, :class:`jina.flow.Flow` supports :func:`jina.flow.Flow.add` to allow user to define their own "graph" by specifying ``send_to``, ``recv_from``. The :class:`jina.flow.Flow` later uses :func:`jina.flow.Flow.build` method and connects all the ``Pod`` together. All sockets assignment are hidden from the user perspective.

One of the big limitations of the current :class:`jina.flow.Flow` is it does not support containerization, either partial or wholly. Imagine a user needs to run a :class:`jina.peapods.pod.Pod` in a container because of the complicated dependencies it relies on. The current :class:`jina.flow.Flow` can not do that. All :class:`jina.peapods.pod.Pod` are either run as a thread or process. This is in fact a common requirement as most of the DL/AI libraries do require specific versions of the DL package or complicated dependencies. Promoting the idea of "Model-as-Docker" and encouraging users to adapt to this idea not only solves the dependency issue, but also serves as preliminary education to our Jina Hub.

Rationale
---------

To add containerization feature to the :class:`jina.flow.Flow`, we first need to understand what are the common use cases.

- All pods run outside of the container locally;
    This is already supported in the current version
- All pods run outside of the container remotely;
    This should be supported but not tested. For the sake of security, this should not be encouraged.
- Some pods run outside of the container;
    This is a common use case, either locally or remotely.
- All pods run inside of **one** container;
    No clear usage. May need to design the API separately
- Each pod runs in its own container;
    This is a special case of "some pods run outside of the container".

As one can observe from the list, designing an API that allows Pods running locally or remotely, inside or outside the container is the key of this JEP. Imagine we add two new arguments when spawning each pod, ``host`` and ``docker_image``. Note that these two arguments should not be added to the arguments of :class:`jina.peapods.pod.Pod` but to :func:`jina.flow.Flow.add`.


Can we support remote Pod in the Flow API?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Let's first look at ``host`` argument. Supposedly,

.. confval:: host

    ``host`` describes the IP address that the added ``Pod`` will be running on, e.g. ``192.168.1.20``.

    :type: str

One immediate problem is that :class:`jina.flow.Flow` has no way to start this ``Pod`` remotely on ``192.168.1.20``. To achieve, all remote workers need to register themselves or keep a daemon in the background, waiting the "master" Flow sending a "spawning" signal to them so they can start. We have no intention to implement such mechanism right now. This is completely out of the scope of the Flow API and seems reinventing the orchestration layer of Kubernetes or Docker Swarm.

Assuming the Pod is started already on the ``host``, then writing ``host`` as an argument of :func:`jina.flow.Flow.add` can make it accessible to other Pods. This looks true at first, but look at the example below:


.. highlight:: python
.. code-block:: python

    f = (Flow().add(name='p1', host='192.168.0.2')
                .add(name='p2', host='192.168.0.3')
                .join(['p1', 'p2']))  # -> p3


In the example, `p3` is blocking the flow until `p1` and `p2` are all done. `p3` is on the "bind" side, `p1` and `p2` are on the "connect" side. Therefore, it is in fact `p3` who needs to expose its IP to `p1` and `p2` to make sure ``p2.host_out = p3.host`` and ``p2.host_out = p3.host``, not in the other way. Simply put, the ``host`` argument of `p1` and `p2` is useless in this case. Besides that, as `p1` and `p2` are already running in remote (manually), their ``host_out`` is not changeable by the Flow. This simple use case is not even possible if the Flow can not spawn Pod remotely.

So what can we support? If a remote pod is on the "bind" side, and the local pods are on the "connect" side, then this works fine. Though in this case we can simply use the existing ``host_in``, ``host_out``. For example,

.. highlight:: python
.. code-block:: python

    f = (Flow().add(name='p1')  # -> p1 running remotely on 192.168.0.2
                .add(name='p2', host_in='192.168.0.2')
        )


That is, in the current Flow API a remote pod must be "bind" on both input socket and output socket. Otherwise, its "connect" socket must be specified with an IP address that is manually given when spawning.

Note, it is difficult to guarantee a "bi-bind" Pod in an arbitrary flow. Depending on the topology, the input/output socket may switch the role between "bind" and "connect". Implementing heuristics to maximize the chance that a remote Pod enjoys  "bi-bind" may be possible, but is tedious and not very cost-effective.

As the conclusion, **we decide not to support remote Pod in this JEP.** All pods can only run locally.


Run pods in their own container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^



Specification
-------------


Backwards Compatibility
-----------------------

