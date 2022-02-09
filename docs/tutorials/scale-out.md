# Executor Scale-Out With Replicas & Shards

```{article-info}
:avatar: avatars/bo.jpg
:avatar-link: https://jobs.jina.ai
:avatar-outline: muted
:author: Bo @ Jina AI
:date: February 8, 2022
```

## Overview

A typical Jina `Flow` orchestrates multiple `Executors`.
By default, a Jina `Executor` runs with a single `Replica` and `Shard`.
Some `Executor` in the Flow might be less performant than other `Executors`,
this could be a performance bottleneck when you deploy your Jina service to production environment 

Luckily, Jina `Flow` allows you to config the number of `Replicas` and `Shards`.
`Replica` is used to increase `Executor` throughput and availability.
`Shard` is used for data partitioning.
In this tutorial, we'll dive into these two concepts and see how you can make use of `Replica` and `Shard` to scale out your `Executor`.

## Before you start
<!-- Delete this section if your readers can go to the steps without requiring any prerequisite knowledge. -->
Before you begin, make sure you meet these prerequisites:

* You have a good understanding of Jina [Flow](../fundamentals/flow/index.md).
* You have a good understanding of Jina [Executor](../fundamentals/executor/index.md)

## Speed-Up A Slow Executor: Replicas

### Context

### Scale-Up your Executor

## Split Data over Machines: Shards

### Context

### Partitioning your Data

### Different POOLING Strategies

## Concept Alignment: How does it work on Localhost, Docker and K8s

## Where to go next:
If there are known feature limitations that a user would expect to see mention them here.