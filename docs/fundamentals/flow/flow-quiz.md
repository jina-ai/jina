# Flow Quiz
<h2> 1. What does a Flow do? </h2>
<ul>
<p> <input type="checkbox"> The <code>Flow</code> ties Executors together into a processing pipeline to perform a bigger task, like indexing or querying a dataset. </p>
<p> <input type="checkbox"> The <code>Flow</code> is a graphical interface that lets users see how their <code>Documents</code> are flowing into the processing pipeline. </p>
<p> <input type="checkbox"> The <code>Flow</code> is short for &quot;fast, low-resource&quot; and is a special kind of Executor for low-powered machines. </p>
</ul>
<details>
<summary>Reveal explanation</summary>
<p>
<p><a href="https://docs.jina.ai/fundamentals/flow/">The <code>Flow</code> ties Executors together into a processing pipeline to perform a bigger task, like indexing or querying a dataset</a>. Documents &quot;flow&quot; through the created pipeline and are processed by Executors.</p>

</p>
</details>
<h2> 2. What languages can you use to create a Flow? </h2>
<ul>
<p> <input type="checkbox"> Python directly </p>
<p> <input type="checkbox"> YAML </p>
<p> <input type="checkbox"> JSON </p>
<p> <input type="checkbox"> From the command line with <code>jina flow new</code> </p>
</ul>
<details>
<summary>Reveal explanation</summary>
<p>
<p>Jina supports <a href="https://docs.jina.ai/fundamentals/flow/#minimum-working-example">creating Flows in both YAML and directly in Python</a></p>

</p>
</details>
<h2> 3. How would you create and run a Flow? </h2>
<pre><code class="language-python">from jina import Flow

flow = Flow()

with flow:
   flow.index()
</code></pre>
<pre><code class="language-python">from jina import Flow

flow = Flow()
flow.index()
</code></pre>
<pre><code class="language-python">from jina import Flow

Flow.index()
</code></pre>
<details>
<summary>Reveal explanation</summary>
<p>
<p>To use <code>flow</code>, <a href="https://docs.jina.ai/fundamentals/flow/flow-api/#use-a-flow">always open it as a context manager, just like you open a file</a>. This is considered the best practice in Jina.</p>

</p>
</details>
<h2> 4. What are some valid ways to index a dataset? </h2>
<pre><code class="language-python">with flow:
  flow.index()
