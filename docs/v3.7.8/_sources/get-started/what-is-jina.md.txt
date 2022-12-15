(what-is-jina)=
# What is Jina?

Jina is the framework for helping you to build cross-modal and multi-modal systems on the cloud. With Jina, developers can easily build high performant cloud native applications, services and systems in production. But at this point, you are not buying those campaign words. That's okay and that's what this chapter is about: to tell you what Jina is and to convince you about it.

In the {ref}`last chapter<intro-cm>`, you already learned the idea of cross-modal and multi-modal from the machine learning perspective. This chapter will talk more from the system and engineering side. Let's start with an example and understand why Jina is needed.

(motivate-example)=
## Motivation example

Why do you need Jina? Let's first see an example that describes a life without Jina.

Imagine you are a **machine learning engineer** whose task is to build a shop-the-look service for an e-commerce company, i.e. allowing users to upload a photo and search visually similar items from the stock. Sounds cool and deep learning related, exactly what your expertise is, so let's get started.

### Prototype

There are two mode of the system, one is **indexing**, which is to create the visual representation of all stock items, the other is **search**, which is to take a user-uploaded photo and find the visually similar items from stock.

The indexing part is to create a visual representation of all the stock items. In order to do this, you need to first extract features from the images to create the visual representation. The features could be extracted using a convolutional neural network, and then be stored in a database. 

The search part is to take a user-uploaded photo and find the visually similar items from stock. You first need to extract features from the user-uploaded photo using a convolutional neural network. Then, you can use the similarity metric to find the visually similar items from the stock. The similarity metric could be cosine similarity.

At this point, you need a deep learning framework such as PyTorch, some key-value database such as MongoDB, and possibly some vector search engine such as FAISS or Elasticsearch. As a machine learning engineer, you are mostly familiar with PyTorch and prototyping. You are smart and full of energy so nothing you can't learn. You easily glue them together as the first _proof of concept_ (POC).

### As a service

Are we done? We just start. Instead of some Python functions, your goal is to make it as a web service so that its IO goes through network. To do that, you need to _refactor_ the above logic in some web framework with some API so that it can be called by other services.

There are many ways to do this, one example would be to use the Django web framework. You would create an endpoint that accepts user-uploaded photos, then use the above logic to find the visually similar items from stock. Finally, you would return the results to the user in the form of a JSON object.

At this point, you learned a few new things such as REST API, web service, web framework, which seems to go beyond your scope of a "machine learning engineer". You started to wonder whether it is worth it to learn them. But a machine learning **engineer** is an engineer after all, and learning new things is always good. But deep down you feel that your engineering may not be sufficient to make it into production. After some time, you managed to glue everything together.

### Deployment

The product team is impressed by the progress and asks you to deploy it on AWS to serve some real traffic. This is exciting because it means your POC will face the public and have real users. You encountered many problems while migrating from local to the cloud, mostly because of dependencies issues, CUDA driver and GPU issues. You finally solved all of them by wrapping everything in a 30GB Docker image. It is a _big_ monolith container, but it is easy to deploy and manage for you. 

### Scalability and performance

Are we done now? Not yet. The product team wants to ensure certain scalability of the service in practice, meaning that the feature extraction should be parallelized and concurrent user requests should be handled without lagging. Certain QPS (query per second) is required from the product team.

You tried the straightforward `multiprocessing` and `threading`, but nothing works out of the box with your deep learning stacks. You decided to learn more high-performance computing frameworks such as Dask or Ray and try to adopt them. After some trial and error, you finally glued everything together and made them work. At this point you feel exhausted as it diverges too far from your expertise. 

### Availability and downtime

_"What if our database is down (due to update) for a short-time?"_

So you designed some naive failsafe mechanism that you just learned from a blog post. You also picked up some AWS service in a rush to ensure the availability of the service, hoping it can be fire-and-forget.

### Observability

_"How can I see the incoming traffic?"_

You changed all `print` to `logger.info` and impatiently spun up a dashboard.

### Security

_"Can we add some authentication header to it?"_

_"Is this service prone to attack?"_

At this point, you are burnt out. It goes too far away from your expertise. You decided to hand over the project to a senior backend engineer, who is a new hire but has a lot of experience in infrastructure engineering and cloud services. He knows what he is doing and is willing to help you.

So you sit down with him, scrolling over your glued code and justifying all your tricks, design decisions and explaining all the caveats. He kept nodding and you see it as some kind of recognition. Soon after he took a slow and thoughtful sip of his coffee, he said: 

_"Why don't we start to rewrite it?"_

## Problems and Jina's solution

The above example is quite real, and it reveals some gaps when developing a cross-modal/multi-modal system in production:

**First is the lack of design pattern for such system.** It is unclear how should one represent, compute, store, and transit the data with different modalities in a consistent way; and how can one switch between different tools and avoid glue code. 

**Second is the large gap of between a proof-of-concept and a production system.** For a production system, cloud native techniques are often required to ensure the professionalism and scalability of the system. In particular, microservices, orchestration, containerization and observability are four pillars of such system. However, the learning curve is too steep for many machine learning engineers, preventing them to build production ready system.

**Third is the long go-to-market time**. If a company chooses a wrong tech stack, it will take longer to bring the product to market. This is because the company will have to spend more time and resources on developing the product, refactoring it, going back and forth. In addition, a wrong stack can cause problems with the product itself, raising the risk of the product being unsuccessful.

Jina is a solution to address above problems by providing a consistent design pattern for cross-modal/multi-modal systems with the latest cloud native technologies.

### Why cloud native?

At first cloud native seems pretty irrelevant: why a cross-modal/multi-modal system is any related to cloud native? 

