(mesh-type)=
# {octicon}`package` 3D Mesh

````{tip}

To enable the full feature of Document API on mesh data, you need to install `trimesh`.

```shell
pip install trimesh
```
````

A 3D mesh is the structural build of a 3D model consisting of polygons. Most 3D meshes are created via professional software packages, such as commercial suites like Unity, or the free open source Blender 3D. Neural search on 3D mesh can be both fun and practically useful: consider a game developer places a zombie into a scene, one can leverage Jina to find looks-alike monsters and put them in the scene to bring the terror to the next level.

```{figure} image45.gif
:align: center
:width: 50%
```

Before you start, let's recap some basic concepts of 3D mesh data and how Jina can help you process them.

## Vertices, edges and faces

A common misconception is that 3D model/mesh is just a set of points defined by (X, Y, Z) coordinates. That is not true, at least not the full story. 3D mesh is a collection of vertices, edges and faces that defines the shape of a polyhedral object. The faces usually consist of triangles since this simplifies rendering.  


```{figure} img.png
:align: center
:width: 50%
```

When we talk about simple 3D mesh data, there are three concepts you need to be aware of:

- **Vertex**: a (X, Y, Z) coordinate along with other meta information such as color, normal vector and texture.
- **Edge**: a connection between two vertices.
- **Face**: a closed set of edges, in which a triangle face has three edges.

Our intuition on storing (X, Y, Z) coordinates only corresponds to the vertex-vertex representation, which describes a 3D object as a set of vertices connected to other vertices. Despite its simplicity, vertex-vertex representation is not widely used since the face and edge information is implicit. Thus, it is necessary to traverse the data in order to generate a list of faces for rendering. In addition, operations on edges and faces are not easily accomplished.

## Common file formats

Due to the variety of mesh representations, there are many 3D files in the market: `.glb`, `gltf`, `.fbx`, `.obj` etc. Some of them are proprietary and hence Jina does not provide a loader for all of them.

## Point cloud

Point cloud is another representation of a 3D mesh. It is made by repeated and uniformly sampling points within the 3D body. Comparing to the mesh representation, point cloud is a fixed size ndarray and hence easier for deep learning algorithms to handle. In Jina, you can simply load a 3D mesh and convert it into a point cloud via:

```python
from jina import Document
doc = Document(uri='viking.glb').load_uri_to_point_cloud_blob(1000)

print(doc.blob)
```

```text
(1000, 3)
```

The following pictures depict a 3D mesh and a point cloud with 1000 samples from that 3D mesh. 

```{figure} 3dmesh-man.gif
:width: 50%
```

```{figure} pointcloud-man.gif
:width: 50%
```

```{toctree}
:hidden:

mesh-search
```
