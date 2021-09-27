# Hub Portal

Hub is a marketplace for Executors. It allows everyone to share their Executors and use others' Executors. You can check the next {ref}`tutorials <create-hub-executor>` if you want to know more about the creation of an Executor.

[Hub portal](https://hub.jina.ai) gives you a bird's eye view of all Hub Executors. You can explore and find Executors that can help you to build your neural search applications.

## Catalogue Page

The very first and main page is a list of all Executors created by all Jina developers all over the world.

```{figure} ../../../.github/hub-website-list.png
:align: center
```

You can sort by switching the tab. 

- Popular: based on how much people like it and how many downloads it has.
- Recent: based on recent update time.

If you want to search some specific Executor or some Executors for specific domain, then search is the right thing to use.

You can type plain text to the search input to search specific Executor:

```{figure} ../../../.github/hub-website-search-1.png
:align: center
```

You can also type some text prefixed with character `:`, such as `:image` to search all Executors that are related to image search domain.

```{figure} ../../../.github/hub-website-search-2.png
:align: center
```

## Detail Page

Congrats! You have found some Executors that interest you! Then how do you get more detail about these Executors? Such as description and parameters of this Executor. You can find it all in Detail Page. 

```{figure} ../../../.github/hub-website-detail.png
:align: center
```

There are several tabs you can explore: README, Arguments, Tag and Dependencies.

README introduces basic information about this Executor, how this Executor works internally, its basic usage.

Arguments describes detailed API of this Executor. It's generated automatically from Python docstrings. So it's always in sync with the code base. And the Executor producers don't need to write it themselves.

```{figure} ../../../.github/hub-website-detail-arguments.png
:align: center
```

Tag lists all the available tags this Executor has. You can choose one of them. It also gives a code snippet to simplify your usage.

```{figure} ../../../.github/hub-website-detail-tag.png
:align: center
```

Dependencies lists all Python dependencies this Executor introduces.

```{figure} ../../../.github/hub-website-detail-dep.png
:align: center
```

