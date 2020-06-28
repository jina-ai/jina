# What is Jina and Neural Search?

## TLDR

### What is Neural Search?

In short, neural search is a new approach to retrieving information. Instead of telling a machine a set of rules to understand what data is what, neural search uses does the same thing with a neural network. This means developers don't have to write every little rule, saving them time and headaches, and the system trains itself to get better as it goes along.

### What is Jina?

Jina is our approach to neural search. It's cloud-native, so it can be deployed in containers, and it offers anything-to-anything search. Text-to-text, image-to-image, video-to-video, or whatever else you can feed it.

## Background

Search is big business, and getting bigger every day. Whereas just a few years ago, searching meant typing something into a textbox (ah, those heady days of Yahoo! and Altavista), nowadays search encompasses text, voice, music, photos, videos, products, and so much more. Just before the turn of the millennium there were just 3.5 million Google searches per day. Today (according to the top result for search term 2020 google searches per day) that figure could be as high as 5 billion and rising, more than 1,000 times more. That’s not to mention all the billions of Tinder profiles, Amazon products, and Spotify songs searched by millions of people every day from their phones, computers, and virtual assistants.

As an example, just look at the stratospheric growth in Google queries — and that’s only until 2012!

<p align="center">
<img src="https://cdn-images-1.medium.com/max/2000/1*aYnGqTncE7DZLnb7ZlsA9A.png">
</p>

In short, search is *huge*. In this article we’re going to look at the reigning champ of search methods, symbolic search, and the plucky upstart contender, neural search.

<p align="center">
<img src="https://cdn-images-1.medium.com/max/2000/1*HhqWzCFeEj88Acp9rYHmRQ.png" width="400">
</center>

