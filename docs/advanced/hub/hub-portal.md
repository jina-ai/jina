# Hub Portal

Jina Hub is a marketplace for Executors. It allows anyone to share their Executors and use others' Executors. You can check the next {ref}`tutorials <create-hub-executor>` if you want to know more about creating an Executor.

[Hub portal](https://hub.jina.ai) gives you a bird's eye view of all Hub Executors. You can explore and find Executors to help you build your neural search applications.

## Catalog page

The very first and main page is a list of all Executors created by all Jina developers all over the world.

```{figure} ../../../.github/hub-website-list.png
:align: center
```

You can sort by switching tabs: 

- Popular: how many people like the Executor and how many downloads it has.
- Recent: based on when the Executor was last updated.

If you want to search for a specific Executor or Executors for a specific domain you can type plain text into the search box:

```{figure} ../../../.github/hub-website-search-1.png
:align: center
```

You can also prefix text with `:`, such as `:image` to search all Executors that are related to the image search domain.

```{figure} ../../../.github/hub-website-search-2.png
:align: center
```

## Detail page

Congratulations! You have found some Executors that interest you! Then how do you get more detail about these Executors, like description and parameters? You can find them all in the detail page. 

```{figure} ../../../.github/hub-website-detail.png
:align: center
```

There are several tabs you can explore: README, Arguments, Tag and Dependencies.

README introduces basic information about this Executor, how it works internally, and its basic usage.

Arguments describes the detailed API of this Executor. It's generated automatically from Python docstrings so it's always in sync with the code base, and Executor developers don't need to write it themselves.

```{figure} ../../../.github/hub-website-detail-arguments.png
:align: center
```

Tag lists all the available tags for this Executor. It also gives a code snippet to simplify your usage.

```{figure} ../../../.github/hub-website-detail-tag.png
:align: center
```

Dependencies lists the Executor's Python dependencies.

```{figure} ../../../.github/hub-website-detail-dep.png
:align: center
```

