## What is Jina and Neural Search?

Jina is a search framework powered by neural networks. Classic search frameworks like Apache Solr or Elastic need strict rules and a fragile pipeline to achieve results. Jina, on the other hand, leverages the power of machine learning to train the search engine for better results.

Let's take product search as an example use case: You need a system that matches a search query with a set of products in your store. A good product search can understand user queries in any language, retrieve as many relevant products as possible, and finally present the result as a list with the preferred products at the top, and irrelevant products at the bottom.

## Classic Symbolic Searching

Not all searches are equal: For text searches like Google, these products would be structured data, often defined by a list of key-value pairs, a set of pictures, and some unstructured text. Developers use similar solutions for full-text like Apache Solr and Elastic.

Fundamentally, these are symbolic information retrieval (IR) systems, using words as symbols. If we want quality search results, we have to ensure search queries and the documents being searched are mapped to a common string space.
 
* What are the symbols in "symbolic"? The words? Tokenized words?
* How is IR different from search? Are the terms more-or-less interchangeable?
* What's an example of a string space? What does it look like?

These classic search frameworks perform three tasks. In our product search context, these are:
 
* **Indexing**: Storing products in a database with attributes as keys, like brand, color, category
* **Parsing**: Extracting attribute words from the search query. For example red sneakers -> {"color": "red", "category": "sneakers"}
* **Matching**: Filtering the product database by the parsed attributes

If no attributes match the query, the system falls back to matching the exact search sting. While parsing and matching have to be performed for each search query, indexing can be done less frequently.

Most existing open-source search frameworks follow this approach, except with more sophisticated algorithms for each step. This lets many businesses build their own product search and serve millions of customers.

### Disadvantages of Symbolic Search

#### You have to explain every little thing to the system

Our example search query above was `red nikke sneaker man`. But what if our searcher is British? A Brit would type `red nikke trainer man`. We would have to explain to our system that sneakers and trainers are just the same thing with different names. Or what is someone is searching `LV handbag`? The system would have to be told `LV` stands for `Louis Vuitton`.

All of these need to be specified by humans, meaning a lot of hard work, knowledge, and attention to detail is needed.

#### Fragility

Text is complicated: If a user types in "red nikke sneaker man" a classic search system has to recognize that they're searching for a red (color) Nike (brand with corrected spelling) sneaker (category) for men (sub-category). You can think of this process as a chain of components, one each for recognizing color, brand, etc, and for spelling correction, tokenization, etc

This approach has several drawbacks:

* Every component in the chain has an output that is fed as input into the next component along. So a problem early on in the process and break the whole system
* Some components may take inputs from multiple predecessors. That means you have to introduce more mechanisms to stop them blocking each other
* It's difficult to improve overall search quality. Just improving one or two components may lead to no improvement in actual search results
* If you want to search in another language, you have to rewrite all the language-dependent components in the pipeline, which increases maintenance cost

## Jina's Neural Search

By using machine learning, Jina:

* Removes this fragile pipeline to make the system more resilient and scalable
* Finds a better way to represent the underlying semantics of products and search queries

### How Do We Train Jina?

Machine learning systems like neural search have to be trained, and we can do that using an existing log of search queries. This log should contain what products users interacted with by clicking, adding to a wishlist, or purchasing. You may already have this information in your system. After cleaning and processing it, you can get accurate associations. We could also use other data like comments, reviews, or crowdsourced annotations.

A neural search system is only as good as its training data, so a diverse set of training materials results in a system that can make better decisions and not just mimic a classic search system. On the other hand, if your only data source is what you got from a classic system, your neural search system will be inevitably biased. For example, if the classic system just returned zero results when a user typed `nikke`, instead of correcting to `Nike`, then your system will do the same.

In a sense we're bootstrapping our neural search system with an existing symbolic search system. With enough training data we don't have to write rules or functions - these can just be picked up and learnt by the neural network.

#### Training for Irrelevance

Why would we want irrelevant products? Because we also want to know what *not* to show in our search results. We can get this data in a couple of ways:

* Randomly sampling all products: It's easy to do and not a bad idea in practice, but we have to hope we don't catch any of the products we *do* want to show.
* Collect products that often come up in results but get no clicks. This means coordination between lots of teams to ensure these really *are* uninteresting to users, and not because users would have scroll down to see them, etc.

### Does It Work Though?

We can call a search "working" if it understands and returns quality results for:

* Simple queries: Like searching 'red', 'nike', or 'sneakers'
* Compound queries: Like 'red nike sneakers'

If it can't even do those well, there's no point in checking for fancy things like spell-checking and ability to work in different languages.

Anyway, less talking, more showing:

## Jina vs Classic Search

