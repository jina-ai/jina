# What is Jina?

Jina is a neural search framework written in Python that helps developers build neural search applications that can be easily scaled and deployed in the Cloud.



Jina empowers developers to focus on their business logic, by guiding them with abstractions that will help to modularize, serve and scale applications in the cloud.

Jina can help you in every phase of the development cycle, from prototyping to deployment. It is designed to provide a unified experience when developing your solutions locally and in the cloud. It builds your applications with a set of separate microservices that can be scaled independently and easily.

As part of [Jina AI ecosystem](https://jina.ai/), Jina brings your search to production. [**DocArray**](https://docarray.jina.ai/) to serve as the main data structure; [**Jina Hub**](https://hub.jina.ai/) to share, containerize and reuse components of the search pipelines.



## Design 

Jina is designed as a lean and easy-to-use framework. There are only two main concepts to learn:

- {ref}`Executor <executor-cookbook>` is a self-contained component and performs a group of tasks on [Documents](https://docarray.jina.ai/).
- {ref}`Flow <flow-cookbook>` ties Executors together into a processing pipeline, provides scalability and facilitates deployments in the cloud.


# Comparing to Alternatives

Sometimes the question arises of how Jina compares to different libraries and frameworks. Here we want to shed light on some of the
most commonly-drawn comparisons:

## Comparing to MLOps frameworks

At first glance, Jina and MLOps frameworks such as **MLFlow**, **KubeFlow** or **RayWorkflow** may seem quite similar:
They all have complex pipelines, or *Flows*, through which data can be processed.
At closer inspection, though, standard MLOps frameworks are quite different from Jina, because they were *designed with
a different purpose in mind*.

Usually, MLOps frameworks are geared towards scheduling and operating individual jobs relating to training,
hyperparameter tuning, and other machine learning tasks.
These jobs are commonly very time-consuming, and create artifacts which trigger events.

In contrast, Jina is a tool to *build and serve neural search applications as microservices*.
Microservices communicate through the network in a *streaming* fashion: Every microservice (called **Executor**) in a
**Flow** constantly receives and continuously processes data, in the form of **Documents**.

## Comparing to model serving frameworks

Jina's ability to scale and replicate its *Executor* microservices might sound reminiscent of model serving frameworks
such as **Seldon Core**.

Seldon is designed to serve and expose machine learning models of different kinds, such as classifiers, regressors and others.
This is done by deploying model artifacts from different ML frameworks in predefined ways.

Jina, on the other hand, is built from the ground up for *end-to-end neural search applications*, and brings along an
entire neural search ecosystem, including [DocArray](https://docarray.jina.ai/) and [Finetuner](https://finetuner.jina.ai/).
Furthermore, Jina gives *all the power to the user*, letting them define their own logic, in a Pythonic way.

## Comparing to vector databases

Another natural comparison within the neural search ecosystem is between Jina and vector databases.

The main distinction is the following: Jina is **not** a vector database. 

Jina is a *neural search framework* to build complete *end-to-end search applications*.
With the power of *DocumentArray* and *Executors*, Jina allows the user to integrate external vector databases into a
complete search application.
 
In summary, Jina takes care of the complete neural search pipeline and lets users integrate their own custom logic
and persistence layer into their applications.
