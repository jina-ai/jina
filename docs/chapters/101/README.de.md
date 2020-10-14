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

In Jina,**ein Dokument ist alles, wonach Sie suchen möchten**: ein Textdokument, ein kurzer Tweet, ein Codeschnipsel, ein Bild, ein Video-/Audioclip, GPS-Spuren eines Tages usw. Ein Dokument ist auch die Eingabeanfrage bei der Suche.

**Ein Chunk ist eine kleine semantische Einheit eines Dokuments.** Es könnte ein Satz, ein 64x64-Bildfeld, ein 3-Sekunden-Videoclip, ein Koordinaten- und Adressenpaar sein

In Jina ist ein Dokument wie ein Schokoriegel. Nicht nur, weil es in verschiedenen Formaten und Zutaten erhältlich ist, sondern auch, weil man es nach Belieben in Stücke brechen kann. Was man schließlich kauft und lagert, sind die Schokoriegel, und was man isst und verdauen kann, sind die Stücke. Sie wollen nicht den ganzen Riegel schlucken, Sie wollen ihn auch nicht zu Pulver zermahlen; so oder so verlieren Sie den Geschmack (d.h. die Semantik).

<br/><br/><br/>

<h2 align="center">YAML config</h2>

<img align="right" src="img/ILLUS2.png?raw=true" alt="Jina 101 YAML, Copyright by Jina AI Limited" title="Jina 101 YAML Concept, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Eine YAML-Konfiguration wird in Jina häufig verwendet, um die Eigenschaften eines Objekts zu beschreiben.** Es bietet Anpassungsmöglichkeiten, so dass Benutzer das Verhalten eines Objekts ändern können, ohne seinen Code zu berühren. Jina kann ein sehr kompliziertes Objekt direkt aus einer einfachen YAML-Konfiguration erstellen und ein Objekt in einer YAML-Konfiguration speichern.

<br/><br/><br/><br/><br/><br/>

<h2 align="center">Executor</h2>

<img align="left" src="img/ILLUS3.png?raw=true" alt="Jina AI Executor, Copyright by Jina AI Limited" title="Jina AI Executor Concept, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Executor stellt eine algorithmische Einheit in Jina dar.** Algorithmen wie das Kodieren von Bildern in Vektoren, das Speichern von Vektoren auf der Platte, das Ranking der Ergebnisse, können alle als Executor formuliert werden. Executor bietet nützliche Schnittstellen, die es KI-Entwicklern und -Ingenieuren ermöglichen, sich auf den Algorithmus zu konzentrieren. Funktionen wie Persistenz, Planung, Verkettung, Gruppierung und Parallelisierung sind sofort einsatzbereit.

Die Eigenschaften eines EXECUTORs werden in einer YAML-Konfiguration gespeichert, sie gehen immer Hand in Hand.

<br/><br/><br/>

<h3 align="center">Family of Executors</h3>

<p align="center">
  <img src="img/ILLUS4.png?raw=true" alt="Jina 101 Family of Executor, Copyright by Jina AI Limited" title="Jina 101 Family of Executor, Copyright by Jina AI Limited" hspace="10" width="80%"/>
</p>

**Executor ist eine große Familie.** Jedes Familienmitglied konzentriert sich auf einen wichtigen Aspekt des Recherchensystems. Treffen wir uns:

-   **Crafter**: für die Herstellung/Segmentierung/Umwandlung des Dokuments und Chunk;
-   **Encoder**: zur Darstellung des Chunk als Vektor;
-   **Indexer**: zum Speichern und Abrufen von Vektoren und Schlüsselwert-Informationen aus dem Speicher;
-   **Ranker**: zum Sortieren der Ergebnisse;

Haben Sie einen neuen Algorithmus im Sinn? Kein Problem, diese Familie heißt neue Mitglieder immer willkommen!

<br/><br/>

<h2 align="center">Driver</h2>

<img align="right" src="img/ILLUS5.png?raw=true" alt="Jina 101 Driver, Copyright by Jina AI Limited" title="Jina 101 Driver, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Driver definiert, wie sich ein Executor bei Netzwerkanforderungen verhält.** Driver hilft dem Executor bei der Abwicklung des Netzwerkverkehrs, indem er die Verkehrsdaten (z.B. Protobuf) in ein Format interpretiert, das der Executor verstehen und verarbeiten kann (z.B. Numpy array).

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>

<h2 align="center">Pea</h2>

<img align="left" src="img/ILLUS6.png?raw=true" alt="Jina 101 Pea, Copyright by Jina AI Limited" title="Jina 101 Pea, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Pea umhüllt einen Executor und gewährt ihm die Fähigkeit, Daten über ein Netzwerk auszutauschen.** Die Pea kann Daten von anderen PEAs senden und empfangen. Die Pea kann auch innerhalb eines Docker-Containers laufen, der alle Abhängigkeiten und die kontextbezogene Umgebung an einem Ort enthält.

<img align="right" src="img/ILLUS7.png?raw=true" alt="Jina 101 Pea, Copyright by Jina AI Limited" title="Jina 101 Pea, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>

<h2 align="center">Pod</h2>

<img align="left" src="img/ILLUS8.png?raw=true" alt="Jina 101 Pod, Copyright by Jina AI Limited" title="Jina 101 Pod, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Pod ist eine Gruppe von Erbsen mit der gleichen Eigenschaft.** Erbsen laufen parallel in einem Pod. Pod vereinheitlicht die Netzwerkschnittstellen dieser PEAs, so dass sie von außen wie eine einzige Pea aussehen. Darüber hinaus verleiht ein Pod den Peas mehr Kontrolle, Zeitplanung und Kontextmanagement.

Pod kann entweder auf einem lokalen Host oder auf verschiedenen Computern über ein Netzwerk ausgeführt werden

<img align="right" src="img/ILLUS9.png?raw=true" alt="Jina 101 Pod Remote, Copyright by Jina AI Limited" title="Jina 101 Pod Remote, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>

<h2 align="center">Flow</h2>

<img align="left" src="img/ILLUS10.png?raw=true" alt="Jina 101 Flow, Copyright by Jina AI Limited" title="Jina 101 Flow, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Flow stellt eine hochrangige Aufgabe dar,** z.B. Indexierung, Suche, Schulung. Es verwaltet die Zustände und den Kontext einer Gruppe von Pods und orchestriert sie, um eine Aufgabe zu erfüllen. Flow umfasst die Vielfalt, unabhängig davon, ob sich ein Pod entfernt oder im Docker-Container befindet - ein Flow beherrscht sie alle!

<br/><br/><br/><br/><br/><br/>

<h2 align="center">From Micro to Macro</h2>

Jina ist eine glückliche Familie. Sie können die Harmonie spüren, wenn Sie Jina benutzen

Sie können auf der Mikroebene entwerfen und diese bis auf die Makroebene skalieren. Aus YAMLs werden Algorithmen, aus Threads werden Prozesse, aus Pods werden Flüsse. Die Muster und die Logik bleiben immer gleich. Das ist die Schönheit von Jina

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

Das Aussehen und die Gestaltung dieses Dokuments ("Jina 101: First Thing to Learn About Jina") ist urheberrechtlich geschützt © Jina AI Limited. Alle Rechte vorbehalten. Der Kunde darf ohne ausdrückliche schriftliche Genehmigung von Jina AI Limited keine Teile der visuellen Designelemente oder Konzepte vervielfältigen, kopieren oder wiederverwenden.