So, how does Jina compare to the reigning champ that is symbolic search? Let's take a look at the pro's and cons of each:

|       | Symbolic search               | Neural search                      |
| ---   | ---                           | ---                                |
| Pro's | * Efficient querying          | * Automatic                        |
|       | * Easy to implement           | * Resilient to noise               |
|       | * Interpretable results       | * Scales easily                    |
|       | * Many off-the-shelf packages | * Not much domain knowledge needed |
| Cons  | * Fragile                     | * Less efficient querying          |
|       | * Hard-coded rules            | * Hard to add rules                |
|       | * High maintenance cost       | * Requires lots and lots of data   |

We're not trying to choose between Team Symbolic and Team Neural. Both approaches have their own advantages and complement each other pretty well. So a better question to ask is: How can we combine them in a way that we can enjoy all the advantages of both?

---

## Background

Product search is one of the key components in an online retail store. Essentially, you need a system that matches a text query with a set of products in your store. A good product search can understand user’s query in any language, retrieve as many relevant products as possible, and finally present the result as a list, in which the preferred products should be at the top, and the irrelevant products should be at the bottom.

> OK. Very clear

Unlike text retrieval (e.g. Google web search), products are structured data. A product is often described by a list of key-value pairs, a set of pictures and some free text. In the developers’ world, Apache Solr and Elasticsearch are known as de-facto solutions for full-text search, making them a top contender for building e-commerce product search.

> But not all searches are equal: For text searches like Google, these products would be structured data, often defined by a list of key-value pairs, a set of pictures, and some unstructured text. Developers use similar solutions for full-text like Apache Solr and Elastic.

At the core, Solr/Elasticsearch is a symbolic information retrieval (IR) system. Mapping query and document to a common string space is crucial to the search quality. This mapping process is an NLP pipeline implemented with Lucene Analyzer. In this post, I will reveal some drawbacks of such a symbolic-pipeline approach, and then present an end-to-end way to build a product search system from query logs using Tensorflow. This deep learning based system is less prone to spelling errors, leverages underlying semantics better, and scales out to multiple languages much easier.

> Fundamentally, Solr and Elastic are symbolic information retrieval (IR) systems. For quality search results, search queries and the documents being searched must be mapped to a common string space. This process is a Natural Language Programming (NLP) pipeline implemented with Lucene Analyzer.
> * What are the symbols in "symbolic"? The words? Tokenized words?
> * How is IR different from search? Are the terms more-or-less interchangeable?
> * What's an example of a string space? What does it look like?

Table of Content

    Recap Symbolic Approach for Product Search
        Symbolic IR System
    Pain points of Symbolic IR System
        1. NLP Pipeline is Fragile and doesn’t Scale Out to Multiple Languages
        2. Symbolic System does not Understand Semantics without Hard Coding
    Neural IR System
        End-to-End Model Training
        Where Do Query-Product Pairs Come From?
        What about Negative Query-Product Pairs?
    Symbolic vs. Neural IR System
    Neural Network Architecture
        Query Encoder
        Image Encoder
        Attribute Encoder
        Metric & Loss Layer
        Inference
    Training and Evaluation Scheme
    Qualitative Results
    Summary

## Recap Symbolic Approach for Product Search

Let’s first do a short review of the classic approach. Typically, an information retrieval system can be divided into three tasks: indexing, parsing and matching. As an example, the next figure illustrates a simple product search system:

    indexing: storing products in a database with attributes as keys, e.g. brand, color, category;
    parsing: extracting attribute terms from the input query, e.g. red shirt -> {"color": "red", "category": "shirt"};
    matching: filtering the product database by attributes.
  
> Classic search frameworks perform three tasks. In a product search context, these would cover
> * Indexing: Storing products in a database with attributes as keys, like brand, color, category
> * Parsing: Extracting attribute words from the search query. For example red shirt -> {"color": "red", "category": "shirt"}
> * Matching: Filtering the product database by the parsed attributes

If there is no attribute found in the query, then the system fallbacks to exact string matching, i.e. searching every possible occurrence in the database. Note that, parsing, and matching must be done for each incoming query, whereas indexing can be done less frequently depending on the stock update speed.

> If no attributes match the query, the system falls back to matching the exact search sting. While parsing and matching have to be performed for each search query, indexing can be done less frequently.

Many existing solutions such as Apache Solr and Elasticsearch follow this simple idea, except they employ more sophisticated algorithms (e.g. Lucene) for these three tasks. Thanks to these open-source projects many e-commerce businesses are able to build product search on their own and serve millions of requests from customers.
Symbolic IR System

