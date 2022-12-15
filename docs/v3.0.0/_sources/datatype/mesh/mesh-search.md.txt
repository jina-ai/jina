# Search Similar 3D Meshes

In this tutorial, we will learn how to build a 3D mesh search pipeline with Jina. In particular, we will be building a search pipeline for 3D models in GLB format.

Just like other data types, the 3D meshes search pipeline consists of **loading**, **encoding** and **indexing** the data. We can search the data after they are indexed.

## Prerequisites

Let's first install the following PyPI dependencies:
```shell
pip install tensorflow trimesh pyrender
```

## Load GLB data

First, given a `glb` file, how do we load and craft the `glb` into a Document so that we can process and encode?  Let's use `trimesh` to build an executor for this.

```python
def as_mesh(scene: trimesh.Scene) -> Optional[trimesh.Trimesh]:
    if len(scene.geometry) == 0:
        return None
    return trimesh.util.concatenate(
        tuple(trimesh.Trimesh(vertices=g.vertices, faces=g.faces)
            for g in scene.geometry.values()))


class GlbCrafter(Executor):
    @requests(on=['/index', '/search'])
    def craft(self, docs: DocumentArray, **kwargs):
        for d in docs:
            mesh = trimesh.load_mesh(d.uri)
            d.blob = as_mesh(mesh).sample(2048)
```

We first load the data of each `glb` file as Python object. We will use the `trimesh` package to represents the `glb` data in the form of triangular meshes. The loaded object is of type `trimesh.Scene` which may contain one or more triangular mesh geometries. We combine all the meshes in the `Scene` to create a single `Trimesh` using `as_mesh`. Then we can sample surfaces from a single mesh geometry. The sampled surface will be made from 2048 points in 3D space and hence the shape of the `ndarray` representing each 3D model will be `(2048, 3)`.

## Encode 3D Model

Once we convert each `glb` model into an `ndarray`, encoding the inputs becomes straightforward. We will use our pre-trained `pointnet` to encode the data. The model looks like:

```python
def get_model(ckpt_path):
    import numpy as np
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    
    def conv_bn(x, filters):
        x = layers.Conv1D(filters, kernel_size=1, padding='valid')(x)
        x = layers.BatchNormalization(momentum=0.0)(x)
        return layers.Activation('relu')(x)
    
    
    def dense_bn(x, filters):
        x = layers.Dense(filters)(x)
        x = layers.BatchNormalization(momentum=0.0)(x)
        return layers.Activation('relu')(x)
    
    
    def tnet(inputs, num_features):
        class OrthogonalRegularizer(keras.regularizers.Regularizer):
            def __init__(self, num_features_, l2reg=0.001):
                self.num_features = num_features_
                self.l2reg = l2reg
                self.eye = tf.eye(self.num_features)
    
            def __call__(self, x):
                x = tf.reshape(x, (-1, self.num_features, self.num_features))
                xxt = tf.tensordot(x, x, axes=(2, 2))
                xxt = tf.reshape(xxt, (-1, self.num_features, self.num_features))
                return tf.reduce_sum(self.l2reg * tf.square(xxt - self.eye))
    
            def get_config(self):
                return {'num_features': self.num_features,
                        'l2reg': self.l2reg,
                        'eye': self.eye.numpy()}
    
        bias = keras.initializers.Constant(np.eye(num_features).flatten())
        reg = OrthogonalRegularizer(num_features)
    
        x = conv_bn(inputs, 32)
        x = conv_bn(x, 64)
        x = conv_bn(x, 512)
        x = layers.GlobalMaxPooling1D()(x)
        x = dense_bn(x, 256)
        x = dense_bn(x, 128)
        x = layers.Dense(
            num_features * num_features,
            kernel_initializer='zeros',
            bias_initializer=bias,
            activity_regularizer=reg,
        )(x)
        feat_T = layers.Reshape((num_features, num_features))(x)
        return layers.Dot(axes=(2, 1))([inputs, feat_T])

    inputs = keras.Input(shape=(2048, 3))
    x = tnet(inputs, 3)
    x = conv_bn(x, 32)
    x = conv_bn(x, 32)
    x = tnet(x, 32)
    x = conv_bn(x, 32)
    x = conv_bn(x, 64)
    x = layers.GlobalMaxPooling1D()(x)
    x = dense_bn(x, 128)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(1, activation='softmax')(x)
    model = keras.Model(inputs=inputs, outputs=outputs, name='pointnet')
    intermediate_layer_model = keras.Model(inputs=model.input,
                                           outputs=model.get_layer(f'dense_1').output)
    intermediate_layer_model.load_weights(ckpt_path)
    return intermediate_layer_model
```

