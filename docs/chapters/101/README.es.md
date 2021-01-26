<table>
  <tr>
    <td width="70%"><h1>Jina 101: Lo primero que tienes que aprender sobre Jina</h1>
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
  <a href="README.ar.md">عربية</a> •
  <a href="README.es.md">Español</a>
    </td>
    <td>
      <img src="img/ILLUS12.png?raw=true" alt="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited" title="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited"/>
    </td>
  </tr>
</table>

¿Quiere una introducción general a la búsqueda neuronal y en qué se diferencia de la búsqueda simbólica normal? [Consulte nuestra publicación](https://medium.com/@jina_ai/what-is-jina-and-neural-search-7a9e166608ab) para aprender más!

<h2 align="center">Document y Chunk</h2>

<img align="left" src="img/ILLUS1.png?raw=true" alt="Jina 101 Concept Document and Chunk, Copyright by Jina AI Limited" title="Jina 101 Concept Document and Chunk, Copyright by Jina AI Limited" hspace="10" width="30%"/>

Cuando la gente piensa en búsqueda, la mayoría piensa en una barra en la que se escriben palabras, como Google. Pero la búsqueda es mucho más que eso: además de texto, es posible que desee buscar una canción, receta, video, secuencia genética, artículo científico o ubicación.

En Jina, llamamos a todas estas cosas **Documents**. En resumen, un documento es cualquier cosa que desee buscar así como la consulta de entrada que utiliza al realizar la búsqueda.

Sin embargo, los documentos pueden ser enormes, ¿cómo podemos buscar la parte correcta? Hacemos esto dividiendo un documento en **Chunks**. Un Chunk es un fragmento, una pequeña unidad semántica de un documento, como una oración, un parche de imagen de 64x64 píxeles o un par de coordenadas.

Puede pensar en un documento como una barra de chocolate. Los documentos tienen diferentes formatos e ingredientes, pero también puede dividirlos en trozos como desee. Con el tiempo, lo que compra y almacena son las barras de chocolate, y lo que come y digiere son los trozos. No quiere comerse toda la barra, pero tampoco quiere molerla hasta convertirla en polvo. Al hacer eso, pierde el sabor (es decir, la semántica).

<br/><br/><br/>

<h2 align="center">YAML Config</h2>

<img align="right" src="img/ILLUS2.png?raw=true" alt="Jina 101 YAML, Copyright by Jina AI Limited" title="Jina 101 YAML Concept, Copyright by Jina AI Limited" hspace="10" width="30%"/>

Cada parte de Jina está configurada con **archivos YAML**. Los archivos YAML ofrecen personalización, lo que le permite cambiar el comportamiento de un objeto sin tocar su código. Jina puede construir un objeto complejo directamente desde un archivo YAML y/o guardar un objeto en un archivo YAML.

<br/><br/><br/><br/><br/><br/>

<h2 align="center">Executors</h2>

<img align="left" src="img/ILLUS3.png?raw=true" alt="Jina AI Executor, Copyright by Jina AI Limited" title="Jina AI Executor Concept, Copyright by Jina AI Limited" hspace="10" width="30%"/>

¿Cómo dividimos un documento en chunks (fragmentos) y qué sucede a continuación? Los **Executors** hacen todo este trabajo duro, cada Executor representa una unidad algorítmica. Hacen cosas como codificar imágenes en vectores, almacenar vectores en disco, rankear los resultados, etc. Cada uno tiene una interfaz simple, lo que le permite concentrarse en el algoritmo y no perderse en la maleza. Manejan la persistencia, planificación, encadenamiento, agrupación y paralelización de funciones de forma inmediata. Las propiedades de un Executor se almacenan en un archivo YAML. Siempre van de la mano.

<br/><br/><br/>

<h3 align="center">The Executor Family</h3>


<p align="center">
  <img src="img/ILLUS4.png?raw=true" alt="Jina 101 Family of Executor, Copyright by Jina AI Limited" title="Jina 101 Family of Executor, Copyright by Jina AI Limited" hspace="10" width="80%"/>
</p>

Los **Executors** son una gran familia. Cada integrante de la familia se centra en un aspecto importante del sistema de búsqueda:

- **Crafter**: para crear/segmentar/transformar los Documents y Chunks;
- **Encoder**: para representar el Chunk como vector;
- **Indexer**: para guardar y recuperar vectores e información de valor-clave del almacenamiento;
- **Ranker**: para ordenar y ranquear los resultados;

¿Tiene un nuevo algoritmo en mente? No hay problema, ¡esta familia siempre da la bienvenida a nuevos integrantes!

<br/><br/>

<h2 align="center">Drivers</h2>

<img align="right" src="img/ILLUS5.png?raw=true" alt="Jina 101 Driver, Copyright by Jina AI Limited" title="Jina 101 Driver, Copyright by Jina AI Limited" hspace="10" width="30%"/>

Los Executors hacen todo el trabajo duro, pero no son buenos para hablarse entre ellos. Un **Driver** les ayuda a hacer esto definiendo cómo se comporta un Executor ante las peticiones de red. Interpreta el tráfico de la red en un formato que el Executor puede entender, por ejemplo, traduciendo un Protobuf en un arreglo NumPy.

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>



<h2 align="center">Peas</h2>

<img align="left" src="img/ILLUS6.png?raw=true" alt="Jina 101 Pea, Copyright by Jina AI Limited" title="Jina 101 Pea, Copyright by Jina AI Limited" hspace="10" width="30%"/>

Todas las familias saludables necesitan comunicarse, y el clan Executor no es diferente. Se hablan a través de **Peas**.

Mientras que un Driver traduce datos para un Executor, un Pea envuelve a un Executor y le permite intercambiar datos a través de una red o con otros Peas. Los Peas también se pueden ejecutar en Docker, conteniendo todas las dependencias y el contexto en un solo lugar.

<img align="right" src="img/ILLUS7.png?raw=true" alt="Jina 101 Pea, Copyright by Jina AI Limited" title="Jina 101 Pea, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>



<h2 align="center">Pods</h2>

<img align="left" src="img/ILLUS8.png?raw=true" alt="Jina 101 Pod, Copyright by Jina AI Limited" title="Jina 101 Pod, Copyright by Jina AI Limited" hspace="10" width="30%"/>

Así que ahora tienes muchos Peas hablando entre ellos y rodando por todos lados. ¿Cómo puedes organizarlos? Usamos **Pods** al igual que la naturaleza.

Un Pod es un grupo de Peas con la misma propiedad que se ejecuta en paralelo en un host local o en la red. Un Pod proporciona una interfaz única de red para sus Peas, lo que los hace parecer un solo Pea desde el exterior. Más allá de eso, un Pod agrega mayor control, planeación y administración de contexto a los Peas.


<img align="right" src="img/ILLUS9.png?raw=true" alt="Jina 101 Pod Remote, Copyright by Jina AI Limited" title="Jina 101 Pod Remote, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>

<h2 align="center">Flow</h2>


<img align="left" src="img/ILLUS10.png?raw=true" alt="Jina 101 Flow, Copyright by Jina AI Limited" title="Jina 101 Flow, Copyright by Jina AI Limited" hspace="10" width="30%"/>


Ahora tenemos un jardín lleno de Pods, con cada Pod llena de Peas. ¡Eso es mucho para administrar! ¡Te introducimos a **Flow**! Flow es como una planta de Peas. Así como una planta gestiona el flujo de nutrientes y la tasa de crecimiento de sus ramas, Flow gestiona los estados y el contexto de un grupo de Pods.

El Flow representa una tarea de alto nivel. Por ejemplo, indexación, búsqueda y entrenamiento. Gestiona los estados y el contexto de un grupo de Pods y los organiza para realizar una tarea.
Ya sea que un Pod sea remoto o se esté ejecutando en Docker, ¡un Flow los gobierna a todos!


<br/><br/><br/><br/><br/><br/>



<h2 align="center">De Micro a Macro</h2>


Jina es una familia feliz. Puede sentir la armonía cuando usa Jina.

Puede diseñar a nivel micro y escalar al nivel macro. Los YAML se convierten en algoritmos, los hilos se convierten en procesos, los Pods se convierten en Flows. Los patrones y la lógica siempre son los mismos. Esa es la belleza de Jina.


<p align="center">
  <img src="img/ILLUS11.png?raw=true" alt="Jina 101 All Characters, Copyright by Jina AI Limited" title="Jina 101 All Characters, Copyright by Jina AI Limited" hspace="10" width="80%"/>
</p>

<br/><br/><br/><br/>

<p align="center">
<a href="../../../README.md#jina-hello-world-">
    ✨<b> ¿Le intriga? Pruebe nuestro "Hola, Mundo!" y construya su buscador de imágenes neuronales en 1 minuto. </b>
</a>
</p>
<br><br><br>
<p align="center">
    ✨<b> ¡Desata tu curiosidad y feliz búsqueda! </b>🔍
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



La apariencia de este documento ("Jina 101: Lo primero que debe aprender sobre Jina") está protegida por derechos de autor © Jina AI Limited. Todos los derechos reservados. Clientes no pueden duplicar, copiar ni reutilizar ninguna parte de los elementos o conceptos de diseño visual sin el permiso expreso por escrito de Jina AI Limited.