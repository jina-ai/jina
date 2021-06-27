# Cookbook on Clean & Efficient Code

Jina is designed as a lean and efficient framework. Solutions built on top of Jina also mean to be so. Here are some
tips to help you write beautiful and efficient code.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->



<!-- END doctoc generated TOC please keep comment here to allow auto update -->

1. `from jina import Document, DocumentArray, Executor, Flow, requests` is all you need. Copy-paste it as the first line of your code.

1. Use [Python generator](https://docs.python.org/3/glossary.html#term-generator) as the input to the Flow. Generator can lazily build `Document` one at a time, instead of building all at once. This can greatly speedup the overall performance and reduces the memory footprint.

   <table>
   <tr>
   <td>
   <b><center>✅ Do</center></b>
   </td>
   <td>
   <b><center>😔 Don't</center></b>
   </td>
   </tr>
   <tr>
   <td>
   
   ```python
   from jina import Flow, Document
   
   def my_input():
       for _ in range(1000):
          yield Document()

   f = Flow()
   with f:
      f.post('/', my_input)
   ```


   </td>
   <td>
   
   ```python
   from jina import Flow, Document, DocumentArray
   
   my_input = DocumentArray([Document() for _ in range(1000)]) 
   
   f = Flow()
   with f:
      f.post('/', my_input)
   ```
   
   </td>
   </tr>
   </table>

1. Set `request_size`. `request_size` decides how many Documents in each request. When combining with Generator, `request_size` determines how long will it take before sending the first request. You can change `request_size` to overlap the time of request generation and Flow computation.


   <table>
   <tr>
   <td>
   <b><center>✅ Do</center></b>
   </td>
   <td>
   <b><center>😔 Don't</center></b>
   </td>
   </tr>
   <tr>
   <td>
   
   ```python
   from jina import Flow, Document
   
   def my_input():
       for _ in range(1000):
          # big document
          yield Document()

   f = Flow().add(uses=...)  # heavy computation
   with f:
      f.post('/', my_input, request_size=10)
   ```


   </td>
   <td>
   
   ```python
   from jina import Flow, Document
   
   def my_input():
       for _ in range(1000):
          # big document
          yield Document()

   f = Flow().add(uses=...)  # heavy computation
   with f:
      f.post('/', my_input, request_size=10000)
   ```
   
   </td>
   </tr>
   </table>

1. No need to implement `__init__` if your `Executor` does not contain initial states.
   
   <table>
   <tr>
   <td>
   <b><center>✅ Do</center></b>
   </td>
   <td>
   <b><center>😔 Don't</center></b>
   </td>
   </tr>
   <tr>
   <td>
   
   ```python
   from jina import Executor
   
   class MyExecutor(Executor):
      def foo(self, **kwargs):
        ...
   ```
   </td>
   <td>
   
   ```python
   from jina import Executor
   
   class MyExecutor(Executor):
      def __init__(**kwargs):
        super().__init__(**kwargs)
   
      def foo(self, **kwargs):
        ...
   ```
   
   </td>
   </tr>
   </table>
   
1. Use `@requests` without specifying `on=` if your function mean to work on all requests. You can use it for catching all requests that are not for this Executor.

   <table>
   <tr>
   <td>
   <b><center>✅ Do</center></b>
   </td>
   <td>
   <b><center>😔 Don't</center></b>
   </td>
   </tr>
   <tr>
   <td>
   
   ```python
   from jina import Executor, requests
   
   class MyExecutor(Executor):
      
      @requests
      def _skip_all(self, **kwargs):
        print('default do sth')
   ```
   
   </td>
   <td>
   
   ```python
   from jina import Executor
   
   class MyExecutor(Executor):
      @requests(on='/index')
      def _skip_index(self, **kwargs):
        pass
   
      @requests(on='/search')
      def _skip_search(self, **kwargs):
        pass
   ```

   </td>
   </tr>
   </table>
   
1. Fold unnecessary arguments into `**kwargs`, only get what you need.

   <table>
   <tr>
   <td>
   <b><center>✅ Do</center></b>
   </td>
   <td>
   <b><center>😔 Don't</center></b>
   </td>
   </tr>
   <tr>
   <td>
   
   ```python
   from jina import Executor, requests
   
   class MyExecutor(Executor):
      
      @requests
      def foo_need_pars_only(self, parameters, **kwargs):
        print(parameters)
   ```
   </td>
   <td>
   
   ```python
   from jina import Executor, requests
   
   class MyExecutor(Executor):
      
      @requests
      def foo_need_pars_only(self, docs, parameters, docs_matrix, groundtruths_matrix, **kwargs):
        print(parameters)
   ```
   
   </td>
   </tr>
   </table>

1. To debug an `Executor`, there is no need to use it in the Flow. Simply initiate it as an object and call its method.

   <table>
   <tr>
   <td>
   <b><center>✅ Do</center></b>
   </td>
   <td>
   <b><center>😔 Don't</center></b>
   </td>
   </tr>
   <tr>
   <td>
   
   ```python
   from jina import Executor, requests, DocumentArray, Document


   class MyExec(Executor):
   
       @requests
       def foo(self, docs, **kwargs):
           for d in docs:
               d.text = 'hello world'
   
   
   m = MyExec()
   da = DocumentArray([Document(text='test')])
   m.foo(da)
   print(da)
   ```
   
   </td>
   <td>
   
   ```python
   from jina import Executor, requests, DocumentArray, Document, Flow
   
   
   class MyExec(Executor):
   
       @requests
       def foo(self, docs, **kwargs):
           for d in docs:
               d.text = 'hello world'
   
   
   da = DocumentArray([Document(text='test')])
   
   with Flow().add(uses=MyExec) as f:
       f.post('/', da, on_done=print)
   ```
   
   </td>
   </tr>
   </table>
   
1. Send `parameters` only request to a Flow if you don't need `docs`.

   <table>
   <tr>
   <td>
   <b><center>✅ Do</center></b>
   </td>
   <td>
   <b><center>😔 Don't</center></b>
   </td>
   </tr>
   <tr>
   <td>
   
   ```python
   from jina import Executor, Flow, requests
   
   class MyExecutor(Executor):
      
      @requests
      def foo_need_pars_only(self, parameters, **kwargs):
        print(parameters)
   
   f = Flow().add(uses=MyExecutor)
   
   with f:
      f.post('/foo', parameters={'hello': 'world'})
   ```
   
   </td>
   <td>
   
   ```python
   from jina import Executor, Flow, Document, requests
   
   class MyExecutor(Executor):
      
      @requests
      def foo_need_pars_only(self, parameters, **kwargs):
        print(parameters)
   
   f = Flow().add(uses=MyExecutor)
   
   with f:
      f.post('/foo', inputs=Document(), parameters={'hello': 'world'})
   ```
   
   </td>
   </tr>
   </table>
