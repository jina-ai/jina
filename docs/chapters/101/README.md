<table>
  <tr>
    <td width="70%"><h1>Jina 101: First Things to Learn About Jina</h1>
    <a href="https://twitter.com/intent/tweet?text=%F0%9F%91%8DCheck+out+Jina%3A+the+New+Open-Source+Solution+for+Neural+Information+Retrieval+%F0%9F%94%8D%40JinaAI_&url=https%3A%2F%2Fgithub.com%2Fjina-ai%2Fjina&hashtags=JinaSearch&original_referer=http%3A%2F%2Fgithub.com%2F&tw_p=tweetbutton" target="_blank">
  <img src="../../../.github/badges/twitter-share101.svg?raw=true"
       alt="tweet button" title="👍Check out Jina: the New Open-Source Solution for Neural Information Retrieval 🔍@JinaAI_"></img>
</a>
  <a href="../../../README.md#jina-hello-world-">
    <img src="../../../.github/badges/jina-hello-world-badge.svg?raw=true" alt="Run Jina Hello World">
</a>

<a href="https://docs.jina.ai">
    <img src="../../../.github/badges/docs-badge.svg?raw=true" alt="Read full documentations">
</a>
<a href="https://github.com/jina-ai/jina/">
    <img src="../../../.github/badges/jina-badge.svg?raw=true" alt="Visit Jina on Github">
</a>
<a href="https://jobs.jina.ai">
    <img src="../../../.github/badges/jina-corp-badge-hiring.svg?raw=true" alt="Check out jobs@Jina AI">
</a>
    <a href="#">
    <img src="../../../.github/badges/pdf-badge.svg?raw=true" alt="Download PDF version of Jina 101">
    </a>
     <br>
<a href="README.md">English</a> •
  <a href="README.ja.md">日本語</a> •
  <a href="README.fr.md">Français</a> •
  <a href="README.pt.md">Português</a> •
  <a href="README.de.md">Deutsch</a> •
  <a href="README.ru.md">Русский язык</a> •
  <a href="README.zh.md">中文</a> •
  <a href="README.ar.md">عربية</a>
    </td>
    <td>
      <img src="img/ILLUS12.png?raw=true" alt="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited" title="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited"/>
    </td>
  </tr>
</table>

Want a general introduction to neural search and how it's different to regular old symbolic search? [Check out our explainer blog post](https://medium.com/@jina_ai/what-is-jina-and-neural-search-7a9e166608ab) to learn more!

<h2 align="center">Document & Chunk</h2>

<img align="left" src="img/ILLUS1.png?raw=true" alt="Jina 101 Concept Document and Chunk, Copyright by Jina AI Limited" title="Jina 101 Concept Document and Chunk, Copyright by Jina AI Limited" hspace="10" width="30%"/>

When most people think of search, they think of a bar you type words into, like Google. But search is much more than that - as well as text, you may want to search for a song, recipe, video, genetic sequence, scientific paper, or location.

In Jina, we call all of these things **Documents**. In short, a Document is anything you want to search for, and the input query you use when searching.

Documents can be huge though - how can we search for the right part? We do this by breaking a Document into **Chunks**. A Chunk is a small semantic unit of a Document, like a sentence, a 64x64 pixel image patch, or a pair of coordinates. 

You can think of a Document like a chocolate bar. Documents have different formats and ingredients, but you can also break it into chunks any way you like. Eventually, what you buy and store are the chocolate bars, and what you eat and digest are the chunks. You don’t want to swallow the whole bar, but you don’t want to grind it into powder either; By doing that, you lose the flavor (i.e. the semantics).

<br/><br/><br/>

<h2 align="center">YAML Config</h2>

<img align="right" src="img/ILLUS2.png?raw=true" alt="Jina 101 YAML, Copyright by Jina AI Limited" title="Jina 101 YAML Concept, Copyright by Jina AI Limited" hspace="10" width="30%"/>

Every part of Jina is configured with **YAML files**. YAML files offer customization, allowing you to change the behavior of an object without touching its code. Jina can build a very complicated object directly from a simple YAML file, or save an object into a YAML file.

<br/><br/><br/><br/><br/><br/>

<h2 align="center">Executors</h2>

<img align="left" src="img/ILLUS3.png?raw=true" alt="Jina AI Executor, Copyright by Jina AI Limited" title="Jina AI Executor Concept, Copyright by Jina AI Limited" hspace="10" width="30%"/>

