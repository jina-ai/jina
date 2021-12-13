import numpy as np

from ...helper import T, deprecate_by


class MeshDataMixin:
    """Provide helper functions for :class:`Document` to support 3D mesh data and point cloud. """

    def load_uri_to_point_cloud_blob(
        self: T, samples: int, as_chunks: bool = False
    ) -> T:
        """Convert a 3d mesh-like :attr:`.uri` into :attr:`.blob`

        :param samples: number of points to sample from the mesh
        :param as_chunks: when multiple geometry stored in one mesh file,
            then store each geometry into different :attr:`.chunks`

        :return: itself after processed
        """
        import trimesh

        mesh = trimesh.load_mesh(self.uri).deduplicated()

        pcs = []
        for geo in mesh.geometry.values():
            geo: trimesh.Trimesh
            pcs.append(geo.sample(samples))

        if as_chunks:
            from . import Document

            for p in pcs:
                self.chunks.append(Document(blob=p))
        else:
            self.blob = np.stack(pcs).squeeze()
        return self

    convert_uri_to_point_cloud_blob = deprecate_by(load_uri_to_point_cloud_blob)