**Note:** This article is based on a [post by Han Xiao](https://hanxiao.io/2018/01/10/Build-Cross-Lingual-End-to-End-Product-Search-using-Tensorflow/) with his permission. Check there if you want a more technical introduction to neural search.

## Symbolic Search: Rules are Rules

Google is a huge general-purpose search engine. Other companies can’t just adapt it to their needs and plug it into their systems. Instead, they use solutions like [Elastic](http://elastic.co/) and [Apache Solr](https://lucene.apache.org/solr/), symbolic search systems that let developers write the rules and create the pipelines for searching products, people, messages, or whatever the company needs. 

Take [Shopify](http://www.shopify.com) for example. They use Elastic to index and search through millions of products across hundreds of categories. This couldn’t be done out-of-the-box or with a general purpose search engine like Google. They have to take Elastic and write specific rules and pipelines to index, filter, sort, and rank products by a variety of criteria, and convert this data into symbols that the system can understand. Hence the name, *symbolic search*. Here's *Colourpop*, a popular Shopify store:

<p align="center">
<img src="https://cdn-images-1.medium.com/max/3716/1*o6NN3Oz2JQqX6c0zL_H8vg.png">
</p>

You and I know that if you search for red nike sneakers you want, well, red Nike sneakers. Those are just words to a typical search system though. Sure, if you type them in you'll hopefully get what you asked for, but what if those sneakers are tagged as *trainers*? Or even tagged as *scarlet* for that matter? In cases like this, a developer needs to write rules:

* **Red** is a color
* **Scarlet** is a synonym of red
* **Nike** is a brand
* **Sneakers** are a type of footwear
* Another name for sneakers is **trainers**

Or, expressed in JSON as key-value pairs:

    {
    "color": "red",
    "color_synonyms": ["scarlet"],
    "brand": "nike",
    "type": "sneaker",
    "type_synonyms": ["trainers"],
    "category": "footwear"
    }

Each of these key-value pairs can be thought of as a symbol, hence the name *symbolic search*. When a user inputs a search query, the system breaks it down into symbols, and matches these symbols with the symbols from the products in its database.

<p align="center">
<img src="https://cdn-images-1.medium.com/max/2000/1*W_XwT1buVRA6w1zc1pNWEg.png" width="200">
</p>

But what if a user types nikke instead of nike, or searches shirts (with an s) rather than shirt? There are so many rules in language, and people break them all the time. To get effective symbols (i.e. knowing that nikke *really* means {"brand": "nike"}), you need to define lots of rules and chain them together in a complex pipeline:

<p align="center">
<img src="https://cdn-images-1.medium.com/max/2366/1*x17BoteKGOT08Jzb9xl0xA.png" width="800">
</p>

Doing that for every kind of product takes *forever* and there are always things that fall between the cracks. And if you want to localize for other languages? You’ll have to go through it all over again.

### Drawbacks of Symbolic Search

#### You Have to Explain Every. Little. Thing

Our example search query above was red nikke sneaker man. But what if our searcher is British? A Brit would type red nikke trainer man. We would have to explain to our system that sneakers and trainers are just the same thing with different names. Or what is someone is searching LV handbag? The system would have to be told LV stands for Louis Vuitton.

<p align="center">
<img src="https://cdn-images-1.medium.com/max/2000/1*Rj7d48EOct-6SRB_Yhjy4g.png" width=400>
</p>

All of these need to be specified by humans, meaning a lot of hard work, knowledge, and attention to detail is needed.

#### It’s Fragile

Text is complicated: If a user types in red nikke sneaker man a classic search system has to recognize that they're searching for a red (color) Nike (brand with corrected spelling) sneaker (type) for men (sub-type). This has to be interpreted to symbols via the pipeline, and pipelines can have major issues

<p align="center">
<img src="https://cdn-images-1.medium.com/max/2000/1*YOqh7rNFLOlTmeLSqikK0Q.png" width=200>
</p>

* Every component in the chain has an output that is fed as input into the next component along. So a problem early on in the process and break the whole system
* Some components may take inputs from multiple predecessors. That means you have to introduce more mechanisms to stop them blocking each other
* It’s difficult to improve overall search quality. Just improving one or two components may lead to no improvement in actual search results
* If you want to search in another language, you have to rewrite all the language-dependent components in the pipeline, which increases maintenance cost

## Neural Search: Train, Don’t Explain

An easier method would be train your search system on existing data. Instead of writing a rule that says if you type sportswear return sneakers, shorts, leotards, sweatbands, etc, what about just showing your system the inputs and outputs that worked before, and let it learn from those?

<p align="center">
<img src="https://cdn-images-1.medium.com/max/2000/1*IJtC-DHQ9Nb6YMzc9fi5Gg.png" width="250">
</p>

That’s the idea behind neural search systems like [Jina](http://www.jina.ai). You can take the search log from an existing system and use it to train a new, more flexible system which then learns from later user interactions to create a better user experience and more accurate results.

Compared to symbolic search, neural search:
 
* Removes the fragile pipeline, making the system more resilient and scalable
* Finds a better way to represent the underlying semantics of products and search queries
* Learns as it goes along, so improves over time

## How Do We Train Neural Search?

Machine learning systems like neural search have to be trained, and we can do that using an existing log of search queries. This log should contain what products users interacted with by clicking, adding to a wishlist, or purchasing. You may already have this information in your system. After cleaning and processing it, you can get accurate associations. You could also use other data like user comments, reviews, or crowdsourced annotations.

A neural search system is only as good as its training data, so a diverse set of training materials results in a system that can make better decisions and not just mimic a classic search system. On the other hand, if your only data source is what you got from a more rigid classic system, your neural search system will be inevitably biased. For example, if the classic system just returned zero results when a user typed nikke, instead of correcting to nike, then your system will do the same.

When we’re training our neural system, we’re showing it a set of labelled data from your existing search logs. An example would be the search query red nike sneakers and a list of the products returned by the search. These products could include images, ratings, description text, and so on. Over time the neural network gets a feel for the products as it adjusts its internal weights and biases. 

<p align="center">
<img src="https://cdn-images-1.medium.com/max/2000/1*ORPPlJNdkL4w0ImmOZ3JRA.png" width="400">
</p>

After this we'll test it on *different* sets of data from your search logs and ask it to give us the right results. This testing includes:

* Showing just the product and the system guesses the search query
* Showing just the search query and the system guesses the right products to return
* Letting the system produce matching products and search queries of its own

If it fails, then it adjusts its weights and biases to improve next time. Over time it gets better and better at understanding the concept of red nike sneakers, black chanel dress, or harley davidson motorcycle, all without having to understand the symbols that define them. No symbols means no rules for you to define, an easier experience for developers and better results for end-users.

And if you want to train your system in another language? Just gather the data to throw at it for training. No need to teach it all the rules of Spnaish, French, or Klingon.

<p align="center">
<img src="https://cdn-images-1.medium.com/max/2000/1*0XpG6posaNKgrnUqyMQzEw.png" width="250">
</p>

In a sense we’re bootstrapping the neural search system with an existing symbolic search system. With enough training data we don’t have to write rules or pipelines — these can just be picked up and learnt on-the-fly by the neural network.

### Training for Irrelevance

**Is this red Nike sneakers?**

<p align="center">
<img src="https://cdn-images-1.medium.com/max/3540/1*lpU_ag8URqUkgJfOJ5mpuA.png">
</p>

Why would we want to train for irrelevant products? Because we also want to know what *not* to show in our search results. We can get this data in a couple of ways:

* Randomly sampling all products: It’s easy to do and not a bad idea in practice, but we have to hope we don’t catch any of the products that we *do* want to show.
* Collect products that often come up in results but get no clicks. This means coordinating lots of teams to ensure these really *are* uninteresting to users, and not because users would have to scroll down to see them, etc.

We’re basically doing the inverse of the above training. We’re showing the system a Harley Davidson motorcycle and telling us that it is *not* red nike sneakers. (For an interesting example of what happens if you *don't* do this, see [this tweet from Janelle Shane](https://twitter.com/janellecshane/status/1088223417365454848))

## Does Jina Work Though?

A search “works” if it understands and returns quality results for:

* **Simple queries:** Like searching ‘red’, ‘nike’, or ‘sneakers’
* **Compound queries:** Like ‘red nike sneakers’

If it can’t even do those, there’s no point in checking for fancy things like spell-checking and ability to work in different languages.

Anyway, less talking, more searching:

    🇬🇧 nike

<p align="center">
<img src="https://cdn-images-1.medium.com/max/2612/1*oNKektGb38R6-MpA4pc-YA.png">
</p>

    🇩🇪 nike schwarz (different language)

<p align="center">
<img src="https://cdn-images-1.medium.com/max/2594/1*0YJWA5fvYZ1Dl_N2mh3lGA.png">
</p>

    🇬🇧 addidsa (misspelled brand)

<p align="center">
<img src="https://cdn-images-1.medium.com/max/2608/1*mEwmzGm0gxGkaUca4w10Yg.png">
</p>

    🇬🇧 addidsa trosers (misspelled brand and category)

<p align="center">
<img src="https://cdn-images-1.medium.com/max/2600/1*4BrUhReTod8Gbo_2ESrNBw.png">
</p>

    🇬🇧 🇩🇪 kleider flowers (mixed languages)

<p align="center">
<img src="https://cdn-images-1.medium.com/max/2604/1*acWqat542AohmX4TJUPq_g.png">
</p>

So, as you can see, neural search does pretty well!

## Comparing Symbolic and Neural Search

So, how does neural search compare to the reigning champ that is symbolic search? Let’s take a look at the pro’s and cons of each:

<table width="100%">
  <thead>
    <tr>
      <th scope="col">
      </th>
      <th scope="col">
        Pro's
      </th>
      <th scope="col">
        Cons
      </th>
    </tr>
  <thead>
  <tbody>
    <tr>
      <th scope="row">
        Symbolic Search
      </th>
      <td>
        <li>Efficient querying</li>
        <li>Easy to implement</li>
        <li>Interpretable results</li>
        <li>Off-the-shelf packages</li>
      </td>
      <td>
        <li>Fragile</li>
        <li>Hard-coded rules</li>
        <li>Maintenance costs</li>
      </td>
    </tr>
    <tr>
      <th scope="row">
        Neural Search
      </th>
      <td>
        <li>Automatic</li>
        <li>Resilient to noise</li>
        <li>Scales easily</li>
        <li>Little domain knowledge needed</li>
      </td>
      <td>
        <li>Less efficient querying</li>
        <li>Hard to add rules</li>
        <li>Needs lots of data</li>
      </td>
    </tr>
  </tbody>
</table>

We’re not trying to choose between Team Symbolic and Team Neural. Both approaches have their own advantages and complement each other pretty well. So a better question to ask is: Which is right for your organization?

## Try Jina Yourself

<p align="center">
<img src="https://cdn-images-1.medium.com/max/2000/0*n27u8HMyBgIiiKHW.gif">
</p>

There’s no better way to test-drive Jina technology than by diving in and playing with it. We provide pre-trained Docker images and [jinabox.js](https://github.com/jina-ai/jinabox.js/), an easy-to-use front-end for searching text, images, audio, or video. There’s no product search example (yet), but you *can* search for more light-hearted things like lines from South Park or your favorite Pokémon.
