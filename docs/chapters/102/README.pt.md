<table>
  <tr>
    <td width="70%"><h1>Jina 101: A primeira coisa para se aprender sobre Jina</h1>
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
  <a href="README.zh.md">中文</a> •
  <a href="README.ar.md">عربية</a>
    </td>
    <td>
      <img src="img/ILLUS12.png?raw=true" alt="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited" title="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited"/>
    </td>
  </tr>
</table>


<h2 align="center">Document & Chunk</h2>

<img align="left" src="img/ILLUS1.png?raw=true" alt="Jina 101 Concept Document and Chunk, Copyright by Jina AI Limited" title="Jina 101 Concept Document and Chunk, Copyright by Jina AI Limited" hspace="10" width="30%"/>


Em Jina, **um Document é qualquer coisa que você deseja procurar**: um documento de texto, um pequeno tweet, um trecho de código, uma imagem, um clipe de vídeo/áudio, rastreamentos GPS de um dia, etc. Um Document também é usado para se fazer uma pesquisar.

**Um Chunk é uma pequena unidade semântica de um Document.** Pode ser uma frase, um patch de imagem de 64x64, um videoclipe de 3 segundos ou um par de coordenadas e endereços.

Em Jina, um Document é como uma barra de chocolate. Não apenas porque ele vem em diferentes formatos e ingredientes, mas também porque você pode dividi-lo em pedaços da maneira que desejar. Eventualmente, o que você compra e armazena são as barras de chocolate e o que você come e digere são os pedaços. Você não quer engolir a barra inteira, também não deseja triturá-la em pó; de qualquer forma, você perderá o sabor (ou seja, a semântica).

<br/><br/><br/>


<h2 align="center">YAML config</h2>

<img align="right" src="img/ILLUS2.png?raw=true" alt="Jina 101 YAML, Copyright by Jina AI Limited" title="Jina 101 YAML Concept, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Um arquivo de configuração YAML é amplamente usada na Jina para descrever as propriedades de um objeto.** Ele oferece personalização, permitindo que os usuários alterem o comportamento de um objeto sem tocar em seu código. Jina pode criar um objeto muito complicado diretamente de uma configuração YAML simples, assim como salvar esse objeto em uma configuração YAML.

<br/><br/><br/><br/><br/><br/>

<h2 align="center">Executor</h2>

<img align="left" src="img/ILLUS3.png?raw=true" alt="Jina AI Executor, Copyright by Jina AI Limited" title="Jina AI Executor Concept, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**O Executor representa uma unidade algorítmica em Jina.** Algoritmos, como um para codificar imagens em vetores, ou armazenar vetores no disco, ou classificar resultados, podem ser todos formulados como Executores. O Executor fornece interfaces úteis que permitem que desenvolvedores e engenheiros de IA se concentrem no algoritmo. Recursos como persistência, programação, encadeamento, agrupamento e paralelização já são automaticamente fornecidos.

As propriedades de um Executor são armazenadas em uma configuração YAML, elas sempre andam de mãos dadas.

<br/><br/><br/>

<h3 align="center">Family of Executors</h3>


<p align="center">
  <img src="img/ILLUS4.png?raw=true" alt="Jina 101 Family of Executor, Copyright by Jina AI Limited" title="Jina 101 Family of Executor, Copyright by Jina AI Limited" hspace="10" width="80%"/>
</p>


**O Executor é uma grande família.** Cada membro da família se concentra em um aspecto importante do sistema de busca. Conhecam alguns membros dessa família:
- **Crafter**: para criar/segmentar/transformar os Documents e Chunks;
- **Encoder**: para representar um Chunk como vetor;
- **Indexador**: para salvar e recuperar vetores e informações sobre valores-chave do armazenamento;
- **Ranker**: para classificar os resultados;

Tem em mente um novo algoritmo? Não tem problema, essa família sempre recebe novos membros!

<br/><br/>

<h2 align="center">Driver</h2>

<img align="right" src="img/ILLUS5.png?raw=true" alt="Jina 101 Driver, Copyright by Jina AI Limited" title="Jina 101 Driver, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**O Driver define como o Executor se comporta em solicitações de rede.** O Driver ajuda o Executor a lidar com o tráfego de rede, interpretando os dados de tráfego (por exemplo, Protobuf) no formato que o Executor pode entender e processar (por exemplo, uma matriz em Numpy).

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>



<h2 align="center">Pea</h2>

<img align="left" src="img/ILLUS6.png?raw=true" alt="Jina 101 Pea, Copyright by Jina AI Limited" title="Jina 101 Pea, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**A Pea (ervilha) envolve um Executor e concede sua capacidade de trocar dados através de uma rede.** A Pea pode enviar e receber dados de outras Peas. A Pea também pode ser executado dentro de um contêiner de Docker, contendo todas as dependências e o ambiente contextual em um único local.

<img align="right" src="img/ILLUS7.png?raw=true" alt="Jina 101 Pea, Copyright by Jina AI Limited" title="Jina 101 Pea, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>

<h2 align="center">Pod</h2>

<img align="left" src="img/ILLUS8.png?raw=true" alt="Jina 101 Pod, Copyright by Jina AI Limited" title="Jina 101 Pod, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**O Pod é um grupo de Peas com a mesma propriedade.** As Peas são executadas em paralelo dentro de um Pod. O Pod unifica as interfaces de rede dessas Peas, fazendo com que pareçam uma única Pea do lado de fora. Além disso, um Pod adiciona mais controle, programação e gerenciamento de contexto às Peas.

O pod pode ser executado no host local ou em computadores diferentes de uma rede.

<img align="right" src="img/ILLUS9.png?raw=true" alt="Jina 101 Pod Remote, Copyright by Jina AI Limited" title="Jina 101 Pod Remote, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>

<h2 align="center">Flow</h2>


<img align="left" src="img/ILLUS10.png?raw=true" alt="Jina 101 Flow, Copyright by Jina AI Limited" title="Jina 101 Flow, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**O fluxo representa uma tarefa de alto nível**, como indexação, pesquisa and treinamento. Ele gerencia os estados e o contexto de um grupo de Pods, orquestrando-os para realizar uma tarefa. O Flow abraça a diversidade, seja um Pod remoto ou no contêiner do Docker, um Flow é quem manda!

<br/><br/><br/><br/><br/><br/>

<h2 align="center">From Micro to Macro</h2>

Jina é uma família feliz. Você pode sentir a harmonia ao usar Jina.

Você pode projetar no nível micro e dimensioná-lo até o nível macro. YAMLs tornam-se algoritmos, threads tornam-se processos, Pods tornam-se fluxos. Os padrões e a lógica sempre permanecem os mesmos. Esta é a beleza de Jina.

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


A aparência deste documento ("Jina 101: a primeira coisa a aprender sobre a Jina") é protegida por direitos autorais © Jina AI Limited. Todos os direitos reservados. Pessoas não podem duplicar, copiar ou reutilizar qualquer parte dos elementos ou conceitos do design visual sem a permissão expressa por escrito da Jina AI Limited.

