<table>
  <tr>
    <td width="70%"><h1>Jina 101: First Thing to Learn About Jina</h1>      
      <a href="https://twitter.com/intent/tweet?text=%F0%9F%91%8DCheck+out+Jina%3A+the+New+Open-Source+Solution+for+Neural+Information+Retrieval+%F0%9F%94%8D%40JinaAI_&url=https%3A%2F%2Fgithub.com%2Fjina-ai%2Fjina&hashtags=JinaSearch&original_referer=http%3A%2F%2Fgithub.com%2F&tw_p=tweetbutton" target="_blank">
  <img src=".github/twitter-badge.svg"
       alt="tweet button" title="👍Check out Jina: the New Open-Source Solution for Neural Information Retrieval 🔍@JinaAI_"></img>
</a>
    </td>
    <td>
      <img src="img/ILLUS%2312.png" alt="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited" title="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited"/>
    </td>
  </tr>
</table>


<h2 align="center">Document & Chunk</h2>

<img align="left" src="img/ILLUS%231.png" alt="Jina 101 Concept Document and Chunk, Copyright by Jina AI Limited" title="Jina 101 Concept Document and Chunk, Copyright by Jina AI Limited" hspace="10" width="30%"/>



In Jina, a **Document** is anything that you want to search for: a text document, a short tweet, a code snippet an image, a video/audio clip, GPS traces of a day. A Document is also the input query when searching.

A Chunk is a small semantic unit of a Document. It could be a sentence, a 64x64 image patch, a 3 second video shot, a pair of coordinate and address. 

In Jina, a Document is like chocolate bar. Not only because it comes with different kinds and ingredients, but also you can break it into chunks in the way you like. Eventually, what you buy and store are the chocolate bars, and what you eat and digest are the chunks. You don’t want to swallow the whole bar, you also don’t want to cut it into powder; either way you will miss the flavor (i.e. the semantic).

<br/><br/><br/>


<h2 align="center">YAML config</h2>

<img align="right" src="img/ILLUS%232.png" alt="Jina 101 YAML, Copyright by Jina AI Limited" title="Jina 101 YAML Concept, Copyright by Jina AI Limited" hspace="10" width="30%"/>

A YAML config is widely used in Jina to describe the properties of an object. It offers customization, allowing users to change the behavior of an object without touching its code. Jina can build a very complicated object directly from a simple YAML config, and save an object into a YAML config.

<br/><br/><br/><br/><br/><br/>

<h2 align="center">Executor</h2>

<img align="left" src="img/ILLUS%233.png" alt="Jina AI Executor, Copyright by Jina AI Limited" title="Jina AI Executor Concept, Copyright by Jina AI Limited" hspace="10" width="30%"/>

Executor represents an algorithmic unit in Jina. Algorithms such as encoding images into vectors, storing vectors on the disk, ranking results, can all be formulated as Executors. Executor provides useful interfaces, allowing AI developers and engineers to really focus on the algorithm. Features such as persistency, scheduling, chaining, grouping and parallelization come out of the box.

The properties of an Executor are stored in a YAML config, they always go hands-in-hands.

<br/><br/><br/>

<h3 align="center">Family of Executors</h3>


<p align="center">
  <img src="img/ILLUS%234.png" alt="Jina 101 Family of Executor, Copyright by Jina AI Limited" title="Jina 101 Family of Executor, Copyright by Jina AI Limited" hspace="10" width="80%"/>
</p>

Executor is a big family. Each family member focuses on one important aspect of the search system. Let’s meet:
- Crafter: for crafting/segmenting/transforming the document and chunks
- Encoder: for representing the chunks as vectors
- Indexer: for saving and retrieving vectors from storage
- Ranker: for sorting the results

Having a new algorithm in mind? No problem, this family always welcome new members!


<h2 align="center">Driver</h2>

<img align="right" src="img/ILLUS%235.png" alt="Jina 101 Driver, Copyright by Jina AI Limited" title="Jina 101 Driver, Copyright by Jina AI Limited" hspace="10" width="30%"/>

Driver defines how an Executor behaves on network requests. Driver helps the Executor to handle the network traffic by interpreting the traffic data (e.g. Protobuf) into the format that the Executor can understand and handle (e.g. Numpy array).

<br/><br/><br/><br/><br/><br/>



<h2 align="center">Pea</h2>

<img align="left" src="img/ILLUS%236.png" alt="Jina 101 Pea, Copyright by Jina AI Limited" title="Jina 101 Pea, Copyright by Jina AI Limited" hspace="10" width="30%"/>

Pea wraps an Executor and grant it the ability to exchange data over a network. Pea can send and receive data from other Peas. Pea can also run inside a Docker container, containing all dependencies and the contextual environment in one place.

<img align="right" src="img/ILLUS%237.png" alt="Jina 101 Pea, Copyright by Jina AI Limited" title="Jina 101 Pea, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<br/><br/><br/><br/><br/><br/><br/><br/><br/>



<h2 align="center">Pod</h2>

<img align="left" src="img/ILLUS%238.png" alt="Jina 101 Pod, Copyright by Jina AI Limited" title="Jina 101 Pod, Copyright by Jina AI Limited" hspace="10" width="30%"/>

Pod is a group of Peas with the same property. Peas are running in parallel inside a Pod. Pod unifies the network interfaces of those Peas, making them look like one single Pea from outside. Beyond that, a Pod adds more control, scheduling and context management to the Peas.

Pod can be run either on local host or on different computers over a network. 

<img align="right" src="img/ILLUS%239.png" alt="Jina 101 Pod Remote, Copyright by Jina AI Limited" title="Jina 101 Pod Remote, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<br/><br/><br/><br/><br/><br/><br/><br/><br/>

<h2 align="center">Flow</h2>


<img align="left" src="img/ILLUS%2310.png" alt="Jina 101 Flow, Copyright by Jina AI Limited" title="Jina 101 Flow, Copyright by Jina AI Limited" hspace="10" width="30%"/>


Flow represents a high-level task, e.g. indexing, searching, training. It manages the states and context of a group of Pods, orchestrating them to accomplish one task. Flow embraces diversity, whether a Pod is remote or in the Docker container, one Flow to rule them all!

<br/><br/><br/><br/><br/><br/>



<h2 align="center">From Micro to Macro</h2>


Jina is a happy family. You can feel the harmony when you use Jina. 

You can design at the micro-level and scale that up to the macro-level. YAMLs becomes algorithms, threads become processes, pods become flows. The patterns and logic always remain the same. This is the beauty of Jina. 


<p align="center">
  <img src="img/ILLUS%2311.png" alt="Jina 101 All Characters, Copyright by Jina AI Limited" title="Jina 101 All Characters, Copyright by Jina AI Limited" hspace="10" width="80%"/>
</p>

<br/><br/><br/><br/><br/><br/>

<p align="center">
    ✨<b>Unleash your curiosity and happy searching! </b>🔍
</p>


