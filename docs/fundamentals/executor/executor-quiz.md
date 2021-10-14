# Executor Quiz
<h2> 1. What does an Executor do? </h2>
<ul>
<p> <input type="checkbox"> An Executor is the tool you use to execute your Flow from the CLI: <code>execute jina_app.py</code>. </p>
<p> <input type="checkbox"> An Executor performs a single task on a <code>Document</code> or <code>DocumentArray</code>, like segmenting or encoding it. </p>
<p> <input type="checkbox"> An Executor is a processing pipeline for indexing or querying a dataset. </p>
</ul>
<details>
<summary>Reveal explanation</summary>
<p>
<p><a href="https://docs.jina.ai/fundamentals/executor/">An Executor</a> represents a processing component in a Jina Flow. It performs a single task on a <code>Document</code> or <code>DocumentArray</code>.</p>

</p>
</details>
<h2> 2. Which of the following usages of <code>requests</code> are valid? </h2>
<pre><code class="language-python">    @requests(on=&#39;/index&#39;)
    def foo(self, **kwargs):
        print(f&#39;foo is called: {kwargs}&#39;)
</code></pre>
<pre><code class="language-python">    @requests
    def foo(self, **kwargs):
        print(f&#39;foo is called: {kwargs}&#39;)
</code></pre>
<pre><code class="language-python">    @requests(&#39;/index&#39;)
    def foo(self, **kwargs):
        print(f&#39;foo is called: {kwargs}&#39;)
</code></pre>
<details>
<summary>Reveal explanation</summary>
<p>
<p><a href="https://docs.jina.ai/fundamentals/executor/executor-api/#method-decorator"><code>@requests</code></a> defines when a function will be invoked in the Flow. It has a keyword <code>on=</code> to define the endpoint.</p>

</p>
</details>
<h2> 3. What <strong>should</strong> an Executor method return? </h2>
<ul>
<p> <input type="checkbox"> Nothing. </p>
<p> <input type="checkbox"> It should yield the processed <code>Document</code>. </p>
<p> <input type="checkbox"> It should return the processed <code>DocumentArray</code>. </p>
<p> <input type="checkbox"> Whatever you like. </p>
</ul>
<details>
<summary>Reveal explanation</summary>
<p>
<p>Methods decorated with <code>@request</code> can <a href="https://docs.jina.ai/fundamentals/executor/executor-api/#method-returns">return <code>Optional[DocumentArray]</code></a>. The return is optional. <strong>All changes happen in-place</strong>.</p>

</p>
</details>
<h2> 4. Can you use an Executor outside of a Flow? </h2>
<ul>
<p> <input type="checkbox"> Yes, just like an ordinary Python object </p>
<p> <input type="checkbox"> Yes, but you need to use <code>jina.executor.load_executor</code> function </p>
<p> <input type="checkbox"> No </p>
</ul>
<details>
<summary>Reveal explanation</summary>
<p>
<p>An <code>Executor</code> object can be used directly <a href="https://docs.jina.ai/fundamentals/executor/executor-built-in-features/#use-executor-out-of-flow">just like a regular Python object</a>.</p>

</p>
</details>
<h2> 5. What formats are supported for creating Executors? </h2>
<ul>
<p> <input type="checkbox"> YAML </p>
<p> <input type="checkbox"> Python </p>
<p> <input type="checkbox"> JSON </p>
<p> <input type="checkbox"> JinaScript </p>
</ul>
<details>
<summary>Reveal explanation</summary>
<p>
<p>Besides building an Executor in Python, <a href="https://docs.jina.ai/fundamentals/executor/executor-built-in-features/#yaml-interface">an Executor can be loaded from and stored to a YAML file</a>. JinaScript is not a thing!</p>

</p>
</details>
<h2> 6. When creating an Executor with multiple Python files, how should it be organized? </h2>
<ul>
<p> <input type="checkbox"> As a zip file </p>
<p> <input type="checkbox"> Directly as a git repo </p>
<p> <input type="checkbox"> As a Python package in a git repo </p>
<p> <input type="checkbox"> Jina doesn&#39;t support multi-file Executors </p>
</ul>
<details>
<summary>Reveal explanation</summary>
<p>
<p>When you are working with multiple python files, <a href="https://docs.jina.ai/fundamentals/executor/repository-structure/">you should organize them as a Python package</a> and put them in a special folder inside your repository (as you would normally do with Python packages). </p>

</p>
</details>
<h2> 7. What&#39;s the recommended way to share Executors with a colleague? </h2>
<ul>
<p> <input type="checkbox"> Send them a link to the repo </p>
<p> <input type="checkbox"> Dockerize your Executor and push directly to Docker Hub </p>
<p> <input type="checkbox"> Push your Executor to Pypi and ask them to install via <code>pip</code> </p>
<p> <input type="checkbox"> Push your Executor to Jina Hub </p>
</ul>
<details>
<summary>Reveal explanation</summary>
<p>
<p>By using <a href="https://docs.jina.ai/advanced/hub/">Jina Hub</a> you can pull prebuilt Executors to dramatically reduce the effort and complexity needed in your search system, or push your own custom Executors to share privately or publicly.</p>

</p>
</details>
<h2> 8. How would you create a new Hub Executor from the CLI? </h2>
<ul>
<p> <input type="checkbox"> <code>jina hub create &lt;executor_name&gt;</code> </p>
<p> <input type="checkbox"> <code>jina hub new</code> </p>
<p> <input type="checkbox"> <code>cat executor.py | jina hub</code> </p>
</ul>
<details>
<summary>Reveal explanation</summary>
<p>
<p>Running <a href="https://docs.jina.ai/advanced/hub/create-hub-executor/#create-executor"><code>jina hub new</code></a> starts a wizard that will ask you some questions to build your Executor.</p>

</p>
</details>
<h2> 9. How would you use an Executor from Hub directly in your Python code? </h2>
<pre><code class="language-python">from jina import Flow

f = Flow().add(uses=&#39;jinahub+docker://executor_name&#39;)
</code></pre>
<pre><code class="language-python">from jina import Flow, Hub

executor = Hub.pull(&quot;executor_name&quot;)

f = Flow().add(uses=executor)
</code></pre>
<pre><code class="language-python">from jina import Flow

f = Flow().add(uses=executor, from=&quot;hub&quot;)
</code></pre>
<details>
<summary>Reveal explanation</summary>
<p>
<p>To <a href="https://docs.jina.ai/advanced/hub/use-hub-executor/">use an Executor from Hub</a> you need to use <code>.add(uses=jinahub+docker://executor_name)</code>.</p>

</p>
</details>
<h2> 10. How would you publish a <strong>private</strong> Executor? </h2>
<ul>
<p> <input type="checkbox"> <code>jina hub push --private &lt;path_to_executor_folder&gt;</code>. </p>
<p> <input type="checkbox"> <code>jina hub private push &lt;path_to_executor_folder&gt;</code>. </p>
<p> <input type="checkbox"> <code>jina hub push</code> then log in to Jina Hub front-end to set it as private. </p>
</ul>
<details>
<summary>Reveal explanation</summary>
<p>
<p>When <a href="https://docs.jina.ai/advanced/hub/push-executor/#publish-executor">publishing your Executor</a> you simply need to use the <code>--private</code> argument. Anyone who wants to use that Executor will need to know both the name and a <code>SECRET</code> hash.</p>

</p>
</details>
