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

En Jina,**un Document est tout ce que vous voulez rechercher**un document texte, un court tweet, un extrait de code, une image, un clip vidéo/audio, les traces GPS d'une journée, etc. Un Document est également la requête de saisie lors d'une recherche.

**Un Chunk est une petite unité sémantique d'un Document.** Il peut s'agir d'une phrase, d'un patch d'image 64x64, d'un clip vidéo de 3 secondes, d'une paire de coordonnées et d'une adresse

En Jina, un Document est comme une barre de chocolat. Non seulement parce qu'il se présente sous différents formats et ingrédients, mais aussi parce que vous pouvez le casser en morceaux comme vous le souhaitez. En fin de compte, ce que vous achetez et stockez, ce sont les barres de chocolat, et ce que vous mangez et digérez, ce sont les morceaux. Vous ne voulez pas avaler la barre entière, vous ne voulez pas non plus la moudre en poudre; de toute façon, vous perdrez la saveur (c'est-à-dire la sémantique).

<br/><br/><br/>

<h2 align="center">YAML config</h2>

<img align="right" src="img/ILLUS2.png?raw=true" alt="Jina 101 YAML, Copyright by Jina AI Limited" title="Jina 101 YAML Concept, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Une configuration YAML est largement utilisée dans la Jina pour décrire les propriétés d'un objet.** Il offre une personnalisation, permettant aux utilisateurs de modifier le comportement d'un objet sans toucher à son code. Jina peut construire un objet très compliqué directement à partir d'une simple config YAML, et enregistrer un objet dans une config YAML.

<br/><br/><br/><br/><br/><br/>

<h2 align="center">Executor</h2>

<img align="left" src="img/ILLUS3.png?raw=true" alt="Jina AI Executor, Copyright by Jina AI Limited" title="Jina AI Executor Concept, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Executor représente une unité algorithmique dans Jina.** Les algorithmes tels que l'encodage des images en vecteurs, le stockage des vecteurs sur le disque, le classement des résultats, peuvent tous être formulés comme Executor. Executor fournit des interfaces utiles, permettant aux développeurs et aux ingénieurs en IA de se concentrer sur l'algorithme. Des fonctionnalités telles que la persistance, l'ordonnancement, le chaînage, le regroupement et la parallélisation sortent de l'ordinaire.

Les propriétés d'un Executor sont stockées dans une configuration YAML, elles vont toujours de pair.

<br/><br/><br/>

<h3 align="center">Family of Executors</h3>

<p align="center">
  <img src="img/ILLUS4.png?raw=true" alt="Jina 101 Family of Executor, Copyright by Jina AI Limited" title="Jina 101 Family of Executor, Copyright by Jina AI Limited" hspace="10" width="80%"/>
</p>

**Executor est une grande famille.** Chaque membre de la famille se concentre sur un aspect important du système de recherche. Rencontrons-nous :

-   **Crafter**pour l'élaboration/la segmentation/la transformation du Document et du Chunk ;
-   **Encoder**pour représenter le Chunk en tant que vecteur ;
-   **Indexer**pour la sauvegarde et la récupération de vecteurs et d'informations clés du stockage ;
-   **Ranker**pour le tri des résultats ;

Vous avez un nouvel algorithme en tête ? Pas de problème, cette famille accueille toujours de nouveaux membres !

<br/><br/>

<h2 align="center">Driver</h2>

<img align="right" src="img/ILLUS5.png?raw=true" alt="Jina 101 Driver, Copyright by Jina AI Limited" title="Jina 101 Driver, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Driver définit la manière dont un Executor se comporte sur les demandes du réseau.** Driver aide l'Executor à gérer le trafic réseau en interprétant les données de trafic (par exemple Protobuf) dans un format que l'Executor peut comprendre et traiter (par exemple Numpy array).

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>

<h2 align="center">Pea</h2>

<img align="left" src="img/ILLUS6.png?raw=true" alt="Jina 101 Pea, Copyright by Jina AI Limited" title="Jina 101 Pea, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Le Pea enveloppe un Executor et lui accorde la possibilité d'échanger des données sur un réseau.** Les Pea peuvent envoyer et recevoir des données d'autres Pea. Les Pea peuvent également fonctionner à l'intérieur d'un conteneur Docker, contenant toutes les dépendances et l'environnement contextuel en un seul endroit.

<img align="right" src="img/ILLUS7.png?raw=true" alt="Jina 101 Pea, Copyright by Jina AI Limited" title="Jina 101 Pea, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>

<h2 align="center">Pod</h2>

<img align="left" src="img/ILLUS8.png?raw=true" alt="Jina 101 Pod, Copyright by Jina AI Limited" title="Jina 101 Pod, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Pod est un groupe de Peas ayant la même propriété.** Les Peas fonctionnent en parallèle à l'intérieur d'un Pod. Le Pod unifie les interfaces réseau de ces Peas, les faisant ressembler à un seul Pea de l'extérieur. Au-delà de cela, un Pod ajoute au Peas plus de contrôle, de planification et de gestion du contexte.

Le Pod peut être exécuté soit sur un hôte local, soit sur des ordinateurs différents via un réseau

<img align="right" src="img/ILLUS9.png?raw=true" alt="Jina 101 Pod Remote, Copyright by Jina AI Limited" title="Jina 101 Pod Remote, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>

<h2 align="center">Flow</h2>

<img align="left" src="img/ILLUS10.png?raw=true" alt="Jina 101 Flow, Copyright by Jina AI Limited" title="Jina 101 Flow, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Flow représente une tâche de haut niveau**par exemple, l'indexation, la recherche, la formation. Il gère les états et le contexte d'un groupe de Pods, en les orchestrant pour accomplir une tâche. Flow embrasse la diversité, qu'un Pod soit à distance ou dans le conteneur Docker, un Flow les dirige tous !

<br/><br/><br/><br/><br/><br/>

<h2 align="center">From Micro to Macro</h2>

La Jina est une famille heureuse. Vous pouvez sentir l'harmonie quand vous utilisez Jina

Vous pouvez concevoir au niveau micro et à l'échelle jusqu'au niveau macro. Les YAML deviennent des algorithmes, les threads des processus, les Pods des flux. Les modèles et la logique restent toujours les mêmes. C'est là toute la beauté de Jina

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

L'aspect et la convivialité de ce document ("Jina 101 : First Thing to Learn About Jina") sont protégés par le droit d'auteur © Jina AI Limited. Tous droits réservés. Le client ne peut pas dupliquer, copier ou réutiliser toute partie des éléments ou concepts de la conception visuelle sans l'autorisation écrite expresse de Jina AI Limited.
