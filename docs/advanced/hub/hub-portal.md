# Hub Portal

Jina Hub is a marketplace for Executors. Here you can upload the Executors you have created or use the ones already developed by the community. If it's the first time you'll develop your Executor you can start by checking our {ref}`tutorials <create-hub-executor>` that will guide you through the process
 
Let's see the [Hub portal](https://hub.jina.ai) in detail

## Catalog page

The main page contains a list of all Executors created by Jina developers all over the world. By default, you will see the Editors Pick first at the top of the list. Those are the Executors that were Highlighted by the Jina team. 

```{figure} ../../../.github/hub-website-list.png
:align: center
```

You can sort the list of displayed Executors by *Trending* and *Recent* using the drop-down menu on the top. Otherwise, if you want to search for a specific Executor, you can use the search box on the top or use the tags for specific keywords such as Image, Video, TensorFlow, and so on:

```{figure} ../../../.github/hub-website-search-2.png
:align: center
```

## Detail page

After you found an Executor that interests you, you can get more detail about it by clicking on it. You will then see a description of the Executor with basic information, usage, parameters, etc. If you need more in-depth details you can click on "More" and you will be directed to a new page with all information available about that Executor. 

```{figure} ../../../.github/hub-website-detail.png
:align: center
```

There are several tabs you can explore: **README**, **Arguments**, **Tag** and **Dependencies**.

```{figure} ../../../.github/hub-website-detail-arguments.png
:align: center
```

1. **README** introduces basic information about this Executor, how it works internally, and its basic usage.

2. **Arguments** describes the detailed API of this Executor. This is generated automatically from the Python docstrings of the Executor so it's always in sync with the code base, and Executor developers don't need to write it themselves.

3. **Tags** will show you the possible tags available for this Executor. For example `latest`, `latest-gpu` and so on. It also gives a code snippet to simplify your usage.

```{figure} ../../../.github/hub-website-detail-tag.png
:align: center
```

4. **Dependencies** lists all the required Python dependencies to use this Executor

On the right side, you will see two possible ways to use this Executor. Either via Docker Image or Source Code

```{figure} ../../../.github/hub-website-usage.png
:align: center
```

That's it, now you have an overview of what the [Hub portal](https://hub.jina.ai) is and how to navigate it. 