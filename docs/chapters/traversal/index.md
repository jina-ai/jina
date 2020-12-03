# Understand Jina Document Recursive Structure and Traversal

In Jina, each Document is represented as a rooted binary-tree:

>  a binary tree is a tree data structure in which each node has at most two children, which are referred to as the left child and the right child.

A rooted binary tree has a root node and every node has at most two children.
In Jina, the root node is the document itself, while the *left* & *right* child are referred as *chunks* and *matches* respectivaly.

![rooted-binary-tree](img/rooted-binary-tree.png)

The above image illustrates a most simple document structure: A document (root node) consist of two child nodes, *chunks* and *matches*.
We'll dive into these concepts in this document:

- [Chunks in Jina](#chunks-in-jina)
- [Matches in Jina](#matches-in-jina)
- [Recursive structure and Traversal](#recursive-structure-and-traversal)
---

## Chunks in Jina
