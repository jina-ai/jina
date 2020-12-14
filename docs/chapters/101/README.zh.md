<table>
  <tr>
    <td width="70%"><h1>Jina 101: First Thing to Learn About Jina</h1>
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
  <a href="README.fr.md">français</a> •
  <a href="README.pt.md">Português</a> •
  <a href="README.de.md">Deutsch</a> •
  <a href="README.ru.md">Русский язык</a> •
  <a href="README.zh.md">中文</a>
  <a href="README.ar.md">عربية</a>
    </td>
    <td>
      <img src="img/ILLUS12.png?raw=true" alt="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited" title="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited"/>
    </td>
  </tr>
</table>

<h2 align="center">Document & Chunk</h2>

<img align="left" src="img/ILLUS1.png?raw=true" alt="Jina 101 Concept Document and Chunk, Copyright by Jina AI Limited" title="Jina 101 Concept Document and Chunk, Copyright by Jina AI Limited" hspace="10" width="30%"/>

在Jina中。**Document是指你要搜索的任何东西**。检索对象：文本文档、简短的推文、代码片段、图片、视频/音频片段、一天的GPS轨迹等。Document也是搜索时的输入查询。

**Chunk是Document的一个小语义单位**。可以是一个句子，一个64X64的图像补丁，一个3秒的视频片段，一对坐标和地址。

在Jina中，Document就像巧克力棒一样。不仅因为它有不同的形式和成分，而且你可以用自己喜欢的方式把它分成大块。最终，你买来的是巧克力棒，储存的是巧克力块，而你吃下去消化的是巧克力块。你不想把整块巧克力棒吞下去，你也不想把它磨成粉，无论哪种方式，你都会失去它的味道（即语义）。

<br/><br/><br/>

<h2 align="center">YAML config</h2>

<img align="right" src="img/ILLUS2.png?raw=true" alt="Jina 101 YAML, Copyright by Jina AI Limited" title="Jina 101 YAML Concept, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**在Jina中，YAML配置被广泛用于描述一个对象的属性**。它提供了自定义功能，允许用户在不接触对象代码的情况下改变对象的行为。Jina可以直接从一个简单的YAML配置中建立一个非常复杂的对象，并将对象保存到YAML配置中。

<br/><br/><br/><br/><br/><br/>

<h2 align="center">Executor</h2>

<img align="left" src="img/ILLUS3.png?raw=true" alt="Jina AI Executor, Copyright by Jina AI Limited" title="Jina AI Executor Concept, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Executor代表了Jina中的算法单元**。诸如将图像编码成向量、将向量存储在磁盘上、对结果进行排序等算法，都可以用Executor来表述。Executor提供了有用的接口，使AI开发者和工程师能够专注于算法。诸如持久性、调度、链式、分组和并行化等功能一应俱全。

Executor的属性存储在YAML配置中，它们总是齐头并进。

<br/><br/><br/><br/><br/><br/>

<h3 align="center">Family of Executors</h3>

<p align="center">
  <img src="img/ILLUS4.png?raw=true" alt="Jina 101 Family of Executor, Copyright by Jina AI Limited" title="Jina 101 Family of Executor, Copyright by Jina AI Limited" hspace="10" width="80%"/>
</p>

**Executor是一个大家庭**。每一个家庭成员都会集中在一个重要的方面进行搜索系统。让我们来认识一下。

-   **Crafter**：用于制作/分割/转换Document和Chunk。
-   **Encoder**：用于将Chunk表示为矢量。
-   **Indexer**：用于从存储中保存和检索向量和键值信息。
-   **Ranker**：用于对结果进行排序。

心中有了新的算法？没问题，这个家族随时欢迎新成员加入!

<br/><br/>

<h2 align="center">Driver</h2>

<img align="right" src="img/ILLUS5.png?raw=true" alt="Jina 101 Driver, Copyright by Jina AI Limited" title="Jina 101 Driver, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Driver定义了Executor在网络请求时的行为方式**。Driver通过将流量数据（如Protobuf）解释成Executor能够理解和处理的格式（如Numpy数组），帮助Executor处理网络流量。

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>

<h2 align="center">Pea</h2>

<img align="left" src="img/ILLUS6.png?raw=true" alt="Jina 101 Pea, Copyright by Jina AI Limited" title="Jina 101 Pea, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Pea包装一个Executor并授予其通过网络交换数据的能力**。Pea可以从其他Pea发送和接收数据。Pea也可以在Docker容器内运行，在一个地方包含所有的依赖关系和上下文环境。

<img align="right" src="img/ILLUS7.png?raw=true" alt="Jina 101 Pea, Copyright by Jina AI Limited" title="Jina 101 Pea, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>

<h2 align="center">Pod</h2>

<img align="left" src="img/ILLUS8.png?raw=true" alt="Jina 101 Pod, Copyright by Jina AI Limited" title="Jina 101 Pod, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Pod是一组具有相同属性的Peas**。Peas在一个Pod内部并行运行。Pod统一了这些Peas的网络接口，使它们从外部看起来就像一个个Pea。除此之外，Pod还为Peas增加了更多的控制、调度和上下文管理。

Pod既可以在本地主机上运行，也可以通过网络在不同的计算机上运行。

<img align="right" src="img/ILLUS9.png?raw=true" alt="Jina 101 Pod Remote, Copyright by Jina AI Limited" title="Jina 101 Pod Remote, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>

<h2 align="center">Flow</h2>

<img align="left" src="img/ILLUS10.png?raw=true" alt="Jina 101 Flow, Copyright by Jina AI Limited" title="Jina 101 Flow, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Flow代表了一项高级任务**, 例如，索引、搜索、训练。它管理一组Pods的状态和上下文，协调它们来完成一个任务。Flow拥抱了多样性，无论一个Pod是在远程还是在Docker容器中，一个Flow统治了所有的Pod!

<br/><br/><br/><br/><br/><br/><br/><br/><br/>

<h2 align="center">From Micro to Macro</h2>

Jina是一个幸福的家庭。当你使用Jina时，你可以感受到这种和谐。

你可以在微观层面进行设计，并将其扩展到宏观层面。YAML变成算法，线程变成进程，Pods变成流。模式和逻辑始终保持不变。这就是Jina的魅力所在。

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

本文（"Jina 101：了解Jina的第一件事"）的外观和感觉是Jina AI有限公司版权所有。保留所有权利。未经Jina AI有限公司明确的书面许可，客户不得复制、拷贝或重复使用任何部分的视觉设计元素或概念。
