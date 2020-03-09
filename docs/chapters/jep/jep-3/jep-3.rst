JEP 3 --- Supporting Docker Container in Flow API
=================================================

:Author: Han Xiao (han.xiao@jina.ai)
:Created: Mar. 9, 2020
:Status: Draft
:Related JEPs:
:Created on Jina VCS version: ``@3a6bcf0``
:Merged to Jina VCS version: TBA
:Released in Jina version: TBA
:Discussions: https://github.com/jina-ai/jina/issues/33

.. contents:: Table of Contents
   :depth: 2

Abstract
--------

We describe why and how we add remote control to Jina


Motivation
----------

As a new feature for making Jina more easy to use, we allow one to start a Pod remotely via Flow API. This greatly expands the application scenarios of Jina. Users with multiple old laptops, raspberry pi can easily build a inhouse Jina-cluster, without knowing anything about Docker Swarm and Kubernetes.

Rationale
---------

The new ``SPAWN`` request
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We need a new control request which tells the **remote** Jina to spawn a :class:`jina.peapods.pod.Pod` **locally**.

The ``SPAWN`` request should be sent via gRPC not ZeroMQ for the sake of compatibility, so that all languages can use Jina.


The ``SPAWN`` request should carry a map of arguments that :class:`jina.peapods.pod.Pod` accepted.

When


Who should be returned
^^^^^^^^^^^^^^^^^^^^^^

The log of opened Pod should be returned back to the client.




Specification
-------------


Backwards Compatibility
-----------------------
