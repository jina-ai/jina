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

Jinaで。**a Documentは、あなたが検索したいものです**。テキスト文書、短いつぶやき、コードスニペット、画像、ビデオ/オーディオクリップ、一日のGPSトレースなど。ドキュメントは検索時の入力クエリでもあります。

**ChunkはDocumentの小さな意味単位です**。文章にしても、64x64の画像パッチにしても、3秒のビデオクリップにしても、座標とアドレスのペアにしてもいい。

JinaでいうところのDocumentはチョコレートバーのようなもの。形や材料が違うだけでなく、自分の好きなようにチャンクに割ることができるからです。結局、買って保存するものがチョコバーで、食べて消化するものがチャンクということになる。バー全体を飲み込むのは嫌だし、粉にするのも嫌だし、どちらにしても味（つまり意味）を失うことになります。

<br/><br/><br/>

<h2 align="center">YAML config</h2>

<img align="right" src="img/ILLUS2.png?raw=true" alt="Jina 101 YAML, Copyright by Jina AI Limited" title="Jina 101 YAML Concept, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**YAML設定はオブジェクトのプロパティを記述するためにJinaで広く使われています**。それはカスタマイズを提供し、ユーザーがそのコードに触れることなくオブジェクトの動作を変更することを可能にします。Jinaは単純なYAML設定から直接非常に複雑なオブジェクトを構築し、YAML設定にオブジェクトを保存することができます。

<br/><br/><br/><br/><br/><br/>

<h2 align="center">Executor</h2>

<img align="left" src="img/ILLUS3.png?raw=true" alt="Jina AI Executor, Copyright by Jina AI Limited" title="Jina AI Executor Concept, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**ExecutorはJinaのアルゴリズム単位を表します**。画像をベクターにエンコードする、ベクターをディスクに格納する、結果をランキングするなどのアルゴリズムは、すべてExecutorとして定式化することができます。Executorは便利なインターフェースを提供し、AI開発者やエンジニアがアルゴリズムに集中できるようにします。永続性、スケジューリング、チェーニング、グループ化、並列化などの機能は、その場から出てきます。

ExecutorのプロパティはYAMLの設定に保存されます。

<br/><br/><br/>

<h3 align="center">Family of Executors</h3>

<p align="center">
  <img src="img/ILLUS4.png?raw=true" alt="Jina 101 Family of Executor, Copyright by Jina AI Limited" title="Jina 101 Family of Executor, Copyright by Jina AI Limited" hspace="10" width="80%"/>
</p>

**Executorは大家族です**。家族それぞれが検索システムの重要な一面に焦点を当てています。会ってみましょう

-   **Crafter**DocumentとChunkをクラフト/セグメント/変換するためのものです。
-   **Encoder**: Chunkをベクトルで表現する。
-   **Indexer**: ベクトルやキー値の情報を保存したり取得したりするためのものです。
-   **Ranker**: 結果をソートするために使用します。

新しいアルゴリズムを考えていますか？問題ありません、このファミリーは常に新しいメンバーを歓迎します!

<br/><br/>

<h2 align="center">Driver</h2>

<img align="right" src="img/ILLUS5.png?raw=true" alt="Jina 101 Driver, Copyright by Jina AI Limited" title="Jina 101 Driver, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Driver は、ネットワーク要求に対して Executor がどのように振る舞うかを定義します**。Driverは、トラフィックデータ(Protobufなど)をExecutorが理解して処理できる形式(Numpy配列など)に解釈することで、Executorがネットワークトラフィックを処理するのに役立ちます。

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>

<h2 align="center">Pea</h2>

<img align="left" src="img/ILLUS6.png?raw=true" alt="Jina 101 Pea, Copyright by Jina AI Limited" title="Jina 101 Pea, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**PeaはExecutorをラップし、ネットワークを介してデータを交換する能力を付与します**。Peaは他のPeaとデータを送受信することができます。また、PeaはDockerコンテナ内で実行することができ、すべての依存関係とコンテキスト環境を一箇所に格納します。

<img align="right" src="img/ILLUS7.png?raw=true" alt="Jina 101 Pea, Copyright by Jina AI Limited" title="Jina 101 Pea, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>

<h2 align="center">Pod</h2>

<img align="left" src="img/ILLUS8.png?raw=true" alt="Jina 101 Pod, Copyright by Jina AI Limited" title="Jina 101 Pod, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Podは、同じ性質を持つPeasのグループです**。Peas は Pod 内で並列に動作しています。Pod は、それらの Peas のネットワークインターフェースを統一し、外から見ると 1 つの Pea に見えるようにします。それ以上に、Pod は Peas に制御、スケジューリング、コンテキスト管理を追加します。

Podは、ローカルホストまたはネットワーク上の異なるコンピュータのいずれかで実行することができます。

<img align="right" src="img/ILLUS9.png?raw=true" alt="Jina 101 Pod Remote, Copyright by Jina AI Limited" title="Jina 101 Pod Remote, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>

<h2 align="center">Flow</h2>

<img align="left" src="img/ILLUS10.png?raw=true" alt="Jina 101 Flow, Copyright by Jina AI Limited" title="Jina 101 Flow, Copyright by Jina AI Limited" hspace="10" width="30%"/>

**Flowは高レベルのタスクを表します**。例えば、インデックス作成、検索、トレーニングなどです。FlowはPodsのグループの状態とコンテキストを管理し、一つのタスクを達成するためにそれらをオーケストレーションします。Flowは多様性を受け入れ、PodがリモートであろうとDockerコンテナ内であろうと、1つのFlowがすべてを支配します。

<br/><br/><br/><br/><br/><br/>

<h2 align="center">From Micro to Macro</h2>

Jinaは幸せな家族です。Jinaを使うと和を感じることができます。

ミクロレベルで設計し、マクロレベルまでスケールアップすることができます。YAMLはアルゴリズムになり、スレッドはプロセスになり、Podsはフローになります。パターンとロジックは常に同じままです。これがJinaの良さです。

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

本文書（「Jina 101：Jinaについて学ぶための最初のこと」）の外観と使用感は、著作権 © Jina AI Limited.すべての著作権はJina AI Limitedに帰属します。お客様は、Jina AI Limitedの書面による明示的な許可なしに、ビジュアルデザインの要素やコンセプトのいかなる部分も複製、コピー、再利用することはできません。
