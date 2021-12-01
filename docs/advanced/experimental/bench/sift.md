#### sift

<iframe width="600" height="400" style="border: 0" src="..\..\..\_static\indexers_benchmark_plots\sift-200000.html"></iframe>

<details>
<summary>Table</summary>
    
| name          | config                                                                                   |   time_search |    recall |
|:--------------|:-----------------------------------------------------------------------------------------|--------------:|----------:|
| Rii           | `{'subspaces': 32, 'codewords': 256, 'cluster_center': 1000, 'candidates': 10000}`       |        17.097 |     0.851 |
| Hnsw          | `{'max_connection': 16, 'ef_construction': 400, 'ef_query': 100, 'metric': 'euclidean'}` |        18.920 |     0.988 |
| Hnsw          | `{'max_connection': 48, 'ef_construction': 400, 'ef_query': 50, 'metric': 'euclidean'}`  |        18.964 |     0.996 |
| Hnsw          | `{'max_connection': 64, 'ef_construction': 200, 'ef_query': 50, 'metric': 'euclidean'}`  |        19.120 |     0.993 |
| Hnsw          | `{'max_connection': 64, 'ef_construction': 400, 'ef_query': 50, 'metric': 'euclidean'}`  |        19.130 |     0.996 |
| Hnsw          | `{'max_connection': 64, 'ef_construction': 200, 'ef_query': 100, 'metric': 'euclidean'}` |        19.140 |     0.993 |
| Hnsw          | `{'max_connection': 16, 'ef_construction': 200, 'ef_query': 100, 'metric': 'euclidean'}` |        19.153 |     0.987 |
| Hnsw          | `{'max_connection': 16, 'ef_construction': 400, 'ef_query': 50, 'metric': 'euclidean'}`  |        19.354 |     0.988 |
| Hnsw          | `{'max_connection': 16, 'ef_construction': 200, 'ef_query': 50, 'metric': 'euclidean'}`  |        19.389 |     0.986 |
| Hnsw          | `{'max_connection': 64, 'ef_construction': 400, 'ef_query': 100, 'metric': 'euclidean'}` |        19.587 |     0.996 |
| Hnsw          | `{'max_connection': 48, 'ef_construction': 200, 'ef_query': 50, 'metric': 'euclidean'}`  |        19.742 |     0.993 |
| Hnsw          | `{'max_connection': 48, 'ef_construction': 200, 'ef_query': 100, 'metric': 'euclidean'}` |        19.802 |     0.993 |
| Hnsw          | `{'max_connection': 48, 'ef_construction': 400, 'ef_query': 100, 'metric': 'euclidean'}` |        20.222 |     0.996 |
| Rii           | `{'subspaces': 32, 'codewords': 128, 'cluster_center': 5000, 'candidates': 50000}`       |        20.706 |     0.830 |
| Rii           | `{'subspaces': 32, 'codewords': 128, 'cluster_center': 1000, 'candidates': 10000}`       |        20.730 |     0.830 |
| Rii           | `{'subspaces': 32, 'codewords': 256, 'cluster_center': 5000, 'candidates': 50000}`       |        21.184 |     0.861 |
| Rii           | `{'subspaces': 64, 'codewords': 128, 'cluster_center': 5000, 'candidates': 10000}`       |        21.759 |     0.918 |
| Faiss         | `{'index_key': 'IVF128,PQ32', 'nprobe': 8, 'metric': 'euclidean'}`                       |        21.931 |     0.845 |
| Rii           | `{'subspaces': 64, 'codewords': 256, 'cluster_center': 1000, 'candidates': 50000}`       |        21.931 |     0.940 |
| Rii           | `{'subspaces': 64, 'codewords': 256, 'cluster_center': 1000, 'candidates': 10000}`       |        21.983 |     0.940 |
| Rii           | `{'subspaces': 64, 'codewords': 256, 'cluster_center': 5000, 'candidates': 50000}`       |        22.063 |     0.940 |
| Rii           | `{'subspaces': 128, 'codewords': 256, 'cluster_center': 1000, 'candidates': 10000}`      |        22.155 |     0.972 |
| Rii           | `{'subspaces': 64, 'codewords': 128, 'cluster_center': 5000, 'candidates': 50000}`       |        22.212 |     0.918 |
| Faiss         | `{'index_key': 'IVF512,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                       |        22.584 |     0.843 |
| Faiss         | `{'index_key': 'IVF1024,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                      |        22.835 |     0.794 |
| Rii           | `{'subspaces': 64, 'codewords': 256, 'cluster_center': 5000, 'candidates': 10000}`       |        23.079 |     0.940 |
| Faiss         | `{'index_key': 'IVF256,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                       |        23.150 |     0.896 |
| Faiss         | `{'index_key': 'IVF512,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                      |        23.151 |     0.935 |
| Faiss         | `{'index_key': 'IVF1024,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                     |        23.214 |     0.894 |
| Faiss         | `{'index_key': 'IVF128,PQ64', 'nprobe': 8, 'metric': 'euclidean'}`                       |        23.707 |     0.913 |
| Faiss         | `{'index_key': 'IVF128,PQ32', 'nprobe': 16, 'metric': 'euclidean'}`                      |        23.921 |     0.864 |
| Faiss         | `{'index_key': 'IVF128,PQ64', 'nprobe': 16, 'metric': 'euclidean'}`                      |        24.132 |     0.942 |
| Rii           | `{'subspaces': 128, 'codewords': 128, 'cluster_center': 5000, 'candidates': 10000}`      |        24.177 |     0.978 |
| Rii           | `{'subspaces': 128, 'codewords': 256, 'cluster_center': 1000, 'candidates': 50000}`      |        24.504 |     0.988 |
| Faiss         | `{'index_key': 'IVF128,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                       |        24.761 |     0.947 |
| Rii           | `{'subspaces': 128, 'codewords': 128, 'cluster_center': 1000, 'candidates': 50000}`      |        24.870 |     0.978 |
| Faiss         | `{'index_key': 'IVF256,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                      |        25.208 |     0.968 |
| Rii           | `{'subspaces': 128, 'codewords': 256, 'cluster_center': 5000, 'candidates': 10000}`      |        25.416 |     0.988 |
| Rii           | `{'subspaces': 32, 'codewords': 128, 'cluster_center': 1000, 'candidates': 50000}`       |        26.157 |     0.830 |
| Rii           | `{'subspaces': 32, 'codewords': 256, 'cluster_center': 5000, 'candidates': 10000}`       |        26.456 |     0.861 |
| Rii           | `{'subspaces': 32, 'codewords': 128, 'cluster_center': 5000, 'candidates': 10000}`       |        26.466 |     0.830 |
| Rii           | `{'subspaces': 32, 'codewords': 256, 'cluster_center': 1000, 'candidates': 50000}`       |        26.518 |     0.861 |
| Faiss         | `{'index_key': 'IVF128,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                      |        27.352 |     0.990 |
| Faiss         | `{'index_key': 'IVF128,SQ8', 'nprobe': 8, 'metric': 'euclidean'}`                        |        27.546 |     0.945 |
| Rii           | `{'subspaces': 64, 'codewords': 128, 'cluster_center': 1000, 'candidates': 50000}`       |        27.580 |     0.918 |
| Rii           | `{'subspaces': 64, 'codewords': 128, 'cluster_center': 1000, 'candidates': 10000}`       |        27.856 |     0.918 |
| Faiss         | `{'index_key': 'IVF64,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                        |        28.396 |     0.980 |
| Faiss         | `{'index_key': 'IVF128,SQ4', 'nprobe': 8, 'metric': 'euclidean'}`                        |        29.578 |     0.891 |
| Faiss         | `{'index_key': 'HNSW32', 'metric': 'euclidean'}`                                         |        30.087 |     0.786 |
| Rii           | `{'subspaces': 128, 'codewords': 128, 'cluster_center': 1000, 'candidates': 10000}`      |        30.393 |     0.978 |
| Rii           | `{'subspaces': 128, 'codewords': 128, 'cluster_center': 5000, 'candidates': 50000}`      |        31.381 |     0.978 |
| Rii           | `{'subspaces': 128, 'codewords': 256, 'cluster_center': 5000, 'candidates': 50000}`      |        31.918 |     0.988 |
| Faiss         | `{'index_key': 'IVF128,SQ8', 'nprobe': 16, 'metric': 'euclidean'}`                       |        34.857 |     0.987 |
| Faiss         | `{'index_key': 'IVF32,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                        |        36.722 |     0.996 |
| Faiss         | `{'index_key': 'IVF64,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                       |        37.934 |     0.999 |
| Faiss         | `{'index_key': 'IVF128,SQ4', 'nprobe': 16, 'metric': 'euclidean'}`                       |        38.875 |     0.916 |
| Faiss         | `{'index_key': 'IVF32,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                       |        46.228 |     1.000 |
| Faiss         | `{'index_key': 'Flat', 'metric': 'euclidean'}`                                           |        70.977 |     1.000 |
| SimpleIndexer | `{'match_args': {'metric': 'euclidean', 'only_id': True}}`                               |       266.892 |     1.000 |
</details>

<iframe width="600" height="400" style="border: 0" src="..\..\..\_static\indexers_benchmark_plots\sift-500000.html"></iframe>

<details>
<summary>Table</summary>
    
| name          | config                                                                                   |   time_search |    recall |
|:--------------|:-----------------------------------------------------------------------------------------|--------------:|----------:|
| Rii           | `{'subspaces': 32, 'codewords': 256, 'cluster_center': 1000, 'candidates': 10000}`       |        44.418 |     0.754 |
| Rii           | `{'subspaces': 32, 'codewords': 256, 'cluster_center': 5000, 'candidates': 10000}`       |        45.446 |     0.785 |
| Hnsw          | `{'max_connection': 16, 'ef_construction': 200, 'ef_query': 100, 'metric': 'euclidean'}` |        46.897 |     0.957 |
| Rii           | `{'subspaces': 32, 'codewords': 128, 'cluster_center': 1000, 'candidates': 10000}`       |        47.004 |     0.717 |
| Hnsw          | `{'max_connection': 16, 'ef_construction': 400, 'ef_query': 100, 'metric': 'euclidean'}` |        47.037 |     0.960 |
| Hnsw          | `{'max_connection': 16, 'ef_construction': 200, 'ef_query': 50, 'metric': 'euclidean'}`  |        47.297 |     0.957 |
| Hnsw          | `{'max_connection': 48, 'ef_construction': 200, 'ef_query': 100, 'metric': 'euclidean'}` |        47.597 |     0.978 |
| Hnsw          | `{'max_connection': 64, 'ef_construction': 200, 'ef_query': 50, 'metric': 'euclidean'}`  |        47.936 |     0.979 |
| Hnsw          | `{'max_connection': 16, 'ef_construction': 400, 'ef_query': 50, 'metric': 'euclidean'}`  |        48.202 |     0.960 |
| Hnsw          | `{'max_connection': 64, 'ef_construction': 400, 'ef_query': 50, 'metric': 'euclidean'}`  |        48.769 |     0.986 |
| Hnsw          | `{'max_connection': 64, 'ef_construction': 200, 'ef_query': 100, 'metric': 'euclidean'}` |        48.872 |     0.979 |
| Hnsw          | `{'max_connection': 48, 'ef_construction': 400, 'ef_query': 50, 'metric': 'euclidean'}`  |        48.937 |     0.986 |
| Hnsw          | `{'max_connection': 48, 'ef_construction': 400, 'ef_query': 100, 'metric': 'euclidean'}` |        49.309 |     0.986 |
| Rii           | `{'subspaces': 64, 'codewords': 256, 'cluster_center': 1000, 'candidates': 10000}`       |        50.132 |     0.849 |
| Hnsw          | `{'max_connection': 64, 'ef_construction': 400, 'ef_query': 100, 'metric': 'euclidean'}` |        50.298 |     0.986 |
| Hnsw          | `{'max_connection': 48, 'ef_construction': 200, 'ef_query': 50, 'metric': 'euclidean'}`  |        50.750 |     0.978 |
| Rii           | `{'subspaces': 64, 'codewords': 128, 'cluster_center': 5000, 'candidates': 10000}`       |        51.353 |     0.862 |
| Rii           | `{'subspaces': 64, 'codewords': 128, 'cluster_center': 1000, 'candidates': 10000}`       |        52.172 |     0.824 |
| Rii           | `{'subspaces': 64, 'codewords': 256, 'cluster_center': 5000, 'candidates': 10000}`       |        54.128 |     0.891 |
| Rii           | `{'subspaces': 128, 'codewords': 128, 'cluster_center': 5000, 'candidates': 10000}`      |        55.139 |     0.940 |
| Rii           | `{'subspaces': 128, 'codewords': 128, 'cluster_center': 1000, 'candidates': 10000}`      |        57.199 |     0.885 |
| Rii           | `{'subspaces': 32, 'codewords': 128, 'cluster_center': 1000, 'candidates': 50000}`       |        57.658 |     0.763 |
| Rii           | `{'subspaces': 128, 'codewords': 256, 'cluster_center': 1000, 'candidates': 10000}`      |        58.818 |     0.890 |
| Rii           | `{'subspaces': 32, 'codewords': 128, 'cluster_center': 5000, 'candidates': 50000}`       |        59.657 |     0.763 |
| Rii           | `{'subspaces': 32, 'codewords': 256, 'cluster_center': 5000, 'candidates': 50000}`       |        60.307 |     0.803 |
| Rii           | `{'subspaces': 128, 'codewords': 256, 'cluster_center': 5000, 'candidates': 10000}`      |        61.121 |     0.949 |
| Rii           | `{'subspaces': 64, 'codewords': 128, 'cluster_center': 5000, 'candidates': 50000}`       |        64.772 |     0.882 |
| Rii           | `{'subspaces': 64, 'codewords': 256, 'cluster_center': 5000, 'candidates': 50000}`       |        67.142 |     0.912 |
| Faiss         | `{'index_key': 'IVF1024,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                      |        68.208 |     0.749 |
| Faiss         | `{'index_key': 'IVF128,PQ32', 'nprobe': 8, 'metric': 'euclidean'}`                       |        68.521 |     0.788 |
| Faiss         | `{'index_key': 'IVF1024,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                     |        69.216 |     0.873 |
| Faiss         | `{'index_key': 'IVF512,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                       |        72.808 |     0.826 |
| Rii           | `{'subspaces': 32, 'codewords': 128, 'cluster_center': 5000, 'candidates': 10000}`       |        73.895 |     0.763 |
| Faiss         | `{'index_key': 'IVF256,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                       |        74.120 |     0.893 |
| Faiss         | `{'index_key': 'IVF128,PQ64', 'nprobe': 8, 'metric': 'euclidean'}`                       |        75.032 |     0.887 |
| Rii           | `{'subspaces': 32, 'codewords': 256, 'cluster_center': 1000, 'candidates': 50000}`       |        75.734 |     0.803 |
| Faiss         | `{'index_key': 'IVF512,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                      |        76.672 |     0.930 |
| Faiss         | `{'index_key': 'IVF128,PQ32', 'nprobe': 16, 'metric': 'euclidean'}`                      |        78.513 |     0.805 |
| Rii           | `{'subspaces': 128, 'codewords': 128, 'cluster_center': 1000, 'candidates': 50000}`      |        79.814 |     0.970 |
| Faiss         | `{'index_key': 'IVF128,PQ64', 'nprobe': 16, 'metric': 'euclidean'}`                      |        80.495 |     0.914 |
| Rii           | `{'subspaces': 64, 'codewords': 128, 'cluster_center': 1000, 'candidates': 50000}`       |        81.776 |     0.882 |
| Rii           | `{'subspaces': 128, 'codewords': 128, 'cluster_center': 5000, 'candidates': 50000}`      |        82.068 |     0.970 |
| Rii           | `{'subspaces': 64, 'codewords': 256, 'cluster_center': 1000, 'candidates': 50000}`       |        83.783 |     0.912 |
| Rii           | `{'subspaces': 128, 'codewords': 256, 'cluster_center': 5000, 'candidates': 50000}`      |        83.940 |     0.982 |
| Faiss         | `{'index_key': 'IVF128,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                       |        84.118 |     0.944 |
| Faiss         | `{'index_key': 'HNSW32', 'metric': 'euclidean'}`                                         |        84.434 |     0.638 |
| Faiss         | `{'index_key': 'IVF256,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                      |        88.011 |     0.969 |
| Faiss         | `{'index_key': 'IVF128,SQ8', 'nprobe': 8, 'metric': 'euclidean'}`                        |       103.199 |     0.941 |
| Rii           | `{'subspaces': 128, 'codewords': 256, 'cluster_center': 1000, 'candidates': 50000}`      |       106.225 |     0.982 |
| Faiss         | `{'index_key': 'IVF64,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                        |       110.428 |     0.982 |
| Faiss         | `{'index_key': 'IVF128,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                      |       112.318 |     0.990 |
| Faiss         | `{'index_key': 'IVF128,SQ4', 'nprobe': 8, 'metric': 'euclidean'}`                        |       120.859 |     0.855 |
| Faiss         | `{'index_key': 'IVF128,SQ8', 'nprobe': 16, 'metric': 'euclidean'}`                       |       141.645 |     0.985 |
| Faiss         | `{'index_key': 'IVF64,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                       |       146.081 |     0.999 |
| Faiss         | `{'index_key': 'IVF32,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                        |       146.651 |     0.997 |
| Faiss         | `{'index_key': 'IVF128,SQ4', 'nprobe': 16, 'metric': 'euclidean'}`                       |       164.157 |     0.879 |
| Faiss         | `{'index_key': 'IVF32,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                       |       221.713 |     1.000 |
| Faiss         | `{'index_key': 'Flat', 'metric': 'euclidean'}`                                           |       361.638 |     1.000 |
| SimpleIndexer | `{'match_args': {'metric': 'euclidean', 'only_id': True}}`                               |      1324.322 |     1.000 |
</details>

<iframe width="600" height="400" style="border: 0" src="..\..\..\_static\indexers_benchmark_plots\sift-1m.html"></iframe>

<details>
<summary>Table</summary>
    
| name          | config                                                                                   |   time_search |    recall |
|:--------------|:-----------------------------------------------------------------------------------------|--------------:|----------:|
| Rii           | `{'subspaces': 32, 'codewords': 128, 'cluster_center': 5000, 'candidates': 10000}`       |        94.363 |     0.677 |
| Hnsw          | `{'max_connection': 16, 'ef_construction': 200, 'ef_query': 50, 'metric': 'euclidean'}`  |        94.770 |     0.923 |
| Rii           | `{'subspaces': 32, 'codewords': 256, 'cluster_center': 5000, 'candidates': 10000}`       |        94.798 |     0.719 |
| Hnsw          | `{'max_connection': 16, 'ef_construction': 400, 'ef_query': 50, 'metric': 'euclidean'}`  |        95.335 |     0.926 |
| Hnsw          | `{'max_connection': 16, 'ef_construction': 400, 'ef_query': 100, 'metric': 'euclidean'}` |        95.673 |     0.926 |
| Hnsw          | `{'max_connection': 64, 'ef_construction': 200, 'ef_query': 50, 'metric': 'euclidean'}`  |        96.769 |     0.963 |
| Hnsw          | `{'max_connection': 48, 'ef_construction': 400, 'ef_query': 50, 'metric': 'euclidean'}`  |        96.972 |     0.973 |
| Rii           | `{'subspaces': 32, 'codewords': 256, 'cluster_center': 1000, 'candidates': 10000}`       |        96.997 |     0.658 |
| Hnsw          | `{'max_connection': 64, 'ef_construction': 400, 'ef_query': 100, 'metric': 'euclidean'}` |        97.110 |     0.974 |
| Hnsw          | `{'max_connection': 64, 'ef_construction': 200, 'ef_query': 100, 'metric': 'euclidean'}` |        97.228 |     0.963 |
| Hnsw          | `{'max_connection': 48, 'ef_construction': 200, 'ef_query': 50, 'metric': 'euclidean'}`  |        97.376 |     0.962 |
| Rii           | `{'subspaces': 32, 'codewords': 128, 'cluster_center': 1000, 'candidates': 10000}`       |        97.391 |     0.620 |
| Hnsw          | `{'max_connection': 16, 'ef_construction': 200, 'ef_query': 100, 'metric': 'euclidean'}` |        97.518 |     0.923 |
| Hnsw          | `{'max_connection': 48, 'ef_construction': 200, 'ef_query': 100, 'metric': 'euclidean'}` |        97.880 |     0.962 |
| Rii           | `{'subspaces': 64, 'codewords': 128, 'cluster_center': 1000, 'candidates': 10000}`       |       100.554 |     0.724 |
| Hnsw          | `{'max_connection': 64, 'ef_construction': 400, 'ef_query': 50, 'metric': 'euclidean'}`  |       101.271 |     0.974 |
| Hnsw          | `{'max_connection': 48, 'ef_construction': 400, 'ef_query': 100, 'metric': 'euclidean'}` |       103.660 |     0.973 |
| Rii           | `{'subspaces': 64, 'codewords': 256, 'cluster_center': 1000, 'candidates': 10000}`       |       105.981 |     0.744 |
| Rii           | `{'subspaces': 64, 'codewords': 128, 'cluster_center': 5000, 'candidates': 10000}`       |       110.398 |     0.799 |
| Rii           | `{'subspaces': 64, 'codewords': 256, 'cluster_center': 5000, 'candidates': 10000}`       |       110.678 |     0.829 |
| Rii           | `{'subspaces': 128, 'codewords': 128, 'cluster_center': 5000, 'candidates': 10000}`      |       112.749 |     0.872 |
| Rii           | `{'subspaces': 128, 'codewords': 256, 'cluster_center': 5000, 'candidates': 10000}`      |       115.281 |     0.878 |
| Rii           | `{'subspaces': 128, 'codewords': 128, 'cluster_center': 1000, 'candidates': 10000}`      |       115.651 |     0.771 |
| Rii           | `{'subspaces': 128, 'codewords': 256, 'cluster_center': 1000, 'candidates': 10000}`      |       116.964 |     0.775 |
| Rii           | `{'subspaces': 32, 'codewords': 128, 'cluster_center': 5000, 'candidates': 50000}`       |       141.953 |     0.720 |
| Rii           | `{'subspaces': 32, 'codewords': 256, 'cluster_center': 1000, 'candidates': 50000}`       |       149.069 |     0.768 |
| Rii           | `{'subspaces': 64, 'codewords': 128, 'cluster_center': 5000, 'candidates': 50000}`       |       167.034 |     0.860 |
| Rii           | `{'subspaces': 32, 'codewords': 256, 'cluster_center': 5000, 'candidates': 50000}`       |       176.633 |     0.768 |
| Faiss         | `{'index_key': 'IVF128,PQ32', 'nprobe': 8, 'metric': 'euclidean'}`                       |       177.007 |     0.748 |
| Rii           | `{'subspaces': 32, 'codewords': 128, 'cluster_center': 1000, 'candidates': 50000}`       |       180.531 |     0.720 |
| Faiss         | `{'index_key': 'IVF512,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                       |       181.653 |     0.832 |
| Faiss         | `{'index_key': 'IVF1024,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                      |       184.510 |     0.756 |
| Faiss         | `{'index_key': 'IVF1024,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                     |       185.060 |     0.878 |
| Faiss         | `{'index_key': 'IVF128,PQ32', 'nprobe': 16, 'metric': 'euclidean'}`                      |       193.135 |     0.763 |
| Faiss         | `{'index_key': 'IVF128,PQ64', 'nprobe': 8, 'metric': 'euclidean'}`                       |       203.210 |     0.869 |
| Faiss         | `{'index_key': 'IVF512,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                      |       207.564 |     0.932 |
| Faiss         | `{'index_key': 'IVF256,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                       |       208.289 |     0.895 |
| Rii           | `{'subspaces': 64, 'codewords': 256, 'cluster_center': 1000, 'candidates': 50000}`       |       209.611 |     0.896 |
| Faiss         | `{'index_key': 'HNSW32', 'metric': 'euclidean'}`                                         |       211.001 |     0.616 |
| Rii           | `{'subspaces': 64, 'codewords': 128, 'cluster_center': 1000, 'candidates': 50000}`       |       212.089 |     0.860 |
| Rii           | `{'subspaces': 64, 'codewords': 256, 'cluster_center': 5000, 'candidates': 50000}`       |       215.622 |     0.896 |
| Rii           | `{'subspaces': 128, 'codewords': 128, 'cluster_center': 1000, 'candidates': 50000}`      |       224.690 |     0.961 |
| Faiss         | `{'index_key': 'IVF128,PQ64', 'nprobe': 16, 'metric': 'euclidean'}`                      |       227.490 |     0.894 |
| Rii           | `{'subspaces': 128, 'codewords': 128, 'cluster_center': 5000, 'candidates': 50000}`      |       234.007 |     0.957 |
| Faiss         | `{'index_key': 'IVF256,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                      |       250.604 |     0.968 |
| Faiss         | `{'index_key': 'IVF128,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                       |       259.265 |     0.946 |
| Rii           | `{'subspaces': 128, 'codewords': 256, 'cluster_center': 1000, 'candidates': 50000}`      |       281.552 |     0.977 |
| Rii           | `{'subspaces': 128, 'codewords': 256, 'cluster_center': 5000, 'candidates': 50000}`      |       282.742 |     0.977 |
| Faiss         | `{'index_key': 'IVF128,SQ8', 'nprobe': 8, 'metric': 'euclidean'}`                        |       322.146 |     0.941 |
| Faiss         | `{'index_key': 'IVF128,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                      |       332.204 |     0.990 |
| Faiss         | `{'index_key': 'IVF64,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                        |       359.077 |     0.982 |
| Faiss         | `{'index_key': 'IVF128,SQ4', 'nprobe': 8, 'metric': 'euclidean'}`                        |       383.529 |     0.832 |
| Faiss         | `{'index_key': 'IVF128,SQ8', 'nprobe': 16, 'metric': 'euclidean'}`                       |       468.810 |     0.983 |
| Faiss         | `{'index_key': 'IVF32,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                        |       504.964 |     0.996 |
| Faiss         | `{'index_key': 'IVF64,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                       |       535.492 |     0.999 |
| Faiss         | `{'index_key': 'IVF128,SQ4', 'nprobe': 16, 'metric': 'euclidean'}`                       |       562.634 |     0.854 |
| Faiss         | `{'index_key': 'IVF32,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                       |       834.854 |     1.000 |
| Faiss         | `{'index_key': 'Flat', 'metric': 'euclidean'}`                                           |      1437.081 |     1.000 |
| SimpleIndexer | `{'match_args': {'metric': 'euclidean', 'only_id': True}}`                               |      4843.714 |     1.000 |
</details>