With the above model, we can then build our `pointnet` executor:

```python
class PNEncoder(Executor):
    def __init__(self, ckpt_path: str, **kwargs):
        super().__init__(**kwargs)
        self.embedding_model = get_model(ckpt_path=ckpt_path)

    @requests(on=['/index', '/search'])
    def encode(self, docs: DocumentArray, **kwargs):
        docs.embeddings = self.embedding_model.predict(docs.blobs)
```

```{admonition} Tips
:class: info
 Instead of iterating over each doc to set its embedding, we can directly get the blobs of all docs in `docs` at once by using the attribute `blobs` and set the embeddings of all docs in `docs` at once by using the attribute `embeddings`.
```


## Index the data

Let's also build an indexer to index the data.

```python
class MyIndexer(Executor):
    _docs = DocumentArray()

    @requests(on='/index')
    def index(self, docs: DocumentArray, **kwargs):
        self._docs.extend(docs)

    @requests(on='/search')
    def search(self, docs: DocumentArray, **kwargs):
        docs.match(self._docs, limit=5)
```

The above indexer simply uses `DocumentArray` to store all the index docs and leverages the `match` function of `DocumentArray` to match the query with docs indexed.

## Visualize 3D Model

Finally, let's also build the `GlbVisualizer` to visualize the results.

```python
import pyrender
import pyglet
from pyglet import clock
from pyglet.gl import Config
from pyrender import Viewer


def _init_and_start_app(self):
        TARGET_OPEN_GL_MAJOR = 4  # Target OpenGL Major Version
        TARGET_OPEN_GL_MINOR = 1
        MIN_OPEN_GL_MAJOR = 3     # Minimum OpenGL Major Version
        MIN_OPEN_GL_MINOR = 3     # Minimum OpenGL Minor Version
        confs = [Config(sample_buffers=1, samples=4,
                        depth_size=24,
                        double_buffer=True,
                        major_version=TARGET_OPEN_GL_MAJOR,
                        minor_version=TARGET_OPEN_GL_MINOR),
                 Config(depth_size=24,
                        double_buffer=True,
                        major_version=TARGET_OPEN_GL_MAJOR,
                        minor_version=TARGET_OPEN_GL_MINOR),
                 Config(sample_buffers=1, samples=4,
                        depth_size=24,
                        double_buffer=True,
                        major_version=MIN_OPEN_GL_MAJOR,
                        minor_version=MIN_OPEN_GL_MINOR),
                 Config(depth_size=24,
                        double_buffer=True,
                        major_version=MIN_OPEN_GL_MAJOR,
                        minor_version=MIN_OPEN_GL_MINOR)]
        for conf in confs:
            try:
                super(Viewer, self).__init__(config=conf, resizable=True,
                                             width=self._viewport_size[0],
                                             height=self._viewport_size[1])
                break
            except pyglet.window.NoSuchConfigException:
                pass

        if not self.context:
            raise ValueError('Unable to initialize an OpenGL 3+ context')

        clock.schedule_interval(
            Viewer._time_event, 1.0 / self.viewer_flags['refresh_rate'], self
        )
        self.switch_to()
        self.set_caption(self.viewer_flags['window_title'])


class GlbVisualizer:
    def __init__(self, search_doc, matches: Optional[List]=None):
        self.search_doc = search_doc
        self.matches = matches
        self.orig_func = pyrender.Viewer._init_and_start_app
        pyrender.Viewer._init_and_start_app = _init_and_start_app

    def visualize(self):
        self.add(self.search_doc.uri, 'Query Doc')
        if self.matches:
            for i, match in enumerate(self.matches, start=1):
                self.add(match.uri, f'Top {i} Match')
        pyglet.app.run()

    def add(self, uri, title):
        fuze_trimesh = as_mesh(trimesh.load(uri))
        mesh = pyrender.Mesh.from_trimesh(fuze_trimesh)
        scene = pyrender.Scene()
        scene.add(mesh)

        pyrender.Viewer(
            scene,
            use_raymond_lighting=True,
            viewer_flags={
                'rotate': True,
                'window_title': title, 
                'caption': [{
                    'font_name': 'OpenSans-Regular',
                    'font_pt': 30,
                    'color': None,
                    'scale': 1.0,
                    'location': 4,
                    'text': title
                }]
            },
        )
        
    def __del__(self):
        pyrender.Viewer._init_and_start_app = self.orig_func
```

The visualizer uses `pyrender` to render the query and match results. Since we want to display multiple models at once, we need to patch the `_init_and_start_app` function to delay the start of pyrender app after all viewers are initialized.


## Index, Search and Visualize Data

