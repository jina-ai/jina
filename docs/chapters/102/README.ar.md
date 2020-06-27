
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

في جينا ، المستند هو كل ما تريد البحث عنه **مستند نصي ، تغريدة قصيرة ، مقتطف برمجية ، صورة ، مقطع فيديو / صوت ، مسارات  ليوم واحد ، إلخ.   المستند هو أيضًا طلب الدخول أثناء البحث.**

 **القطعة عبارة عن وحدة دلالية صغيرة للمستند**  يمكن أن تكون جملة أو رقعة صورة بحجم 64 × 64 أو مقطع فيديو مدته 3 ثوانٍ أو زوج من الإحداثيات وعنوان

في جينا ، يشبه المستند شريط الشوكولاتة. ليس فقط لأنه يأتي بتنسيقات ومكونات مختلفة ، ولكن أيضًا لأنه يمكنك تقسيمه إلى أجزاء بالطريقة التي تريدها. في النهاية ، ما تشتريه وتخزنه هو ألواح الشوكولاتة ، وما تأكله وتهضمه هو القطع. لا تريد ابتلاع  ألواح بالكامل ، ولا تريد طحنها إلى مسحوق ؛ في كلتا الحالتين ، ستفقد النكهة أي دلالاتها

<br/><br/><br/>

<h2 align="center">YAML config</h2>

<img align="right" src="img/ILLUS2.png?raw=true" alt="Jina 101 YAML, Copyright by Jina AI Limited" title="Jina 101 YAML Concept, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<cite dir="rtl">
يتم استخدام برمجية YAML على نطاق واسع في جينا لوصف خصائص كائن.  يوفرYAML  التخصيص ، مما يسمح للمستخدمين بتعديل سلوك كائن دون لمس رمزه. يمكن لـ Jina بناء كائن معقد جدًا مباشرة من برنامج YAML بسيط ، وحفظ كائن في برنامج YAML.</cite>


<br/><br/><br/><br/><br/><br/>

<h2 align="center">Executor</h2>

<img align="left" src="img/ILLUS3.png?raw=true" alt="Jina AI Executor, Copyright by Jina AI Limited" title="Jina AI Executor Concept, Copyright by Jina AI Limited" hspace="10" width="30%"/>


يمثل المنفذ وحدة خوارزمية في جينا. يمكن صياغة خوارزميات مثل ترميز الصور في المتجهات ، وتخزين المتجهات على القرص ، وترتيب النتائج ، كمنفذ. يوفر المنفذ واجهات مفيدة ، مما يسمح للمطورين ومهندسي الذكاء الاصطناعي بالتركيز على الخوارزمية. ميزات مثل المثابرة ، والجدولة ، والتسلسل ، والتجميع ، والتوازي غير عادية.

<cite dir="rtl">  يتم تخزين خصائص المنفذ في برنامج YAML ، وهي دائمًا تسير جنبًا إلى جنب.</cite>


<br/><br/><br/>

<h3 align="center">Family of Executors</h3>

<p align="center">
  <img src="img/ILLUS4.png?raw=true" alt="Jina 101 Family of Executor, Copyright by Jina AI Limited" title="Jina 101 Family of Executor, Copyright by Jina AI Limited" hspace="10" width="80%"/>
</p>

<cite dir="rtl"> **منفذ Executor  هو عائلة كبيرة** . يركز كل فرد من أفراد الأسرة على جانب مهم من نظام البحث. دعنا نلتقي :</cite>
<cite dir="rtl">

-  لتطوير / تجزئة / تحويل الوثيقة والمقطع؛  **Crafter**
-  لتمثيل القطعة كمتجه ؛ **Encoder**
-  للنسخ الاحتياطي واستعادة المتجهات والمعلومات الرئيسية من التخزين ؛ **Indexer**
-  لفرز النتائج ؛ **Ranker**</cite>


هل لديك خوارزمية جديدة في الاعتبار؟ لا مشكلة ، هذه العائلة ترحب دائما بالأعضاء الجدد!

<br/><br/>

<h2 align="center">Driver</h2>

