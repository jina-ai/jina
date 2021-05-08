# Temporary Cookbook on Clean Code

Jina is designed as a lean and efficient framework. Solutions built on top of Jina also mean to be clean. Here are some
tips to help you write clean & beautiful code.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->



<!-- END doctoc generated TOC please keep comment here to allow auto update -->

1. **`from jina import Document, DocumentArray, Executor, Flow, requests` is all you need.**

1. **No need to implement `__init__` if your `Executor` does not contain initial states.**

1. **Use `@requests` without specifying `on=` if your function mean to work on all requests.**

1. **Fold unnecessary arguments into `**kwargs`.**