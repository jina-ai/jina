# Cookbook on Clean Code

Jina is designed as a lean and efficient framework. Solutions built on top of Jina also mean to be so. Here are some
tips to help you write clean and beautiful code.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->



<!-- END doctoc generated TOC please keep comment here to allow auto update -->

1. `from jina import Document, DocumentArray, Executor, Flow, requests` is all you need. Copy-paste it as the first line of your code.

1. No need to implement `__init__` if your `Executor` does not contain initial states.
   
   ✅ Do:
   ```python
   from jina import Executor
   
   class MyExecutor(Executor):
      def foo(self, **kwargs):
        ...
   ```
   😔 Don't:
   ```python
   from jina import Executor
   
   class MyExecutor(Executor):
      def __init__(**kwargs):
        super().__init__(**kwargs)
   
      def foo(self, **kwargs):
        ...
   ```

1. Use `@requests` without specifying `on=` if your function mean to work on all requests. You can use it for catching all requests that are not for this Executor.

   ✅ Do:
   ```python
   from jina import Executor, requests
   
   class MyExecutor(Executor):
      
      @requests
      def _skip_all(self, **kwargs):
        print('default do sth')
   ```
   😔 Don't:
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

1. Fold unnecessary arguments into `**kwargs`, only get what you need.

   ✅ Do:
   ```python
   from jina import Executor, requests
   
   class MyExecutor(Executor):
      
      @requests
      def foo_need_pars_only(self, parameters, **kwargs):
        print(parameters)
   ```
   😔 Don't:
   ```python
   from jina import Executor, requests
   
   class MyExecutor(Executor):
      
      @requests
      def foo_need_pars_only(self, docs, parameters, docs_matrix, groundtruths_matrix, **kwargs):
        print(parameters)
   ```

1. To debug an `Executor`, there is no need to use it in the Flow. Simply initiate it as an object and call its method.

   ✅ Do:
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
   
   😔 Don't:
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
   
1. Send `parameters` only request to a Flow if you don't need `docs`.

   ✅ Do:
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
   😔 Don't:
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