How do we break down a Document into Chunks, and what happens next? **Executors** do all of this hard work, and each represents an algorithmic unit. They do things like encoding images into vectors, storing vectors on disk, ranking results, and so on. Each one has a simple interface, letting you concentrate on the algorithm and not get lost in the weeds. They handle feature persistence, scheduling, chaining, grouping, and parallelization out of the box. The properties of an Executor are stored in a [YAML file](#configuring-jina-with-yaml). They always go hand in hand.

<br/><br/><br/>

<h3 align="center">The Executor Family</h3>


<p align="center">
  <img src="img/ILLUS4.png?raw=true" alt="Jina 101 Family of Executor, Copyright by Jina AI Limited" title="Jina 101 Family of Executor, Copyright by Jina AI Limited" hspace="10" width="80%"/>
</p>

The **Executors** are a big family. Each family member focuses on one important aspect of the search system. Let’s meet:
- **Crafter**: for crafting/segmenting/transforming the Documents and Chunks;
- **Encoder**: for representing the Chunk as vector;
- **Indexer**: for saving and retrieving vectors and key-value information from storage;
- **Ranker**: for sorting results;

Got a new algorithm in mind? No problem, this family always welcomes new members!

<br/><br/>

<h2 align="center">Drivers</h2>

<img align="right" src="img/ILLUS5.png?raw=true" alt="Jina 101 Driver, Copyright by Jina AI Limited" title="Jina 101 Driver, Copyright by Jina AI Limited" hspace="10" width="30%"/>

Executors do all the hard work, but they're not great at talking to each other. A **Driver** helps them do this by defining how an Executor behaves to network requests. It interprets network traffic into a format the Executor can understand, for example translating Protobuf into a Numpy array.

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>



<h2 align="center">Peas</h2>

<img align="left" src="img/ILLUS6.png?raw=true" alt="Jina 101 Pea, Copyright by Jina AI Limited" title="Jina 101 Pea, Copyright by Jina AI Limited" hspace="10" width="30%"/>

All healthy families need to communicate, and the Executor clan is no different. They talk to each other via **Peas**.

While a Driver translates data for an Executor, A Pea wraps an Executor and lets it exchange data over a network or with other Peas. Peas can also run in Docker, containing all dependencies and context in one place.

<img align="right" src="img/ILLUS7.png?raw=true" alt="Jina 101 Pea, Copyright by Jina AI Limited" title="Jina 101 Pea, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>



<h2 align="center">Pods</h2>

<img align="left" src="img/ILLUS8.png?raw=true" alt="Jina 101 Pod, Copyright by Jina AI Limited" title="Jina 101 Pod, Copyright by Jina AI Limited" hspace="10" width="30%"/>

So now you've got lots of Peas talking to each other and rolling all over the place. How can you organize them? Nature uses **Pods**, and so do we.

A Pod is a group of Peas with the same property, running in parallel on a local host or over the network. A Pod provides a single network interface for its Peas, making them look like one single Pea from the outside. Beyond that, a Pod adds further control, scheduling, and context management to the Peas.

<img align="right" src="img/ILLUS9.png?raw=true" alt="Jina 101 Pod Remote, Copyright by Jina AI Limited" title="Jina 101 Pod Remote, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>

<h2 align="center">Flow</h2>


<img align="left" src="img/ILLUS10.png?raw=true" alt="Jina 101 Flow, Copyright by Jina AI Limited" title="Jina 101 Flow, Copyright by Jina AI Limited" hspace="10" width="30%"/>


Now we've got a garden full of Pods, with each Pod full of Peas. That's a lot to manage! Say hello to **Flow**! Flow is like a Pea plant. Just as a plant manages nutrient flow and growth rate for its branches, Flow manages the states and context of a group of Pods, orchestrating them to accomplish one task. Whether a Pod is remote or running in Docker, one Flow rules them all!

<br/><br/><br/><br/><br/><br/>



<h2 align="center">From Micro to Macro</h2>


Jina is a happy family. You can feel the harmony when you use Jina.

You can design at the micro-level and scale up to the macro-level. YAMLs becomes algorithms, threads become processes, Pods become Flows. The patterns and logic always remain the same. This is the beauty of Jina.


<p align="center">
  <img src="img/ILLUS11.png?raw=true" alt="Jina 101 All Characters, Copyright by Jina AI Limited" title="Jina 101 All Characters, Copyright by Jina AI Limited" hspace="10" width="80%"/>
</p>

<br/><br/><br/><br/>

<p align="center">
<a href="../../../README.md#jina-hello-world-">
    ✨<b>Intrigued? Try our "Hello, World!" and build your neural image search in 1 min. </b>
</a>
</p>
<br><br><br>
<p align="center">
    ✨<b>Unleash your curiosity and happy searching! </b>🔍
</p>
<br><br><br>
<p align="center">
    <a href="https://twitter.com/intent/tweet?text=%F0%9F%91%8DCheck+out+Jina%3A+the+New+Open-Source+Solution+for+Neural+Information+Retrieval+%F0%9F%94%8D%40JinaAI_&url=https%3A%2F%2Fgithub.com%2Fjina-ai%2Fjina&hashtags=JinaSearch&original_referer=http%3A%2F%2Fgithub.com%2F&tw_p=tweetbutton" target="_blank">
  <img src="../../../.github/badges/twitter-share101.svg?raw=true"
       alt="tweet button" title="👍Check out Jina: the New Open-Source Solution for Neural Information Retrieval 🔍@JinaAI_"></img>
</a>
  <a href="../../../README.md#jina-hello-world-">
    <img src="../../../.github/badges/jina-hello-world-badge.svg?raw=true" alt="Run Jina Hello World">
</a>

<a href="https://docs.jina.ai">
    <img src="../../../.github/badges/docs-badge.svg?raw=true" alt="Read full documentations">
</a>
<a href="https://github.com/jina-ai/jina/">
    <img src="../../../.github/badges/jina-badge.svg?raw=true" alt="Visit Jina on Github">
</a>
<a href="https://jobs.jina.ai">
    <img src="../../../.github/badges/jina-corp-badge-hiring.svg?raw=true" alt="Check out jobs@Jina AI">
</a>
    <a href="#">
    <img src="../../../.github/badges/pdf-badge.svg?raw=true" alt="Download PDF version of Jina 101">
    </a>
</p>
<br><br><br>



The look and feel of this document ("Jina 101: First Things to Learn About Jina") is copyright © Jina AI Limited. All rights reserved. Customer may not duplicate, copy, or reuse any portion of the visual design elements or concepts without express written permission from Jina AI Limited.

