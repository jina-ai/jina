<table>
  <tr>
    <td width="70%"><h1>Jina 101: Τα πρώτα πράγματα για να μάθετε σχετικά με το Jina</h1>
    <a href="https://twitter.com/intent/tweet?text=%F0%9F%91%8DCheck+out+Jina%3A+the+New+Open-Source+Solution+for+Neural+Information+Retrieval+%F0%9F%94%8D%40JinaAI_&url=https%3A%2F%2Fgithub.com%2Fjina-ai%2Fjina&hashtags=JinaSearch&original_referer=http%3A%2F%2Fgithub.com%2F&tw_p=tweetbutton" target="_blank">
  <img src="../../../.github/badges/twitter-share101.svg?raw=true"
       alt="tweet button" title="👍Δείτε το Jina: Την νέα ανοιχτού-κώδικα λύση για ανάκτηση πληροφοριών με την χρήση Νευρωνικών Δικτύων 🔍@JinaAI_"></img>
</a>
  <a href="../../../README.md#jina-hello-world-">
    <img src="../../../.github/badges/jina-hello-world-badge.svg?raw=true" alt="Τρέξτε το Jina Hello World">
</a>

<a href="https://docs.jina.ai">
    <img src="../../../.github/badges/docs-badge.svg?raw=true" alt="Διαβάστε όλο το doumentation">
</a>
<a href="https://github.com/jina-ai/jina/">
    <img src="../../../.github/badges/jina-badge.svg?raw=true" alt="Επισκευθείτε το Jina στο Github">
</a>
<a href="https://jobs.jina.ai">
    <img src="../../../.github/badges/jina-corp-badge-hiring.svg?raw=true" alt="Δείτε jobs@Jina AI">
</a>
    <a href="#">
    <img src="../../../.github/badges/pdf-badge.svg?raw=true" alt="Κατεβάστε την PDF έκδοση του Jina 101">
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
  <a href="README.gr.md">Ελληνικά</a>
    </td>
    <td>
      <img src="img/ILLUS12.png?raw=true" alt="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited" title="Jina 101 Concept Illustration Book, Copyright by Jina AI Limited"/>
    </td>
  </tr>
</table>

