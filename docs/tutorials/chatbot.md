# Hello World Chatbot


We will use the [hello world chatbot](https://github.com/jina-ai/jina#run-quick-demo) for this tutorial. You can find the complete code [here](https://github.com/jina-ai/jina/tree/master/jina/helloworld/chatbot) and we will go step by step.

At the end of this tutorial, you will have your own chatbot. You will use text as an input and get a text result as output. For this example, we will use a [covid dataset](https://www.kaggle.com/xhlulu/covidqa). You will understand how every part of this example works and how you can create new apps with different datasets on your own.

## Set-up & overview

We recommend creating a [new python virtual environment](https://docs.python.org/3/tutorial/venv.html), to have a clean install of Jina and prevent dependency clashing.

We can start by installing Jina:

 ``` shell
pip install jina
 ```

For more information on installing Jina, refer to this [page](https://github.com/jina-ai/jina#install).

And we need the following dependencies:


``` shell
pip install click==7.1.2
pip install transformers==4.1.1
pip install torch==1.7.1
```

Once you have Jina and the dependencies installed, let's get a broad overview of the process we'll follow:

![image](/assets/images/blog/tutorials/flow.png)

You see from this image that you have your data at the beginning of this Flow process, and this can be any data type:

-   Text
-   Images
-   Audio
-   Video
-   Or any other type

In this case, we are using text, but it can be whatever data type you want.

Because our use case is very simple we don't need to process this data any further, and we can move straight on and encode our data into vectors then finally store those vectors, so they are ready for indexing and querying.

Note: If you have a different use case or dataset you may need to process your data somehow (this is a very common task in machine learning)

## Tutorial

### Define data and work directories

We can start creating an empty folder, I'll call mine `tutorial` and that's the name you'll see through the tutorial but feel free to use whatever you wish.

We will display our results in our browser, so download the static folder from [here](https://github.com/jina-ai/jina/tree/master/jina/helloworld/chatbot/static), and paste it into your tutorial folder. This is only the CSS and HTML files to render our results. We will use a dataset in a `.csv` format. I'll use the [COVID](https://www.kaggle.com/xhlulu/covidqa) dataset from Kaggle. You don't need to download this by hand, we'll do it later in our app.

### Create a Flow

The very first concept you'll see in Jina is a Flow. You can see [here](https://github.com/jina-ai/jina/blob/master/.github/2.0/cookbooks/Flow.md) a more formal introduction of what it is, but for now, think of the Flow as a manager in Jina, it takes care of the all the tasks that will run on your application and each Flow object will take care of one real-world task.

To create a Flow you only need to import it from Jina. So open your favorite IDE, create a `app.py` file and let's start writing our code:

``` python
from jina import Flow
flow = Flow()
```

But this is an empty Flow. Since we want to encode our data and then index it, we need to add elements to it. The only things we add to a Flow are Executors. We will talk about them more formally later, but think of them as the elements that will do all the data processing you want.

### Add elements to a Flow

To add elements to your Flow you just need to use the `.add()` method. You can add as many pods as you wish.

``` python
from jina import Flow
flow = Flow().add().add()
```

And for our example, we need to add two `Executors`:

1.  A transformer (to encode our data)
2.  An indexer

So add the following to our code:

``` python
from jina import Flow
flow = (
        Flow()
        .add(uses=MyTransformer)
        .add(uses=MyIndexer)
    )
```

Right now we haven't defined `MyTransformer` or `MyIndexer`. Let's create some dummy Executors so we can try our app. These will not be our final Executors but just something basic to learn first.

### Create dummy Executors

Now we have a Flow with two Executors. Write the following in your code:

``` python
from jina import Jina, Executor, requests

class MyTransformer(Executor):
    @requests(on='/foo')
    def foo(self, **kwargs):
        print(f'foo is doing cool stuff: {kwargs}')

class MyIndexer(Executor):
    @requests(on='/bar')
    def bar(self, **kwargs):
        print(f'bar is doing cool stuff: {kwargs}')
```

We will have more complex Executors later. For now our two Executors are only printing a line.

So far it's a simple Flow but it is still useful to visualize it to make sure we have what we want.

### Visualize a Flow

By now, your code should look like this:

``` python
from jina import Flow, Document, Executor, requests

class MyTransformer(Executor):
    @requests(on='/foo')
    def foo(self, **kwargs):
        print(f'foo is doing cool stuff: {kwargs}')

class MyIndexer(Executor):
    @requests(on='/bar')
    def bar(self, **kwargs):
        print(f'bar is doing cool stuff: {kwargs}')

flow = (
        Flow()
        .add(uses=MyTransformer)
        .add(uses=MyIndexer)
    )

```

If you want to visualize your Flow you can do that with `plot`. So add the `.plot()` function at the end of your Flow

``` python
from jina import Flow

flow = (
        Flow()
        .add(uses=MyTransformer)
        .add(uses=MyIndexer)
        .plot('our_flow.svg')
    )
```

Let's run the code we have so far. If you try it, not much will happen since we are not indexing anything yet, but you will see the new file `our_flow.svg` created on your working folder, and if you open it you would see this:

![image](/assets/images/blog/tutorials/plot_flow1.png)

You can see a Flow with two Executors, but what if you have many Executors? this can quickly become very messy, so it is better to name the Executors with `name='CoolName'`. So in our example, we use:

``` python
from jina import Flow

flow = (
        Flow()
        .add(name='MyTransformer', uses=MyTransformer)
        .add(name='MyIndexer', uses=MyIndexer)
        .plot('our_flow.svg')
    )
```

Now if you run this, you should have a Flow that is more explicit:

![image](/assets/images/blog/tutorials/plot_flow2.png)

### Use a Flow

Ok, we have our Flow created and visualized. Let's put it to use now. The correct way to use a Flow is to open it as a context manager, using the with keyword:

``` python
with flow:
    ...
```

Before we use it in our example, let's recap a bit of what we have seen:

``` python
from jina import Flow
flow = Flow()          # Create Flow

flow.add().add()       # Add elements to Flow
flow.plot()            # Visualize a Flow

with flow:             # Use Flow as a context manager
    flow.index()
```

In our example, we have a Flow with two Executors (`MyTransformer` and `MyIndexer`) and we want to use our Flow to index our data. But in this case, our data is a csv file. We need to open it first.

``` python
with flow, open('our_dataset.csv') as fp:
        flow.index()
```

Now we have our Flow ready, we can start to index. But we can't just pass the dataset in the original format to our Flow. We need to create a Document with the data we want to use.

### To create a Document

To create a Document in Jina, we do it like this:

``` python
from jina import Document
doc = Document(content='hello, world!')
```

In our case, the content of our Document needs to be the dataset we want to use:

``` python
from jina import Document
doc = Document.from_csv(fp, field_resolver={'question': 'text'})
```

So what happened there? We created a Document `doc`, and we use `from_csv` to load our dataset. We use `field_resolver` to map the text from our dataset to the Document attributes.

### Get our data

We have everything ready to use our Flow, but so far we have been using dummy data. Let's download our dataset now. Copy and paste this snippet, we don't need to go into the details for this. What it does is to download the [covid dataset](https://www.kaggle.com/xhlulu/covidqa).

``` python
def download_data(targets, download_proxy=None, task_name='download covid-dataset'):

"""
Download data.

:param targets: target path for data.
:param download_proxy: download proxy (e.g. 'http', 'https')
:param task_name: name of the task
"""
opener = urllib.request.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]
if download_proxy:
    proxy = urllib.request.ProxyHandler(
        {'http': download_proxy, 'https': download_proxy}
    )
    opener.add_handler(proxy)
urllib.request.install_opener(opener)
with ProgressBar(task_name=task_name, batch_unit='') as t:
    for key, value in targets.items():
        if not os.path.exists(value['filename']):
            urllib.request.urlretrieve(
                value['url'], value['filename'], reporthook=lambda *x: t.update_tick(0.01)
            )
```

Let's re-organize our code a little bit. First, we should import everything we need:

``` python
import os
import urllib.request
import webbrowser
from pathlib import Path

from jina import Flow, Executor
from jina.logging import default_logger
from jina.logging.profile import ProgressBar
from jina.parsers.helloworld import set_hw_chatbot_parser
from jina.types.document.generators import from_csv
```

Then we should have our `main`, a `download_data` function and a `tutorial` function

``` python
def download_data(targets, download_proxy=None, task_name='download covid-dataset'):
    # This is exactly as the previous snippet we just saw

def tutorial(args):
    # Here we will have everything for our tutorial

if __name__ == '__main__':
    args = set_hw_chatbot_parser().parse_args()
    tutorial(args)
```

Now let's see our tutorial function with all the code we've done so far:

``` python
def tutorial(args):
    Path(args.workdir).mkdir(parents=True, exist_ok=True)

    class MyTransformer(Executor):
        @requests(on='/foo')
        def foo(self, **kwargs):
            print(f'foo is doing cool stuff: {kwargs}')

    class MyIndexer(Executor):
        @requests(on='/bar')
        def bar(self, **kwargs):
            print(f'bar is doing cool stuff: {kwargs}')

    targets = {
        'covid-csv': {
            'url': args.index_data_url,
            'filename': os.path.join(args.workdir, 'dataset.csv'),
        }
    }

    # download the data
    download_data(targets, args.download_proxy, task_name='download covid-dataset')

    flow = (
        Flow()
            .add(name='MyTransformer', uses=MyTransformer)
            .add(name='MyIndexer', uses=MyIndexer)
            .plot('test.svg')
    )

    with flow, open(targets['covid-csv']['filename']) as fp:
        flow.index(from_csv(fp, field_resolver={'question': 'text'}))
```

If you run this, it should finish without errors. You won't see much yet because we are not showing anything after we index. But you should see a new directory created with the downloaded dataset:

![image](/assets/images/blog/tutorials/downloaded_dataset.png)

To actually see something we need to specify how we will display it. For our tutorial we will do so in our browser. Add the following after indexing:

``` python
flow.use_rest_gateway(args.port_expose)

url_html_path = 'file://' + os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 'static/index.html'
    )
)
try:
    webbrowser.open(url_html_path, new=2)
except:
    pass  # intentional pass, browser support isn't cross-platform
finally:
    default_logger.success(
        f'You should see a demo page opened in your browser, '
        f'if not, you may open {url_html_path} manually'
    )

if not args.unblock_query_flow:
    flow.block()
```

For more information on what the Flow is doing, specially in `f.use_rest_gateway(args.port_expose)` and `f.block()` check our [cookbook](https://github.com/jina-ai/jina/blob/master/.github/2.0/cookbooks/Flow.md)

Ok, so it seems that we have plenty of work done already. If you run this you will see a new tab open in your browser, and there you will have a text box ready for you to input some text. However, if you try to enter anything you won't get any results. This is because we are using dummy Executors. Our `MyTransformer` and `MyIndexer` aren't actually doing anything. So far they only print a line when they are called. So we need real Executors.

This has been plenty of new information you've learned so far, so we won't go deep into Executors today. Instead you can copy-paste the ones we are using for [this example](https://github.com/jina-ai/jina/blob/master/jina/helloworld/chatbot/executors.py), save that `executors.py` file in the same directory where the rest of your code is. The important part to understand is that all Executors' behavior is defined in `executors.py`

To try the Executors from the Github repo, just add this before the `download_data` function:

``` python
if __name__ == '__main__':
    from executors import MyTransformer, MyIndexer
else:
    from .executors import MyTransformer, MyIndexer
```

And remove the dummy executors we made. Your `app.py` should now look like this:

``` python

import os
import urllib.request
import webbrowser
from pathlib import Path

from jina import Flow, Executor
from jina.logging import default_logger
from jina.logging.profile import ProgressBar
from jina.parsers.helloworld import set_hw_chatbot_parser
from jina.types.document.generators import from_csv

if __name__ == '__main__':
    from executors import MyTransformer, MyIndexer
else:
    from .executors import MyTransformer, MyIndexer


def download_data(targets, download_proxy=None, task_name='download fashion-mnist'):
    """
    Download data.

    :param targets: target path for data.
    :param download_proxy: download proxy (e.g. 'http', 'https')
    :param task_name: name of the task
    """
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    if download_proxy:
        proxy = urllib.request.ProxyHandler(
            {'http': download_proxy, 'https': download_proxy}
        )
        opener.add_handler(proxy)
    urllib.request.install_opener(opener)
    with ProgressBar(task_name=task_name, batch_unit='') as t:
        for k, v in targets.items():
            if not os.path.exists(v['filename']):
                urllib.request.urlretrieve(
                    v['url'], v['filename'], reporthook=lambda *x: t.update_tick(0.01)
                )

def tutorial(args):

    Path(args.workdir).mkdir(parents=True, exist_ok=True)

    '''
    Comment this to use the exectors you have in `executors.py`
    class MyTransformer(Executor):
        def foo(self, **kwargs):
            print(f'foo is doing cool stuff: {kwargs}')

    class MyIndexer(Executor):
        def bar(self, **kwargs):
            print(f'bar is doing cool stuff: {kwargs}')
    '''

    targets = {
        'covid-csv': {
            'url': args.index_data_url,
            'filename': os.path.join(args.workdir, 'dataset.csv'),
        }
    }

    # download the data
    download_data(targets, args.download_proxy, task_name='download covid-dataset')

    f = (
        Flow()
            .add(name='MyTransformer', uses=MyTransformer)
            .add(name='MyIndexer', uses=MyIndexer)
            .plot('test.svg')
    )

    with f, open(targets['covid-csv']['filename']) as fp:
        f.index(from_csv(fp, field_resolver={'question': 'text'}))

        # switch to REST gateway at runtime
        f.use_rest_gateway(args.port_expose)

        url_html_path = 'file://' + os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)), 'static/index.html'
            )
        )
        try:
            webbrowser.open(url_html_path, new=2)
        except:
            pass  # intentional pass, browser support isn't cross-platform
        finally:
            default_logger.success(
                f'You should see a demo page opened in your browser, '
                f'if not, you may open {url_html_path} manually'
            )

        if not args.unblock_query_flow:
            f.block()

if __name__ == '__main__':
    args = set_hw_chatbot_parser().parse_args()
    tutorial(args)
```

And your directory should be:

    .
    ├── project                    
    │   ├── app.py          
    │   ├── executors.py         
    │   └── static/         
    │   └── our_flow.svg #This will be here if you used the .plot() function       
    └── ...
    
And we are done! If you followed all the steps, now you should have something like this in your browser:

![image](/assets/images/blog/tutorials/results.png)

There are still a lot of concepts to learn. So stay tuned for our next tutorials.

If you have any issues following this tutorial, you can always get support from our [Slack community](https://slack.jina.ai/)

## Community


-   [Slack community](https://slack.jina.ai/) - a communication platform for developers to discuss Jina.
-   [LinkedIn](https://www.linkedin.com/company/jinaai/) - get to know Jina AI as a company and find job opportunities.
-   [Twitter](https://twitter.com/JinaAI_) - follow us and interact with us using hashtag #JinaSearch.
-   [Company](https://jina.ai) - know more about our company, we are fully committed to open-source!

## License


Copyright (c) 2021 Jina AI Limited. All rights reserved.

Jina is licensed under the Apache License, Version 2.0. See [LICENSE](https://github.com/jina-ai/jina/blob/master/LICENSE) for the full license text.