</code></pre>
<pre><code class="language-python">with flow:
  flow.post(&#39;/index&#39;)
</code></pre>
<pre><code>with flow:
  flow.post(task=&#39;index&#39;)
</code></pre>
<details>
<summary>Reveal explanation</summary>
<p>
<p><code>.post()</code> is the core method for <a href="https://docs.jina.ai/fundamentals/flow/send-recv/">sending data to a <code>Flow</code> object</a>, it provides multiple callbacks for fetching results from the Flow. You can also use CRUD methods (<code>index</code>, <code>search</code>, <code>update</code>, <code>delete</code>) which are just sugary syntax of <code>post</code>
with <code>on=&#39;/index&#39;</code> , <code>on=&#39;/search&#39;</code>, etc.</p>

</p>
</details>
<h2> 5. How do you add an Executor to a Flow? </h2>
<pre><code class="language-python">from jina import Flow, Executor

class MyExecutor(Executor):
    ...


f = Flow().add(uses=MyExecutor)
</code></pre>
<pre><code class="language-python">from jina import Flow, Executor

class MyExecutor(Executor):
    ...


f = Flow().append(MyExecutor)
</code></pre>
<pre><code class="language-python">from jina import Flow, Executor

class MyExecutor(Executor):
    ...


f = Flow(executors=[MyExecutor])
</code></pre>
<details>
<summary>Reveal explanation</summary>
<p>
<p>The <a href="https://docs.jina.ai/fundamentals/flow/add-exec-to-flow/"><code>uses</code> parameter</a> specifies the Executor. <code>uses</code> accepts multiple value types including class name, Docker image, (inline) YAML.</p>

</p>
</details>
<h2> 6. How would you override the <code>workspace</code> directory that an Executor uses? </h2>
<pre><code class="language-python">flow = Flow().add(
    uses=MyExecutor,
    uses_metas={&#39;workspace&#39;: &#39;different_workspace&#39;},
)
</code></pre>
<pre><code class="language-python">flow = Flow().add(
    uses=MyExecutor,
    uses_with={&#39;workspace&#39;: &#39;different_workspace&#39;},
)
</code></pre>
<pre><code class="language-python">flow = Flow().add(
    uses=MyExecutor(workspace=&#39;different_workspace&#39;)
)
</code></pre>
<details>
<summary>Reveal explanation</summary>
<p>
<p><code>workspace</code> is a meta setting, meaning it applies to <em>all</em> Executors in the Flow. <a href="https://docs.jina.ai/fundamentals/flow/add-exec-to-flow/#override-executor-config">As well as meta-configuration, both request-level and Executor-level parameters can be overridden</a>.</p>

</p>
</details>
<h2> 7. What kind of input does an <code>AsyncFlow</code> accept? </h2>
<ul>
<p> <input type="checkbox"> Exactly the same as a standard Flow </p>
<p> <input type="checkbox"> Async generators </p>
<p> <input type="checkbox"> <code>AsyncDocumentArray</code>s </p>
</ul>
<details>
<summary>Reveal explanation</summary>
<p>
<p>AsyncFlow is an “async version” of the Flow class. Unlike Flow, <a href="https://docs.jina.ai/fundamentals/flow/async-flow/#create-asyncflow">AsyncFlow accepts input and output functions as async generators</a>. This is useful when your data sources involve other asynchronous libraries (e.g. motor for MongoDB):</p>

</p>
</details>
<h2> 8. What communication protocols does a Flow support? </h2>
<ul>
<p> <input type="checkbox"> SOAP </p>
<p> <input type="checkbox"> gRPC </p>
<p> <input type="checkbox"> WebSocket </p>
<p> <input type="checkbox"> REST </p>
<p> <input type="checkbox"> GraphQL </p>
</ul>
<details>
<summary>Reveal explanation</summary>
<p>
<p>Jina supports <a href="https://docs.jina.ai/fundamentals/flow/flow-as-a-service/#supported-communication-protocols">HTTP (RESTful), gRPC, and WebSocket protocols</a>.</p>

</p>
</details>
<h2> 9. How do you create a RESTful gateway for a Flow? </h2>
<pre><code class="language-python">flow = Flow()

with f:
  f.protocol = &quot;http&quot;
  f.port_expose = 12345
  f.block()
</code></pre>
<pre><code class="language-python">flow = Flow(protocol=&quot;http&quot;, port_expose=12345)

with f:
  f.block()
</code></pre>
<pre><code class="language-python">flow = Flow()

with f:
  f.gateway(protocol=&quot;restful&quot;, port=12345)
</code></pre>
<details>
<summary>Reveal explanation</summary>
<p>
<p>Jina supports gRPC, WebSocket and RESTful gateways. <a href="https://docs.jina.ai/fundamentals/flow/flow-as-a-service/">To enable a Flow to receive from HTTP requests, you can add protocol=&#39;http&#39; in the Flow constructor</a>.</p>

</p>
</details>
<h2> 10. Can you access a Flow service from a web page with a different domain? </h2>
<ul>
<p> <input type="checkbox"> No. Jina only supports access from a web page running on the same machine. </p>
<p> <input type="checkbox"> Yes, out of the box </p>
<p> <input type="checkbox"> Yes, but you have to enable CORS </p>
</ul>
<details>
<summary>Reveal explanation</summary>
<p>
<p>CORS (cross-origin-resources-sharing) is <a href="https://docs.jina.ai/fundamentals/flow/flow-as-a-service/#enable-cross-origin-resources-sharing-cors">by default disabled for security</a>. That means you can not access the service from a webpage with different domain until you enable it.</p>

</p>
</details>
