# Search Image from Text via CLIP model

In this tutorial, we create an image search system that retrieves images based on short text descriptions of their content.

To do so, we need to figure out away to match images and texts. One way to find such matches we need to find related images with similar semantics to the query texts. This requires us to represent both images and query texts in the same space to be able to do the matching. In this case, pre-trained cross-modal models can help us out.

The full source code is available in this (google colab notebook)[https://colab.research.google.com/drive/1CkT1udBrMfefYo0XJO45kIpW43odLLDm?usp=sharing]