Θέλετε μια γενική εισαγωγή σχετικά με την νευρωνική αναζήτηση και για πώς το πως διαφέρει από την συμβατική παλιά συμβολική αναζήτηση; [Δείτε αυτό το επεξηγηματικό άρθρο](https://medium.com/@jina_ai/what-is-jina-and-neural-search-7a9e166608ab) και μάθετε περισσότερα!

<h2 align="center">Document & Chunks (Έγγραφο & Τμήματα)</h2>

<img align="left" src="img/ILLUS1.png?raw=true" alt="Jina 101 Concept Document and Chunk, Copyright by Jina AI Limited" title="Jina 101 Concept Document and Chunk, Copyright by Jina AI Limited" hspace="10" width="30%"/>

Οι περισσότεροι άνθρωποι, όταν σκέφτονται περι αναζήτησης, φαντάζονται μια μπάρα σαν αυτήν της Google, στην οποία γράφεις μέσα κείμενο. Αλλά ο όρος αναζήτηση είναι πολύ περισσότερα από αυτό - εκτός από το κείμενο, μπορεί να θέλεις να αναζητήσεις ένα τραγούδι, μια συνταγή, ένα βίντεο, μια γενετική ακολουθία, ένα επιστημονικό άρθρο ή μια τοποθεσία.

Στην Jina, ονομάζουμε άυτά τα αντικείμενα **Documents**. Συνοπτικά, ένα Document είναι οτιδήποτε θέλετε να αναζητήσετε, και το ερώτημα (μτφ. query) που χρησιμοποιείτε ως είσοδο στην αναζήτηση.

Ωστόσο, τα έγγραφα μπορεί να είναι τεράστια - πως μπορούμε να ψάξουμε για το σωστό μέρος του? Το κάνουμε αυτό χωρίζοντας το έγραφο σε **Chunks**. Ένα Chunk είναι ένα μικρό συμβολικό μέρος του Εγγράφου, όπως μια πρόσταση, ένα απόσπασμα εικόνας 64x64 pixel, ή ένα ζευγάρι συντεταγμένων.

Μπορείτε να φανταστείτε το Document ως μια σοκολάτα. Τα έγγραφα έχουν διαφορετική μορφή και αποτελούνται από διαφορετικά υλικά, αλλά ωστόσο μπορείτε να τα διαχωρίσετε σε επιμέρους Chunks με όποιον τρόπο θέλετε. Αυτό που τελικά αγοράζετε είναι μια σοκολάτα αλλά αυτό που καταναλώνετε και χωνεύετε είναι τα Chunks αυτής. Δεν θα θέλατε να καταπιείτε μονομιάς ολόκληρη την μπάρα, αλλά ούτε θα θέλατε να την αλέσετε σε σκόνη; Κάνοντας το αυτό, θα χάνατε την γεύση (δηλ. τα semantics)

<br/><br/><br/>

<h2 align="center">YAML Config</h2>

<img align="right" src="img/ILLUS2.png?raw=true" alt="Jina 101 YAML, Copyright by Jina AI Limited" title="Jina 101 YAML Concept, Copyright by Jina AI Limited" hspace="10" width="30%"/>

Κάθε μέρος του Jina ρυθμίζεται μέσω των **αρχείων YAML**. Τα αρχεία YAML προσφέρουν την δυνατότητα προσαρμογής, επιτρέποντας σας έτσι να αλλάξετε την συμπεριφορά ενός αντικειμένου δίχως να αγγίξετε τον κώδικα του. Το Jina μπορεί να δημιουργήσει ένα πολύ περίπλοκο αντικείμενο κατευθείαν με την χρήση ενός απλού αρχείου YAML, ή ακόμα και να σώσει το εκάστοτε αντικείμενο σε ένα αρχείο YAML. 

<br/><br/><br/><br/><br/><br/>

<h2 align="center">Executors (Εκτελεστές)</h2>

<img align="left" src="img/ILLUS3.png?raw=true" alt="Jina AI Executor, Copyright by Jina AI Limited" title="Jina AI Executor Concept, Copyright by Jina AI Limited" hspace="10" width="30%"/>

Πως διαχωρίζουμε το Document σε Chunks, και τι συμβαίνει στην συνέχεια; Οι **Executors** κάνουν όλη αυτήν την δύσκολη εργασία, και κάθε ένας τους εκπροσωπεί μια αλγοριθμική μονάδα. Κάνουν πράγματα όπως η κωδικοποίηση εικόνων σε διανύσματα, αποθήκευση των διανυσμάτων στον δίσκο, κατάταξη των αποτελεσμάτων, κτλ. Καθένας του έχει μια πολύ απλή διεπαφή, παρέχοντας σας έτσι την δυνατότητα να συγκεντρωθείτε στον αλγόριθμο, αντί να χαθείτε στο δάσος. Χειρίζονται το persistance των χαρακτηριστικών, τον προγραμματισμό (scheduling), την αλυσίδωση (chaining), την ομαδοποίηση και την παραλληλοποίηση από προεπιλογή. Οι ιδιότητες ενός Εκτελεστή αποθηκεύονται σε ένα [Αρχείο YAML](#configuring-jina-with-yaml). Τα δυό τους πάνε πάντα χέρι χέρι

<br/><br/><br/>

<h3 align="center">Η οικογένεια των Executors</h3>


<p align="center">
  <img src="img/ILLUS4.png?raw=true" alt="Jina 101 Family of Executor, Copyright by Jina AI Limited" title="Jina 101 Family of Executor, Copyright by Jina AI Limited" hspace="10" width="80%"/>
</p>

Οι **Executors** είναι μια μεγάλη οικογένια. 
The **Executors** are a big family. Κάθε μέλος της οικογένειας επικεντρώνεται σε κάποια σημαντική πτυχή του συστήματος αναζήτησης. Ας γνωρίσουμε τα μέλη:
- **Crafter**: για την οικοδόμηση/τμηματοποίηση/μετασχηματικό των Εγγράφων σε Chunks;
- **Encoder**: για την μετατροπή του εκάστοτε Chunkτος σε διάνυσμα;
- **Indexer**: για την αποθήκευση και την ανάκτηση διανυσμάτων και πληροφορίες κλειδί-τιμή από τον αποθηκευτικό χώρο;
- **Ranker**: για την ταξινόμηση των αποτελεσμάτων;

Έχετε κάποιον νεο αλγόριθμο κατά νου; Κανένα πρόβλημα, η οικογένεια κάνει πάντα ευπρόσδεκτα τα νέα μέλη!

<br/><br/>

<h2 align="center">Drivers (Οδηγοί)</h2>

<img align="right" src="img/ILLUS5.png?raw=true" alt="Jina 101 Driver, Copyright by Jina AI Limited" title="Jina 101 Driver, Copyright by Jina AI Limited" hspace="10" width="30%"/>

Οι Executors κάνουν όλη την δύσκολια εργασία, αλλά δεν μπορούν να επικοινωνήσουν μεταξύ τους. Οι **Drivers** τους βοηθούν στην επικοινωνία ορίζοντας πως ένας Executor ανταποκρίνεται στα αιτήματα από το δίκτυο.

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>


<h2 align="center">Peas (Σπόροι των φασολιών)</h2>

<img align="left" src="img/ILLUS6.png?raw=true" alt="Jina 101 Pea, Copyright by Jina AI Limited" title="Jina 101 Pea, Copyright by Jina AI Limited" hspace="10" width="30%"/>

Όλες οι υγιείς οικογένεις χρειάζεται να επικοινωνούν και αυτό ισχύει και για την οικογένεια των Executor. Μιλούν μεταξύ τους μέσω των **Peas**.

Ενώ οι Drivers μεταφράζουν τα δεδομένα για τους Executors, τα Peas ενσωματώνονται στους Executors και τους επιτρέπουν να ανταλλάζουν μεταξύ τους δεδομένα μέσω του δικτύου επικοινωνόντας με άλλα Peas ενσωματωμένα σε άλλους ελεγκτές. Τα Peas μπορούν επίσης να τρέξουν πάνω σε Docker, εμπεριέχοντας έτσι όλες τις εξαρτήσεις (dependencies) και το context σε ένα μέρος.

<img align="right" src="img/ILLUS7.png?raw=true" alt="Jina 101 Pea, Copyright by Jina AI Limited" title="Jina 101 Pea, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>



<h2 align="center">Pods (Φασόλια)</h2>

<img align="left" src="img/ILLUS8.png?raw=true" alt="Jina 101 Pod, Copyright by Jina AI Limited" title="Jina 101 Pod, Copyright by Jina AI Limited" hspace="10" width="30%"/>

Οπότε, έχετε μέχρι στιγμής, πολλά Peas τα οποία μιλούν το ένα με το άλλο και κυλιούνται στον χώρο. Πως μπορούμε όμως να τα οργανώσουμε? Η φύση χρησιμοποιεί τα **Pods** έτσι και εμείς.

Ένα Pod είναι μια ομάδα από Peas με την ίδια ιδιότητα, τρέχουν παράλληλα στον local hostή στο δίκτυο. Ένα Pod παρέχει μια διεπαφή δικτύου για τα Peas, κάνοντας τα έτσι να φαίνονται (παρατηρώντας από έξω) ως μονάδα. Πέρα από αυτό, ένα Pod προσθέτει επιπλέον έλεγχο, προγραμματισμό και διαχείριση του context στα Peas.

<img align="right" src="img/ILLUS9.png?raw=true" alt="Jina 101 Pod Remote, Copyright by Jina AI Limited" title="Jina 101 Pod Remote, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>

<h2 align="center">Flow</h2>


<img align="left" src="img/ILLUS10.png?raw=true" alt="Jina 101 Flow, Copyright by Jina AI Limited" title="Jina 101 Flow, Copyright by Jina AI Limited" hspace="10" width="30%"/>


Έχουμε λοιπόν πλεον έναν κήπο γεμάτο με Pods και κάθε Pod είναι γεμάτο από Peas. Πολύ πράγμα για διαχείριση! Ας καλωσορίσουμε το **Flow**! Το Flow είναι σαν μια φασολιά. Όπως η φασολιά φροντίζει την θρέψη και τον ρυθμό ανάπτυξης των κλαδιών της, έτσι και το Flow φροντίζει τις καταστάσεις (μτφ states) και το context μιας ομάδας από φασόλια, οργανώνοντας
Now we've got a garden full of Pods, with each Pod full of Peas. That's a lot to manage! Say hello to **Flow**! Flow is like a Pea plant. Just as a plant manages nutrient flow and growth rate for its branches, Flow manages the states and context of a group of Pods, οργανώνοντας τα να πετύχουν ένα έργο. Είτε το φασόλι είναι απομακρυσμένο (μτφ. remote) είναι τρέχει τοπικά σε ένα Docker, ένα Flow αρκεί για να τα οργανώσει όλα! h
<br/><br/><br/><br/><br/><br/>



<h2 align="center">From Micro to Macro</h2>

Η Jina είναι μια χαρούμενη οικογένεια. Μπορείς να νιώσεις την αρμονία όταν χρησημοποιείς την Jina.

Μπορείς να σχεδιάσεις σε micro-επίπεδο και να αναβαθμίσεις σε macro-επίπεδο. Τα YAMLs γίνονται αλγόριθμοι, τα threads γίνονται διεργασίες, τα Pods γίνονται Flows. Τα μοτίβα και η λογική όμως πάντα μένουν ίδια. 
ΑΥτή είναι η ομορφιά της Jina


<p align="center">
  <img src="img/ILLUS11.png?raw=true" alt="Jina 101 All Characters, Copyright by Jina AI Limited" title="Jina 101 All Characters, Copyright by Jina AI Limited" hspace="10" width="80%"/>
</p>

<br/><br/><br/><br/>

<p align="center">
<a href="../../../README.md#jina-hello-world-">
    ✨<b>Ενθουσιαστήκατε? Δοκιμάστε το "Hello, World!" μας και χτίστε την δική σας νευρωνική αναζήτηση σε μόλις 1 λεπτό </b>
</a>
</p>
<br><br><br>
<p align="center">
    ✨<b>Αφήστε ελεύθερη την περιέργεια σας και καλή αναζήτηση!</b>🔍
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



Η όψη και η αίσθηση αυτού του εγγράφου ("Jina 101: First Things to Learn About Jina") αποτελεί πνευματική ιδιοκτησία του οργανισμού © Jina AI Limited. Όλα τα δικαιώματα προστατεύονται. Δεν επιτρέπεται η αντιγραφή, ή επανάχρηση οποιοδήποτε μέρους των γραφικών στοιχείων ή ιδεών χωρίς την ρητή γραπτή άδεια από την Jina AI Limited.

