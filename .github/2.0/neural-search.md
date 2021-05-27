# What is Neural Search?

**Neural Search is deep neural network-powered information retrieval.** In academics, it is often termed as Neural IR. The core idea is to leverage the state-of-the-art deep neural network to build *every* component of a search system. 

### What can it do?

Thanks to the recent advances in Deep Neural Network, a neural search system can go way beyond simple text search. It enables advanced intelligence on all kinds of unstructured data, such as image, audio, video, PDF, 3D mesh.

For example, retrieving animation according to some beats; finding the best-fit memes according to some jokes; scanning a table with your iPhone LiDAR camera and finding similar ones on IKEA. Neural search system enables what traditional search can't: multi/cross-modality data retrieval.

### Think out of the (search)box

Many neural search-powered applications do not have a search box: 

- A question-answering chatbot can be powered by neural search: by first indexing all hardcoded QA pairs and then semantically mapping user dialog to those pairs. 
- A smart speaker can be powered by neural search: by applying STT (speech-to-text) and semantically mapping text to internal commands.
- A recommendation system can be powered by neural search: by embedding user-item information into vectors and finding top-K nearest neighbours of a user/item.

Neural search creates a new way of how we comprehend the world. It is creating new doors led to new businesses. 

### Seize the future today

Has neural search been solved and widely applicable? No. Comparing to traditional symbolic search, a neural search system:
- takes much more time to develop due to the complexity of AI & system engineering;
- suffers from fragmented tech stack and glue code system;
- is computational demanding and can be very inefficient;
- hard to sustain when facing the accelerated innovation in deep learning.

[That's why we build Jina](https://github.com/jina-ai/jina), an easier way to build scalable and sustainable neural search system on the cloud.