# What is Neural Search?

The core idea of neural search is to leverage state-of-the-art deep neural networks to build *every* component of a search system. In short, **neural search is deep neural network-powered information retrieval.** In academia, it's often called *neural information retrieval*, but we think the phrase is too wordy so we coined it as neural search [back in 2019](https://hanxiao.io/2019/07/29/Generic-Neural-Elastic-Search-From-bert-as-service-and-Go-Way-Beyond/).

## What can it do?

Thanks to recent advances in deep neural networks, a neural search system can go way beyond simple text search. It enables advanced intelligence on all kinds of unstructured data, such as **images**, **audio**, **video**, **PDF**, **3D mesh**, **you name it**.

For example, retrieving animation according to some beats; finding the best-fit memes according to some jokes; scanning a table with your iPhone's LiDAR camera and finding similar furniture at IKEA. Neural search systems enable what traditional search can't: multi/cross-modal data retrieval.

## Think outside the (search) box

Many neural search-powered applications do not have a search box: 

- A **question-answering chatbot** can be powered by neural search: by first indexing all hard-coded QA pairs and then semantically mapping user dialog to those pairs. 
- A **smart speaker** can be powered by neural search: by applying STT (speech-to-text) and semantically mapping text to internal commands.
- A **recommendation system** can be powered by neural search: by embedding user-item information into vectors and finding top-K nearest neighbours of a user/item.

Neural search creates a new way to comprehend the world. It is creating new doors that lead to new businesses. 

## Seize tomorrow today

Has neural search been solved and is it widely applicable? Not quite yet - but we're working on it. Compared to traditional symbolic search,
building a neural search system can seem daunting for the following reasons:
- takes much more time to develop due to the complexity of AI and system engineering;
- suffers from a fragmented tech stack and [glue code](https://en.wikipedia.org/wiki/Glue_code);
- is computationally demanding and can be very inefficient;
- is hard to sustain when facing the accelerated innovation in deep learning.

[That's why we built Jina](https://github.com/jina-ai/jina), an easier way to build scalable and sustainable neural search systems on the cloud.