<img align="right" src="img/ILLUS5.png?raw=true" alt="Jina 101 Driver, Copyright by Jina AI Limited" title="Jina 101 Driver, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<cite dir="rtl">
 يحدد برنامج التشغيل Driver  كيف يتصرف المنفذ Executor  وفقًا لطلبات الشبكة.  يساعد برنامج التشغيل المنفذ   على إدارة حركة مرور الشبكة من خلال تفسير بيانات حركة المرور (مثل Protobuf) بصيغة يمكن للمنفذ فهمها و استغلالها (على سبيل المثال  Numpy array).</cite>

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>

<h2 align="center">Pea</h2>

<img align="left" src="img/ILLUS6.png?raw=true" alt="Jina 101 Pea, Copyright by Jina AI Limited" title="Jina 101 Pea, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<cite dir="rtl">
يحيط البازلاء  Pea منفذاً ويمنحه إمكانية تبادل البيانات عبر شبكة. يمكن للبازلاء إرسال واستقبال البيانات من البازلاء الأخرى. يمكن أن تعمل البازلاء أيضًا داخل حاوية Docker ، تحتوي على جميع التبعيات والبيئة السياقية في مكان واحد.
</cite>

<img align="right" src="img/ILLUS7.png?raw=true" alt="Jina 101 Pea, Copyright by Jina AI Limited" title="Jina 101 Pea, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>

<h2 align="center">Pod</h2>

<img align="left" src="img/ILLUS8.png?raw=true" alt="Jina 101 Pod, Copyright by Jina AI Limited" title="Jina 101 Pod, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<cite dir="rtl">
** Pod هي مجموعة من البازلاء لها نفس الخاصية. ** تعمل البازلاء بالتوازي داخل Pod. يعمل Pod على توحيد واجهات الشبكة لهذه البازلاء ، مما يجعلها تبدو كبازلاء واحدة من الخارج. أبعد من ذلك ، يضيف Pod المزيد من التحكم والتخطيط وإدارة السياق إلى البازلاء.</cite>

<cite dir="rtl">يمكن تشغيل Pod إما على مضيف محلي أو على أجهزة كمبيوتر مختلفة عبر شبكة</cite>


<img align="right" src="img/ILLUS9.png?raw=true" alt="Jina 101 Pod Remote, Copyright by Jina AI Limited" title="Jina 101 Pod Remote, Copyright by Jina AI Limited" hspace="10" width="30%"/>

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>

<h2 align="center">Flow</h2>

<img align="left" src="img/ILLUS10.png?raw=true" alt="Jina 101 Flow, Copyright by Jina AI Limited" title="Jina 101 Flow, Copyright by Jina AI Limited" hspace="10" width="30%"/>
<cite dir="rtl">
 يمثل التدفقflow  مهمة عالية المستوى  على سبيل المثال ، الفهرسة والبحث والتدريب. يدير الحالات والسياق لمجموعة من Pods ، وينظمها لإنجاز مهمة. التدفق يحتضن التنوع ، سواء كان الPod بعيدًا أو في حاوية Docker ، فإن التدفق يوجههم جميعًا!
</cite>
<br/><br/><br/><br/><br/><br/>

<h2 align="center">From Micro to Macro</h2>


جينا هي عائلة سعيدة. يمكنك أن تشعر بالانسجام عند استخدام جينا

<cite dir="rtl">يمكنك التصميم على المستوى الجزئي والارتقاء إلى المستوى الكلي. YAMLs تصبح خوارزميات ، خيوط العمليات ، حاضنات الجداول.لكن تبقى النماذج والمنطق كما هو دائما. هذا هو جمال جينا
</cite>

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

<cite dir="rtl">مظهر هذا المستند وسهولة استخدامه ("Jina 101: First Thing to Learn About Jina") محمي بحقوق الطبع والنشر © Jina AI Limited. جميع الحقوق محفوظة. لا يجوز للعميل نسخ أو نسخ أو إعادة استخدام أي جزء من عناصر أو مفاهيم التصميم المرئي دون الحصول على إذن كتابي صريح من شركة Jina AI Limited.</cite>
