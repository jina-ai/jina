<p align="center">
  <img src=".github/1500х667.gif?raw=true" alt="Jina banner">
</p>

<p align="center">
 
[![Jina](.github/badges/jina-badge.svg "We fully commit to open-source")](https://jina.ai)
[![Jina](.github/badges/jina-hello-world-badge.svg "Run Jina 'Hello, World!' without installing anything")](#jina-hello-world-)
[![Jina](.github/badges/license-badge.svg "Jina is licensed under Apache-2.0")](#license)
[![Jina Docs](.github/badges/docs-badge.svg "Checkout our docs and learn Jina")](https://docs.jina.ai)
[![We are hiring](.github/badges/jina-corp-badge-hiring.svg "We are hiring full-time position at Jina")](https://jina.ai/jobs)
<a href="https://twitter.com/intent/tweet?text=%F0%9F%91%8DCheck+out+Jina%3A+the+New+Open-Source+Solution+for+Neural+Information+Retrieval+%F0%9F%94%8D%40JinaAI_&url=https%3A%2F%2Fgithub.com%2Fjina-ai%2Fjina&hashtags=JinaSearch&original_referer=http%3A%2F%2Fgithub.com%2F&tw_p=tweetbutton" target="_blank">
  <img src=".github/badges/twitter-badge.svg"
       alt="tweet button" title="👍Share Jina with your friends on Twitter"></img>
</a>
[![Python 3.7 3.8](.github/badges/python-badge.svg "Jina supports Python 3.7 and above")](#)
[![Docker](.github/badges/docker-badge.svg "Jina is multi-arch ready, can run on differnt architectures")](https://hub.docker.com/r/jinaai/jina/tags)
[![CI](https://github.com/jina-ai/jina/workflows/CI/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3ACI)
[![CD](https://github.com/jina-ai/jina/workflows/CD/badge.svg?branch=master)](https://github.com/jina-ai/jina/actions?query=workflow%3ACD)
[![Release Cycle](https://github.com/jina-ai/jina/workflows/Release%20Cycle/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3A%22Release+Cycle%22)
[![Release CD](https://github.com/jina-ai/jina/workflows/Release%20CD/badge.svg)](https://github.com/jina-ai/jina/actions?query=workflow%3A%22Release+CD%22)

</p>

<p align="center">
  <a href="https://jina.ai">English</a> •
  <a href="">日本語</a> •
  <a href="">français</a> •
  <a href="">Русский язык</a> •
  <a href="">中文</a>
</p>


<p align="center">
  <a href="https://jina.ai">Website</a> •
  <a href="https://docs.jina.ai">Docs</a> •
  <a href="https://docs.jina.ai">Examples</a> •
  <a href="mailto:newsletter+subscribe@jina.ai">Newsletter</a> •
  <a href="https://github.com/jina-ai/jina-hub">Hub (beta)</a> •
  <a href="https://board.jina.ai">Dashboard (beta)</a> •
  <a href="https://twitter.com/intent/tweet?text=%F0%9F%91%8DCheck+out+Jina%3A+the+New+Open-Source+Solution+for+Neural+Information+Retrieval+%F0%9F%94%8D%40JinaAI_&url=https%3A%2F%2Fgithub.com%2Fjina-ai%2Fjina&hashtags=JinaSearch&original_referer=http%3A%2F%2Fgithub.com%2F&tw_p=tweetbutton">Twitter</a> •
  <a href="https://jina.ai/jobs">We are Hiring</a> •
  <a href="https://jina.ai/events">Events</a> •
  <a href="https://blog.jina.ai">Blog</a>
</p>

想建立一个以深度学习为支撑的搜索系统？你来对地方了!

**Jina**是由最先进的AI和深度学习驱动的云原生神经搜索框架。它由一个全职的[风险投资团队](https://jina.ai)提供**长期支持。

智慧搜索解决方案

**🌌 通用搜索解决方案**--Jina可以在多个平台和架构上实现任何类型的大规模索引和查询。无论您是搜索图片、视频片段、音频片段、长的法律文档、短的推文，Jina都能处理。

**🚀高性能和最新技术** - Jina的目标是AI-in-production。您可以轻松扩展出VideoBERT、Xception、您最爱的词法分析器、亦或是图像语义分割和数据库，以处理亿级数据。复制品和碎片等功能都是现成的。

**🐣系统工程轻松搞定** - Jina提供了一个一站式的解决方案，让你从手工制作和粘包、库和数据库中解脱出来。通过最直观的API和【dashboard UI】(https://github.com/jina-ai/dashboard)，构建一个云端搜索系统只是分分钟的事情。

**🧩强大的扩展性、简单的集成性**--全新的AI模型为Jina? 只需编写一个Python脚本或构建一个Docker镜像即可。插入新的算法从来都不是那么容易的事情。查看[Jina Hub (beta)](https://github.com/jina-ai/jina-hub)，找到更多由社区贡献的不同用例的扩展。

Jina是一个开源项目。我们正在招聘](https://jina.ai/jobs)AI工程师、全栈开发者、布道者、PM，以构建**下一个开源的神经搜索生态系统。


## Contents

<img align="right" width="350px" src="./.github/install.png" />

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [Install](#install)
- [Jina "Hello, World!" 👋🌍](#jina-hello-world-)
- [Getting Started](#getting-started)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [Community](#community)
- [Roadmap](#roadmap)
- [License](#license)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

##  安装

#### 从PyPi安装
 
在安装了 Python >= 3.7 的 Linux/MacOS 上，只需在终端上运行此命令即可。

```bash
pip install jina
```

要在Raspberry Pi上安装Jina，请参考文档。

#### ...或使用Docker容器运行 

我们提供了一个通用的Jina图像（只有80MB！），支持多种架构（包括x64、x86、x86、arm-64/v7/v6），简单的说就是：

```bash
docker run jinaai/jina
```

## Jina "Hello, World!" 👋🌍

作为入门者，您可以尝试一下Jina的 "Hello，World"--简单的图像神经搜索[FASHION-MNIST](https://hanxiao.io/2018/09/28/Fashion-MNIST-Year-In-Review/)的简单演示。不需要额外的依赖，只需做：

```bash
jina hello-world
```

....或者对于Docker用户来说更简单，*不需要任何安装，只需：

```bash
docker run -v "$(PWD)/j:/j" jinaai/jina hello-world --workdir /j && open j/hello-world.html
```

<details>
<summary>点击这里查看控制台输出</summary>

<p align="center">
  <img src="docs/chapters/helloworld/hello-world-demo.png?raw=true" alt="hello world console output">
</p>

</details>  

它下载了Fashi-MNIST训练和测试数据，并告诉Jina从训练集中*索引*6万张图像。然后，它从测试集中随机抽取图像作为*查询*，要求Jina检索相关结果。大约1分钟后，它将打开一个网页，显示出这样的结果：

<p align="center">
  <img src="docs/chapters/helloworld/hello-world.gif?raw=true" alt="Jina banner" width="90%">
</p>

那背后的实施呢？就像它应该是很简单的：

<table>
<tr>
<td> Python API </td>
<td> index.yml</td>
<td> <a href="https://github.com/jina-ai/dashboard">Flow in Dashboard</a></td>
</tr>
<tr>
<td> 

  
```python
from jina.flow import Flow

f = Flow.load_config('index.yml')

with f:
    f.index(raw_bytes=input_fn)
```

</td>
<td>
  <sub>

```yaml
!Flow
pods:
  chunk_seg:
    yaml_path: helloworld.crafter.yml
    replicas: $REPLICAS
    read_only: true
  doc_idx:
    yaml_path: helloworld.indexer.doc.yml
  encode:
    yaml_path: helloworld.encoder.yml
    needs: chunk_seg
    replicas: $REPLICAS
  chunk_idx:
    yaml_path: helloworld.indexer.chunk.yml
    replicas: $SHARDS
    separated_workspace: true
  join_all:
    yaml_path: _merge
    needs: [doc_idx, chunk_idx]
    read_only: true
```
</sub>

</td>
<td>

![Flow in Dashboard](docs/chapters/helloworld/hello-world-flow.png)

</td>
</tr>
</table>



所有你能说出名字的大词：计算机视觉、神经IR、微服务、消息队列、弹性、复制&碎片，在短短一分钟内就发生了！你想知道吗？

感兴趣了？通过不同的选项玩一玩：

```bash
jina hello-world --help
```

请务必继续关注我们的[Jina 101指南](https://github.com/jina-ai/jina#jina-101-first-thing-to-learn-about-jina)--3分钟内了解Jina的所有关键概念!  


## 开始

<table>
  <tr>
      <td width="30%">
    <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101">
      <img src="docs/chapters/101/img/ILLUS12.png" alt="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited" title="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited"/>
    </a>
    </td>
    <td width="70%">
&nbsp;&nbsp;<h3><a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101">Jina 101: 学习Jina的第一件事</a></h3>
&nbsp;&nbsp;<a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101">English</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.jp.md">日本語</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.fr.md">français</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.ru.md">Русский язык</a> •
  <a href="https://github.com/jina-ai/jina/tree/master/docs/chapters/101/README.cn.md">中文</a>
    </td>

  </tr>
</table>

<table>
<tr><th width="90%">Tutorials</th><th width="10%">Level</th></tr><tr>

<tr>
<td>
<h4><a href="https://docs.jina.ai/chapters/flow/README.html">Use Flow API to 编写您的搜索工作流程</a></h4>
学会如何协调Pods一起工作：按顺序和并行、本地和远程工作
</td>
<td><h3>🐣</h3></td>
</tr>

<tr>
<td>
<h4><a href="https://github.com/jina-ai/dashboard">使用仪表板了解Jina工作流的情况</a></h4>
学会使用仪表板来监控和了解运行中的工作流程
</td>
<td><h3>🐣</h3></td>
</tr>

<tr>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/x-as-service">From BERT-as-Service to X-as-Service</a></h4>
学习如何使用Jina使用任何深度学习表示法提取特征向量
</td>
<td><h3>🐣</h3></td>
</tr>

<tr>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/southpark-search">构建NLP语义搜索系统</a></h4>
学习如何构建南方公园的脚本搜索系统，练习Flows和Pods的相关知识
</td>
<td><h3>🐣</h3></td>
</tr>

<tr>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/flower-search">构建花卉图片搜索系统</a></h4>
学习如何构建一个图像搜索系统，以及如何定义自己的执行器并在docker中运行。
</td>
<td><h3>🐣</h3></td>
</tr>

<tr>
<td>
<h4><a href="https://github.com/jina-ai/examples/tree/master/tumblr-gif-search">使用预取和分片的视频语义搜索技术进行规模化搜索</a></h4>
学习如何通过使用预取和分片来提高性能
</td>
<td><h3>🕊</h3></td>
</tr>

<tr>
<td>
<h4><a href="https://docs.jina.ai/chapters/remote/main.html">远程分发您的工作流程</a></h4>
学会在远程实例上运行Jina并分发工作流程
</td>
<td><h3>🕊</h3></td>
</tr>


<tr>
<td>
<h4><a href="https://docs.jina.ai/chapters/extend/executor.html">通过实施自己的执行者扩展Jina</a></h4>
学习如何在Jina的插件中实现自己的想法
</td>
<td><h3>🕊</h3></td>
</tr>


<tr>
<td>
<h4><a href="https://docs.jina.ai/chapters/hub/main.html">通过Docker容器运行Jina Pod</a></h4>
学习Jina如何利用Docker容器轻松解决复杂的依赖关系
</td>
<td><h3>🕊</h3></td>
</tr>

<tr>
<td>
<h4><a href="https://github.com/jina-ai/jina-hub#publish-your-pod-image-to-jina-hub">与世界分享您的推广活动</a></h4>
学习使用Jina Hub并与全球各地的工程师分享您的扩展功能
</td>
<td><h3>🚀</h3></td>
</tr>

</table>
  

## 文档 

<a href="https://docs.jina.ai/">
<img align="right" width="350px" src="./.github/jina-docs.png" />
</a>

要深入学习Jina，最好的方法就是阅读我们的文档。文档建立在主分支的每个推送、合并和发布事件上。你可以在我们的文档中找到关于以下主题的更多细节。

- [Jina command line interface arguments explained](https://docs.jina.ai/chapters/cli/main.html)
- [Jina Python API interface](https://docs.jina.ai/api/jina.html)
- [Jina YAML syntax for executor, driver and flow](https://docs.jina.ai/chapters/yaml/yaml.html)
- [Jina Protobuf schema](https://docs.jina.ai/chapters/proto/main.html)
- [Environment variables used in Jina](https://docs.jina.ai/chapters/envs.html)
- ... [and more](https://docs.jina.ai/index.html)

你是Doc明星吗？那就加入我们吧! 我们欢迎大家对文档进行各种改进。

旧版本的文件[在这里存档](https://github.com/jina-ai/docs/releases)。

## 贡献者

我们欢迎来自开源社区、个人和合作伙伴的各种贡献。没有你的积极参与，Jina就不可能成功。

下面的资源可以帮助你做好第一个贡献：

- [Contributing guidelines](CONTRIBUTING.md)
- [Release cycles and development stages](RELEASE.md)

## 社区

- [Slack chanel](https://join.slack.com/t/jina-ai/shared_invite/zt-dkl7x8p0-rVCv~3Fdc3~Dpwx7T7XG8w) - 一个供开发者讨论Jina的交流平台
- [Community newsletter](mailto:newsletter+subscribe@jina.ai) - 订阅Jina的最新更新、发布和活动信息
- [LinkedIn](https://www.linkedin.com/company/jinaai/) - 了解Jina AI作为一家公司
- ![Twitter Follow](https://img.shields.io/twitter/follow/JinaAI_?label=Follow%20%40JinaAI_&style=social) - 关注我们并使用hashtag `#JinaSearch`与我们互动  
- [Join Us](mailto:hr@jina.ai) - 想在Jina全职工作吗？我们正在招聘!
- [Company](https://jina.ai) - 了解更多关于我们公司的信息，我们完全致力于开源!

## 路线图

[GitHub的里程碑](https://github.com/jina-ai/jina/milestones)列出了未来的改进路径。

我们正在寻找合作伙伴，围绕Jina建立一个开放的治理模式（如技术指导委员会），以建立一个健康的开源生态系统和开发者友好的文化。如果您有兴趣参与其中，请随时联系我们[hello@jina.ai](mailto:hello@jina.ai)。


## 许可证

Copyright (c) 2020 Jina AI Limited. All rights reserved.

Jina is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for the full license text.
