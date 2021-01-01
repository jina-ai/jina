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

В Jina, **ДОКУМЕНТ - это все, что вы хотите искать**: текстовый документ, короткий твиттер, фрагмент кода, изображение, видео-/аудиоклип, GPS-следы за день и т.д.. ДОКУМЕНТ - это также входной запрос при поиске.

**ЧАНК - это маленькая семантическая единица ДОКУМЕНТА.** Это может быть предложение, патч изображения 64x64, 3-х секундный видеоклип, пара координат и адрес

В Jina, ДОКУМЕНТ - это как шоколадная плитка. Не только потому, что она поставляется в разных форматах и с разными ингредиентами, но и потому, что вы можете разбить ее на куски так, как вам нравится. В конце концов, то, что вы покупаете и храните - это шоколадные плитки, а то, что вы едите и перевариваете - это куски. Вы не хотите проглотить всю плитку, вы также не хотите перемалывать ее в порошок; в любом случае вы потеряете вкус (т.е. семантический).

<br/><br/><br/>

<h2 align="center">YAML config</h2>

<img align="right" src="img/ILLUS2.png?raw=true" alt="Jina 101 YAML, Copyright by Jina AI Limited" title="Jina 101 YAML Concept, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**YAML-конфигурация широко используется в Jina для описания свойств объекта.** Он предлагает настройку, позволяющую пользователям изменять поведение объекта, не трогая его код. Jina может построить очень сложный объект непосредственно из простой YAML-конфигурации и сохранить объект в YAML-конфигурацию.

<br/><br/><br/><br/><br/><br/>

<h2 align="center">Executor</h2>

<img align="left" src="img/ILLUS3.png?raw=true" alt="Jina AI Executor, Copyright by Jina AI Limited" title="Jina AI Executor Concept, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Executor представляет собой алгоритмическую единицу в Jina.** Такие алгоритмы, как кодирование изображений в векторы, хранение векторов на диске, ранжирование результатов, могут быть сформулированы как Executor. Executor предоставляет полезные интерфейсы, позволяющие разработчикам ИИ и инженерам сконцентрироваться на алгоритме. Такие функции, как непрерывность, планирование, цепочка, группировка и распараллеливание выходят из коробки.

Свойства Executor хранятся в конфигурации YAML, они всегда идут рука об руку.

<br/><br/><br/>

<h3 align="center">Family of Executors</h3>

<p align="center">
  <img src="img/ILLUS4.png?raw=true" alt="Jina 101 Family of Executor, Copyright by Jina AI Limited" title="Jina 101 Family of Executor, Copyright by Jina AI Limited" hspace="10" width="80%"/>
</p>

**Executor - большая семья.** Каждый член семьи фокусируется на одном важном аспекте поисковой системы. Давайте встретимся:

-   **Crafter**: для изготовления/сегментации/трансформирования ДОКУМЕНТА и ЧАНКА;
-   **Encoder**за представление ЧАНКа в качестве вектора;
-   **Indexer**для сохранения и извлечения из хранилища векторной информации и информации о значении ключа;
-   **Ranker**для сортировки результатов;

Имеешь в виду новый алгоритм? Нет проблем, эта семья всегда рада новым членам!

<br/><br/>

<h2 align="center">Driver</h2>

<img align="right" src="img/ILLUS5.png?raw=true" alt="Jina 101 Driver, Copyright by Jina AI Limited" title="Jina 101 Driver, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Driver определяет, как Executor ведет себя при сетевых запросах.** Driver помогает ПОЛЬЗОВАТЕЛЮ обрабатывать сетевой трафик, интерпретируя данные о трафике (например, Protobuf) в формат, который понимает и обрабатывает ПОЛЬЗОВАТЕЛЬ (например, массив Numpy).

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>

<h2 align="center">Pea</h2>

<img align="left" src="img/ILLUS6.png?raw=true" alt="Jina 101 Pea, Copyright by Jina AI Limited" title="Jina 101 Pea, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Pea обертывает Executor и предоставляет ему возможность обмениваться данными по сети.** Pea может отправлять и получать данные от других Pea. Pea также может работать внутри контейнера Docker, содержащего все зависимости и контекстную среду в одном месте.

<img align="right" src="img/ILLUS7.png?raw=true" alt="Jina 101 Pea, Copyright by Jina AI Limited" title="Jina 101 Pea, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>

<h2 align="center">Pod</h2>

<img align="left" src="img/ILLUS8.png?raw=true" alt="Jina 101 Pod, Copyright by Jina AI Limited" title="Jina 101 Pod, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Pod - это группа Peas с одним и тем же свойством.** Peas работают параллельно внутри Pod. Pod унифицирует сетевые интерфейсы этих Peas, делая их похожими на один Pea снаружи. Кроме того, Pod добавляет больше контроля, планирования и управления контекстом в Peas.

Pod может быть запущен как на локальном хосте, так и на разных компьютерах по сети

<img align="right" src="img/ILLUS9.png?raw=true" alt="Jina 101 Pod Remote, Copyright by Jina AI Limited" title="Jina 101 Pod Remote, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>

<h2 align="center">Flow</h2>

<img align="left" src="img/ILLUS10.png?raw=true" alt="Jina 101 Flow, Copyright by Jina AI Limited" title="Jina 101 Flow, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Flow представляет собой задачу высокого уровня**например, индексирование, поиск, обучение. Он управляет состояниями и контекстом группы Pods, организуя их для выполнения одной задачи. Flow включает в себя разнообразие, независимо от того, является ли Pod удаленной или находится в контейнере Docker, один Flow управляет ими всеми!

<br/><br/><br/><br/><br/><br/>

<h2 align="center">From Micro to Macro</h2>

Jina - счастливая семья. Вы можете почувствовать гармонию, когда используете Jina

Вы можете проектировать на микроуровне и масштабировать его до макроуровня. YAML становятся алгоритмами, потоки - процессами, Pods - потоками. Шаблоны и логика всегда остаются неизменными. В этом вся прелесть Jina

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

Внешний вид этого документа ("Jina 101: First Thing to Learn About Jina") защищен авторским правом © Jina AI Limited. Все права защищены. Клиент не имеет права дублировать, копировать или повторно использовать любую часть элементов или концепций визуального дизайна без письменного разрешения Jina AI Limited.