Download the pre-trained PNEncoder model [here](https://github.com/jina-ai/example-3D-model/tree/main/executors/pn_encoder/ckpt) into `model/ckpt`. Also, store the index/search data in `data/`. We can then put the executors into a flow and use the flow to perform indexing and searching. Finally, we use the `GlbVisualizer` built earlier to visualize our data.

```python
with Flow().add(uses=GlbCrafter).add(uses=PNEncoder, uses_with={'ckpt_path': 'model/ckpt/ckpt_True'}).add(uses=MyIndexer) as f:
    f.index(from_files('data/*.glb'))
    results = f.search(Document(uri='data/rifle_16.glb'), return_results=True)
    doc = results[0].docs[0]
    # visualize top 3 matches, since we also index query doc, exclude the top 1 match as it is the query doc
    visualizer = GlbVisualizer(doc, matches=doc.matches[1:4]).visualize()
```

This is how the flow we built looks like:
```{figure} flow.png
:align: center
```


## Putting it all together

Combining the steps listed above and import the necessary dependencies, the following is the complete code.

````{dropdown} Complete source code
```python
from typing import Optional, List

from jina import Flow, Executor, DocumentArray, Document, requests
from jina.types.document.generators import from_files
import trimesh

import pyrender
from pyrender import Viewer

# pyglet dependencies should be imported AFTER pyrender
import pyglet
from pyglet import clock
from pyglet.gl import Config


def as_mesh(scene: trimesh.Scene) -> Optional[trimesh.Trimesh]:
    if len(scene.geometry) == 0:
        return None
    return trimesh.util.concatenate(
        tuple(
            trimesh.Trimesh(vertices=g.vertices, faces=g.faces)
            for g in scene.geometry.values()
        )
    )


class GlbCrafter(Executor):
    @requests(on=['/index', '/search'])
    def craft(self, docs: DocumentArray, **kwargs):
        for d in docs:
            mesh = trimesh.load_mesh(d.uri)
            d.blob = as_mesh(trimesh.load_mesh(d.uri)).sample(2048)


def get_model(ckpt_path):
    import numpy as np
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers

    def conv_bn(x, filters):
        x = layers.Conv1D(filters, kernel_size=1, padding='valid')(x)
        x = layers.BatchNormalization(momentum=0.0)(x)
        return layers.Activation('relu')(x)

    def dense_bn(x, filters):
        x = layers.Dense(filters)(x)
        x = layers.BatchNormalization(momentum=0.0)(x)
        return layers.Activation('relu')(x)

    def tnet(inputs, num_features):
        class OrthogonalRegularizer(keras.regularizers.Regularizer):
            def __init__(self, num_features_, l2reg=0.001):
                self.num_features = num_features_
                self.l2reg = l2reg
                self.eye = tf.eye(self.num_features)

            def __call__(self, x):
                x = tf.reshape(x, (-1, self.num_features, self.num_features))
                xxt = tf.tensordot(x, x, axes=(2, 2))
                xxt = tf.reshape(xxt, (-1, self.num_features, self.num_features))
                return tf.reduce_sum(self.l2reg * tf.square(xxt - self.eye))

            def get_config(self):
                return {
                    'num_features': self.num_features,
                    'l2reg': self.l2reg,
                    'eye': self.eye.numpy(),
                }

        bias = keras.initializers.Constant(np.eye(num_features).flatten())
        reg = OrthogonalRegularizer(num_features)

        x = conv_bn(inputs, 32)
        x = conv_bn(x, 64)
        x = conv_bn(x, 512)
        x = layers.GlobalMaxPooling1D()(x)
        x = dense_bn(x, 256)
        x = dense_bn(x, 128)
        x = layers.Dense(
            num_features * num_features,
            kernel_initializer='zeros',
            bias_initializer=bias,
            activity_regularizer=reg,
        )(x)
        feat_T = layers.Reshape((num_features, num_features))(x)
        return layers.Dot(axes=(2, 1))([inputs, feat_T])

    inputs = keras.Input(shape=(2048, 3))
    x = tnet(inputs, 3)
    x = conv_bn(x, 32)
    x = conv_bn(x, 32)
    x = tnet(x, 32)
    x = conv_bn(x, 32)
    x = conv_bn(x, 64)
    x = layers.GlobalMaxPooling1D()(x)
    x = dense_bn(x, 128)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(1, activation='softmax')(x)
    model = keras.Model(inputs=inputs, outputs=outputs, name='pointnet')
    intermediate_layer_model = keras.Model(
        inputs=model.input, outputs=model.get_layer(f'dense_1').output
    )
    intermediate_layer_model.load_weights(ckpt_path)
    return intermediate_layer_model


class PNEncoder(Executor):
    def __init__(self, ckpt_path: str, **kwargs):
        super().__init__(**kwargs)
        self.embedding_model = get_model(ckpt_path=ckpt_path)

    @requests(on=['/index', '/search'])
    def encode(self, docs: DocumentArray, **kwargs):
        docs.embeddings = self.embedding_model.predict(docs.blobs)


class MyIndexer(Executor):
    _docs = DocumentArray()

    @requests(on='/index')
    def index(self, docs: DocumentArray, **kwargs):
        self._docs.extend(docs)

    @requests(on='/search')
    def search(self, docs: DocumentArray, **kwargs):
        docs.match(self._docs, limit=5)


def _init_and_start_app(self):
    TARGET_OPEN_GL_MAJOR = 4  # Target OpenGL Major Version
    TARGET_OPEN_GL_MINOR = 1
    MIN_OPEN_GL_MAJOR = 3  # Minimum OpenGL Major Version
    MIN_OPEN_GL_MINOR = 3  # Minimum OpenGL Minor Version
    confs = [
        Config(
            sample_buffers=1,
            samples=4,
            depth_size=24,
            double_buffer=True,
            major_version=TARGET_OPEN_GL_MAJOR,
            minor_version=TARGET_OPEN_GL_MINOR,
        ),
        Config(
            depth_size=24,
            double_buffer=True,
            major_version=TARGET_OPEN_GL_MAJOR,
            minor_version=TARGET_OPEN_GL_MINOR,
        ),
        Config(
            sample_buffers=1,
            samples=4,
            depth_size=24,
            double_buffer=True,
            major_version=MIN_OPEN_GL_MAJOR,
            minor_version=MIN_OPEN_GL_MINOR,
        ),
        Config(
            depth_size=24,
            double_buffer=True,
            major_version=MIN_OPEN_GL_MAJOR,
            minor_version=MIN_OPEN_GL_MINOR,
        ),
    ]
    for conf in confs:
        try:
            super(Viewer, self).__init__(
                config=conf,
                resizable=True,
                width=self._viewport_size[0],
                height=self._viewport_size[1],
            )
            break
        except pyglet.window.NoSuchConfigException:
            pass

    if not self.context:
        raise ValueError('Unable to initialize an OpenGL 3+ context')

    clock.schedule_interval(
        Viewer._time_event, 1.0 / self.viewer_flags['refresh_rate'], self
    )
    self.switch_to()
    self.set_caption(self.viewer_flags['window_title'])


class GlbVisualizer:
    def __init__(self, search_doc, matches: Optional[List] = None):
        self.search_doc = search_doc
        self.matches = matches
        self.orig_func = pyrender.Viewer._init_and_start_app
        pyrender.Viewer._init_and_start_app = _init_and_start_app

    def visualize(self):
        self.add(self.search_doc.uri, 'Query Doc')
        if self.matches:
            for i, match in enumerate(self.matches, start=1):
                self.add(match.uri, f'Top {i} Match')
        pyglet.app.run()

    def add(self, uri, title):
        scene = pyrender.Scene()
        scene.add(pyrender.Mesh.from_trimesh(as_mesh(trimesh.load(uri))))

        pyrender.Viewer(
            scene,
            use_raymond_lighting=True,
            viewer_flags={
                'rotate': True,
                'window_title': title,
                'caption': [
                    {
                        'font_name': 'OpenSans-Regular',
                        'font_pt': 30,
                        'color': None,
                        'scale': 1.0,
                        'location': 4,
                        'text': title,
                    }
                ],
            },
        )

    def __del__(self):
        pyrender.Viewer._init_and_start_app = self.orig_func


with Flow().add(uses=GlbCrafter).add(uses=PNEncoder, uses_with={'ckpt_path': 'model/ckpt/ckpt_True'}).add(uses=MyIndexer) as f:
    f.index(from_files('data/*.glb'))
    results = f.search(Document(uri='data/rifle_16.glb'), return_results=True)
    doc = results[0].docs[0]
    visualizer = GlbVisualizer(doc, matches=doc.matches[1:4]).visualize()
```
````


```{admonition} Import warning
:class: warning
Note, `pyrender` has to be imported before all `pyglet` dependencies, otherwise an error will be raised in some os environments such as Mac OS.
```

## Results

Now let's take a look at the search results! Below is the `rifle_16.glb` 3D model we would like to search for:

```{figure} query_doc.gif
:align: center
:scale: 55%
```


And the following are the top 3 matches:
```{figure} top_1.gif
:align: center
:scale: 55%
```

```{figure} top_2.gif
:align: center
:scale: 55%
```

```{figure} top_3.gif
:align: center
:scale: 55%
```

**Congratulations!** You have just built a 3D Mesh Search Pipeline!