Cloud native is a term that refers to a system that is designed to run on the cloud. It consists of a group of concepts:
- **Microservices**: Microservices are the building blocks of a cloud native system.
- **Orchestration**: Orchestration is the process of managing the microservices.
- **Containerization**: Containerization is the process of packaging the microservices into containers.
- **Observability**: Observability is the process of monitoring the system.
- **DevOps and CI/CD**: DevOps and CI/CD are the process of automating the integration of the system.

Sounds cool but irrelevant, so do we really need them?

Yes!

| Characteristics of a cross-modal/multi-modal system                                                                                                                  | How would Cloud-native help                                                                                          |
|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------|
| Cross-modal/multi-modal system is not a single task, it usually consists of multiple components and forms a workflow or multiple workflows (e.g. indexing and search) | **Microservice** each task, then **orchestrate** them into workflows.                                                |
| Cross-modal/multi-modal system involves complicated package dependencies.                                                                                            | **Containerization** comes to help to ensure the reproducibility and isolation.                                      |
| Cross-modal/multi-modal system is often a backend/infrastructure service that requires extra stablilty.                                                              | **DevOps and CI/CD** guarantees the integration and **Observability** provides the health information of the system. |


With that, let me reiterate what Jina is: Jina is a framework that provides a unified, cloud native solution for building cross-modal/multi-modal systems from day one. It provides the best developer experience from day one POC to production. It smooths your journey by resolving every challenge mentioned in all subsections of {ref}`motivate-example`. No more tech debt, no more refactoring and back and forth between different systems.

Now it starts to make sense, right? Let's get our first taste on how a Jina project looks like and how does it work.

## Taste of Jina

Let's look at a simple Jina hello world example. We write a function that appends `"hello, world"` to a Document, we apply the function twice for the two Documents, then return and print their texts.

````{tab} With Jina
```python
from jina import DocumentArray, Executor, Flow, requests


class MyExec(Executor):
    @requests
    async def foo(self, docs: DocumentArray, **kwargs):
        for d in docs:
            d.text += 'hello, world!'


f = Flow().add(uses=MyExec).add(uses=MyExec)

with f:
    r = f.post('/', DocumentArray.empty(2))
    print(r.texts)
```

```console
────────────────────────── 🎉 Flow is ready to serve! ──────────────────────────
╭────────────── 🔗 Endpoint ───────────────╮
│  ⛓     Protocol                    GRPC  │
│  🏠       Local           0.0.0.0:52570  │
│  🔒     Private     192.168.1.126:52570  │
│  🌍      Public    87.191.159.105:52570  │
╰──────────────────────────────────────────╯

['hello, world!hello, world!', 'hello, world!hello, world!']
```

````
````{tab} Plain Python
```python
class Document:
    text: str = ''


def foo(docs, **kwargs):
    for d in docs:
        d.text += 'hello, world!'


docs = [Document(), Document()]
foo(docs)
foo(docs)
for d in docs:
    print(d.text)
```


```console
['hello, world!hello, world!', 'hello, world!hello, world!']
```
````

It is a pretty straightforward program. It abstracts away the complexity of a real cross-modal & multi-modal system, leaving only the basic logics: make a data structure, operate on it, and return the result. 

In fact, one can achieve the same in 14 lines of code (`black`ed) with pure Python.

So does using Jina mean learning some weird design pattern that needs one extra line of code to achieve the same result with pure Python? What's the deal?

Here is the deal. The features below come out of the box with the above 15 lines of code:

- Replicas, sharding, scalability in just one line of code;
- Client/server architecture with duplex streaming;
- Async non-blocking data workflow;
- gRPC, Websockets, HTTP, GraphQL gateway support;
- Microservice from day one, Docker containerization seamlessly;
- Explicit version and dependency control;
- Reuse building blocks from Hub marketplace;
- Immediate observability via Prometheus and Grafana;
- Kubernetes seamless integration.

If you think that's a lot of over-promises, it is not. In fact, they barely scratch the surface of Jina's capability.

## Design principles

With so many powerful features, the learning curve of Jina must be very steep, you might think. But it is not. In fact, you only need to know three concepts to master Jina. They are Document, Executor and Flow, which are introduced in {ref}`architecture-overview`.

A full-fledged cross-modal/multi-modal system is a combination of the following seven layers:

```{figure} 7-layers.png
:scale: 40%
```

This illustration is not exaggerating, it is a real-world example of a cross-modal/multi-modal system in production.

Fortunately, as a Jina developer, you don't need to understand all of them. You only need to know what are relevant to your product logic and let Jina handles the rest. In particular, 

- **The data type**: represents the common data structure across the system; this corresponds to "**Document**" in Jina.
- **The logic**: represents the product logic of each component; this corresponds to "**Executor**" in Jina.
- **The orchestration**: represents the workflow of all components; this corresponds to "**Flow**" in Jina.

are all you need.

```{figure} 3-layers.png
:scale: 50%
```

Patterns are nice, cloud native features are cool. But what's the point if you need to spend months to learn them? Jina's design principles are simple and clear: flatten the learning curve of cloud native techniques and make all awesome production-level features easily accessible.


## Summary

Before Jina, building a cross-modal/multi-modal system was a tedious and time-consuming process. It involved a lot of glue code, back and forth refactoring and after months you eventually end up with a fragile system that is unsustainable. With Jina, you are doing it professionally from day one: from POC to production; from deployment to scaling; from monitoring to analytics; everything is taken care of by Jina. We know the pain, we have the lessons learned and that's why we build Jina: to make developing cross-modal and multi-modal system an easier, productive and enjoyable experience for you.