> Most existing open-source search frameworks follow this approach, except with more sophisticated algorithms for each step. This lets many businesses build their own product search and serve millions of customers

Note, at the core, Solr/Elasticsearch is a symbolic IR system that relies on the effective string representation of the query and product. By parsing or indexing, the system knows which tokens in the query or product description are important. These tokens are the primitive building blocks for matching. Extracting important tokens from the original text is usually implemented as a NLP pipeline, consisting of tokenization, lemmatization, spelling correction, acronym/synonym replacement, named-entity recognition and query expansion.

> In this classic approach of symbolic IR system, both the query and product must be represented by strings, so the system will know which tokens are important when parsing or indexing. This is usually done as an NLP pipeline, which covers tokenization, spelling correction, etc.

Formally, given a query q∈Qq\in \mathcal{Q}q∈Q and a product p∈Pp\in\mathcal{P}p∈P, one can think the NLP pipeline as a predefined function that maps from Q\mathcal{Q}Q or P\mathcal{P}P to a common string space S\mathcal{S}S, i.e. f:Q↦Sf: \mathcal{Q}\mapsto \mathcal{S}f:Q↦S or g:P↦Sg: \mathcal{P}\mapsto \mathcal{S}g:P↦S, respectively. For the matching task, we just need a metric m:S×S↦[0,+∞)m: \mathcal{S} \times \mathcal{S} \mapsto [0, +\infty)m:S×S↦[0,+∞) and then evaluate m(f(q),g(p))m\left(f(q),g(p)\right)m(f(q),g(p)), as illustrated in the figure below.

#### You have to explain every little thing to the system

Our example search query was `red nikke sneaker man`. But what if our searcher is British? A Brit would type `red nikke trainer man`. We would have to explain to our system that sneakers and trainers are just the same thing with different names. Or what if someone searches `LV handbag`? The system would have to be told `LV` stands for `Louis Vuitton`.

All of these rules need to be specified by humans, meaning a lot of hard work, knowledge, and attention to detail is needed. And some things will always fall between the cracks!

## Jina's Neural Search

By using machine learning, Jina:

* Removes this fragile pipeline to make the system more resilient and scalable
* Finds a better way to represent the underlying semantics of products and search queries

### How Do We Train Jina?

Machine learning systems like neural search have to be trained, and we can do that using an existing log of search queries. This log should contain what products users interacted with by clicking, adding to a wishlist, or purchasing. You may already have this information in your system. After cleaning and processing it, you can get accurate associations. We could also use other data like comments, reviews, or crowdsourced annotations.

A neural search system is only as good as its training data, so a diverse set of training materials means a system that makes better decisions and not just mimic a classic search system. On the other hand, if your only data source is what you got from a classic system, your neural search system will be inevitably biased. For example, if the classic system just returned zero results when a user typed `nikke`, instead of correcting to `Nike`, then your system will do the same.

In a sense we're bootstrapping our neural search system with an existing symbolic search system. With enough training data we don't have to write rules or functions - these can just be picked up and learnt by the neural network.

#### Training for Irrelevance

Why would we want irrelevant products? Because we also want to know what *not* to show in our search results. We can get this data in a couple of ways:

* Randomly sampling all products: It's easy to do and not a bad idea in practice, but we have to hope we don't catch any of the products we *do* want to show.
* Collect products that often come up in results but get no clicks. This means coordination between lots of teams to ensure these really *are* uninteresting to users, and not because users would have scroll down to see them, etc.

### Does It Work Though?

We can call a search "working" if it understands and returns quality results for:

* Simple queries: Like searching 'red', 'nike', or 'sneakers'
* Compound queries: Like 'red nike sneakers'

If it can't even do those well, there's no point in checking for fancy things like spell-checking and ability to work in different languages.

Anyway, less talking, more showing:

**Insert pics here of product search**

## Jina vs Classic Search

So, how does Jina compare to the reigning champ that is symbolic search? Let's take a look at the pro's and cons of each:

**Note: I'll improve table layout in final version**

|       | Symbolic search               | Neural search                      |
| ---   | ---                           | ---                                |
| Pro's | * Efficient querying          | * Automatic                        |
|       | * Easy to implement           | * Resilient to noise               |
|       | * Interpretable results       | * Scales easily                    |
|       | * Many off-the-shelf packages | * Not much domain knowledge needed |
| Cons  | * Fragile                     | * Less efficient querying          |
|       | * Hard-coded rules            | * Hard to add rules                |
|       | * High maintenance cost       | * Requires lots and lots of data   |

We're not trying to choose between Team Symbolic and Team Neural. Both approaches have their own advantages and complement each other pretty well. So a better question to ask is: How can we combine them in a way that we can enjoy all the advantages of both?
