#### gist

<iframe width="600" height="400" style="border: 0" src="..\..\..\_static\indexers_benchmark_plots\gist-200000.html"></iframe>

<details>
<summary>Table</summary>
    
| name   | config                                                                                   |   time_search |   recall |
|:-------|:-----------------------------------------------------------------------------------------|--------------:|---------:|
| Hnsw   | `{'max_connection': 16, 'ef_construction': 200, 'ef_query': 50, 'metric': 'euclidean'}`  |        10.115 |    0.857 |
| Rii    | `{'subspaces': 96, 'codewords': 256, 'cluster_center': 5000, 'candidates': 10000}`       |        10.238 |    0.671 |
| Hnsw   | `{'max_connection': 16, 'ef_construction': 400, 'ef_query': 100, 'metric': 'euclidean'}` |        10.266 |    0.878 |
| Hnsw   | `{'max_connection': 16, 'ef_construction': 400, 'ef_query': 50, 'metric': 'euclidean'}`  |        10.280 |    0.879 |
| Hnsw   | `{'max_connection': 64, 'ef_construction': 200, 'ef_query': 100, 'metric': 'euclidean'}` |        10.475 |    0.914 |
| Hnsw   | `{'max_connection': 16, 'ef_construction': 200, 'ef_query': 100, 'metric': 'euclidean'}` |        10.515 |    0.858 |
| Hnsw   | `{'max_connection': 64, 'ef_construction': 400, 'ef_query': 100, 'metric': 'euclidean'}` |        10.663 |    0.943 |
| Hnsw   | `{'max_connection': 48, 'ef_construction': 400, 'ef_query': 100, 'metric': 'euclidean'}` |        10.693 |    0.939 |
| Rii    | `{'subspaces': 64, 'codewords': 128, 'cluster_center': 5000, 'candidates': 50000}`       |        10.872 |    0.561 |
| Hnsw   | `{'max_connection': 48, 'ef_construction': 200, 'ef_query': 50, 'metric': 'euclidean'}`  |        10.890 |    0.911 |
| Hnsw   | `{'max_connection': 64, 'ef_construction': 200, 'ef_query': 50, 'metric': 'euclidean'}`  |        10.893 |    0.914 |
| Rii    | `{'subspaces': 64, 'codewords': 128, 'cluster_center': 1000, 'candidates': 50000}`       |        11.065 |    0.561 |
| Rii    | `{'subspaces': 64, 'codewords': 128, 'cluster_center': 1000, 'candidates': 10000}`       |        11.068 |    0.561 |
| Hnsw   | `{'max_connection': 48, 'ef_construction': 400, 'ef_query': 50, 'metric': 'euclidean'}`  |        11.090 |    0.939 |
| Rii    | `{'subspaces': 192, 'codewords': 256, 'cluster_center': 1000, 'candidates': 10000}`      |        11.244 |    0.768 |
| Rii    | `{'subspaces': 64, 'codewords': 256, 'cluster_center': 1000, 'candidates': 10000}`       |        11.286 |    0.611 |
| Hnsw   | `{'max_connection': 64, 'ef_construction': 400, 'ef_query': 50, 'metric': 'euclidean'}`  |        11.306 |    0.942 |
| Hnsw   | `{'max_connection': 48, 'ef_construction': 200, 'ef_query': 100, 'metric': 'euclidean'}` |        11.324 |    0.911 |
| Rii    | `{'subspaces': 64, 'codewords': 256, 'cluster_center': 5000, 'candidates': 10000}`       |        11.476 |    0.611 |
| Rii    | `{'subspaces': 192, 'codewords': 128, 'cluster_center': 1000, 'candidates': 10000}`      |        11.494 |    0.737 |
| Rii    | `{'subspaces': 96, 'codewords': 128, 'cluster_center': 1000, 'candidates': 50000}`       |        11.672 |    0.649 |
| Faiss  | `{'index_key': 'IVF128,PQ32', 'nprobe': 8, 'metric': 'euclidean'}`                       |        11.987 |    0.499 |
| Rii    | `{'subspaces': 120, 'codewords': 256, 'cluster_center': 5000, 'candidates': 50000}`      |        12.102 |    0.736 |
| Rii    | `{'subspaces': 96, 'codewords': 128, 'cluster_center': 1000, 'candidates': 10000}`       |        12.108 |    0.649 |
| Rii    | `{'subspaces': 96, 'codewords': 256, 'cluster_center': 1000, 'candidates': 50000}`       |        12.128 |    0.697 |
| Rii    | `{'subspaces': 120, 'codewords': 256, 'cluster_center': 1000, 'candidates': 50000}`      |        12.303 |    0.736 |
| Faiss  | `{'index_key': 'IVF128,PQ64', 'nprobe': 8, 'metric': 'euclidean'}`                       |        12.377 |    0.583 |
| Faiss  | `{'index_key': 'IVF128,PQ32', 'nprobe': 16, 'metric': 'euclidean'}`                      |        12.391 |    0.510 |
| Rii    | `{'subspaces': 120, 'codewords': 256, 'cluster_center': 1000, 'candidates': 10000}`      |        12.539 |    0.736 |
| Rii    | `{'subspaces': 120, 'codewords': 256, 'cluster_center': 5000, 'candidates': 10000}`      |        12.566 |    0.736 |
| Rii    | `{'subspaces': 192, 'codewords': 128, 'cluster_center': 5000, 'candidates': 10000}`      |        13.361 |    0.802 |
| Rii    | `{'subspaces': 192, 'codewords': 128, 'cluster_center': 5000, 'candidates': 50000}`      |        13.549 |    0.802 |
| Rii    | `{'subspaces': 192, 'codewords': 256, 'cluster_center': 5000, 'candidates': 10000}`      |        13.746 |    0.838 |
| Faiss  | `{'index_key': 'IVF128,PQ64', 'nprobe': 16, 'metric': 'euclidean'}`                      |        13.781 |    0.599 |
| Rii    | `{'subspaces': 64, 'codewords': 256, 'cluster_center': 1000, 'candidates': 50000}`       |        13.854 |    0.611 |
| Rii    | `{'subspaces': 64, 'codewords': 128, 'cluster_center': 5000, 'candidates': 10000}`       |        13.854 |    0.561 |
| Rii    | `{'subspaces': 192, 'codewords': 256, 'cluster_center': 1000, 'candidates': 50000}`      |        13.946 |    0.838 |
| Rii    | `{'subspaces': 120, 'codewords': 128, 'cluster_center': 1000, 'candidates': 50000}`      |        14.659 |    0.689 |
| Rii    | `{'subspaces': 96, 'codewords': 128, 'cluster_center': 5000, 'candidates': 10000}`       |        14.734 |    0.649 |
| Rii    | `{'subspaces': 120, 'codewords': 128, 'cluster_center': 5000, 'candidates': 50000}`      |        15.036 |    0.689 |
| Rii    | `{'subspaces': 96, 'codewords': 128, 'cluster_center': 5000, 'candidates': 50000}`       |        15.058 |    0.649 |
| Faiss  | `{'index_key': 'IVF1024,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                      |        15.182 |    0.617 |
| Rii    | `{'subspaces': 96, 'codewords': 256, 'cluster_center': 5000, 'candidates': 50000}`       |        15.293 |    0.697 |
| Rii    | `{'subspaces': 120, 'codewords': 128, 'cluster_center': 1000, 'candidates': 10000}`      |        15.488 |    0.689 |
| Rii    | `{'subspaces': 120, 'codewords': 128, 'cluster_center': 5000, 'candidates': 10000}`      |        15.681 |    0.689 |
| Rii    | `{'subspaces': 96, 'codewords': 256, 'cluster_center': 1000, 'candidates': 10000}`       |        15.795 |    0.697 |
| Faiss  | `{'index_key': 'IVF512,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                       |        16.567 |    0.693 |
| Rii    | `{'subspaces': 192, 'codewords': 128, 'cluster_center': 1000, 'candidates': 50000}`      |        16.810 |    0.802 |
| Faiss  | `{'index_key': 'HNSW32', 'metric': 'euclidean'}`                                         |        17.420 |    0.601 |
| Rii    | `{'subspaces': 192, 'codewords': 256, 'cluster_center': 5000, 'candidates': 50000}`      |        17.559 |    0.838 |
| Faiss  | `{'index_key': 'IVF1024,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                     |        18.035 |    0.765 |
| Rii    | `{'subspaces': 64, 'codewords': 256, 'cluster_center': 5000, 'candidates': 50000}`       |        18.488 |    0.611 |
| Faiss  | `{'index_key': 'IVF512,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                      |        21.598 |    0.832 |
| Faiss  | `{'index_key': 'IVF256,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                       |        23.483 |    0.788 |
| Faiss  | `{'index_key': 'IVF128,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                       |        30.475 |    0.862 |
| Faiss  | `{'index_key': 'IVF256,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                      |        31.892 |    0.911 |
| Faiss  | `{'index_key': 'IVF128,SQ8', 'nprobe': 8, 'metric': 'euclidean'}`                        |        42.589 |    0.861 |
| Faiss  | `{'index_key': 'IVF64,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                        |        48.416 |    0.926 |
| Faiss  | `{'index_key': 'IVF128,SQ4', 'nprobe': 8, 'metric': 'euclidean'}`                        |        51.615 |    0.802 |
| Faiss  | `{'index_key': 'IVF128,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                      |        51.866 |    0.959 |
| Faiss  | `{'index_key': 'IVF128,SQ8', 'nprobe': 16, 'metric': 'euclidean'}`                       |        69.125 |    0.956 |
| Faiss  | `{'index_key': 'IVF64,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                       |        85.781 |    0.988 |
| Faiss  | `{'index_key': 'IVF32,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                        |        85.789 |    0.981 |
| Faiss  | `{'index_key': 'IVF128,SQ4', 'nprobe': 16, 'metric': 'euclidean'}`                       |        86.327 |    0.862 |
| Faiss  | `{'index_key': 'IVF32,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                       |       148.602 |    1.000 |
| Faiss  | `{'index_key': 'Flat', 'metric': 'euclidean'}`                                           |       241.103 |    1.000 |
</details>

<iframe width="600" height="400" style="border: 0" src="..\..\..\_static\indexers_benchmark_plots\gist-500000.html"></iframe>

<details>
<summary>Table</summary>
    
| name   | config                                                                                   |   time_search |   recall |
|:-------|:-----------------------------------------------------------------------------------------|--------------:|---------:|
| Rii    | `{'subspaces': 64, 'codewords': 128, 'cluster_center': 1000, 'candidates': 10000}`       |         9.639 |    0.381 |
| Rii    | `{'subspaces': 64, 'codewords': 256, 'cluster_center': 5000, 'candidates': 10000}`       |        10.052 |    0.458 |
| Rii    | `{'subspaces': 120, 'codewords': 128, 'cluster_center': 1000, 'candidates': 10000}`      |        10.241 |    0.482 |
| Hnsw   | `{'max_connection': 16, 'ef_construction': 200, 'ef_query': 50, 'metric': 'euclidean'}`  |        10.260 |    0.786 |
| Hnsw   | `{'max_connection': 16, 'ef_construction': 200, 'ef_query': 100, 'metric': 'euclidean'}` |        10.271 |    0.785 |
| Rii    | `{'subspaces': 64, 'codewords': 128, 'cluster_center': 5000, 'candidates': 10000}`       |        10.456 |    0.413 |
| Rii    | `{'subspaces': 96, 'codewords': 256, 'cluster_center': 5000, 'candidates': 10000}`       |        10.460 |    0.538 |
| Hnsw   | `{'max_connection': 16, 'ef_construction': 400, 'ef_query': 100, 'metric': 'euclidean'}` |        10.464 |    0.807 |
| Rii    | `{'subspaces': 96, 'codewords': 256, 'cluster_center': 1000, 'candidates': 10000}`       |        10.478 |    0.490 |
| Rii    | `{'subspaces': 64, 'codewords': 256, 'cluster_center': 1000, 'candidates': 10000}`       |        10.685 |    0.422 |
| Hnsw   | `{'max_connection': 16, 'ef_construction': 400, 'ef_query': 50, 'metric': 'euclidean'}`  |        10.712 |    0.807 |
| Hnsw   | `{'max_connection': 48, 'ef_construction': 200, 'ef_query': 50, 'metric': 'euclidean'}`  |        10.862 |    0.867 |
| Rii    | `{'subspaces': 120, 'codewords': 256, 'cluster_center': 5000, 'candidates': 10000}`      |        10.865 |    0.576 |
| Rii    | `{'subspaces': 96, 'codewords': 128, 'cluster_center': 5000, 'candidates': 10000}`       |        10.869 |    0.495 |
| Hnsw   | `{'max_connection': 64, 'ef_construction': 200, 'ef_query': 100, 'metric': 'euclidean'}` |        10.893 |    0.874 |
| Hnsw   | `{'max_connection': 48, 'ef_construction': 400, 'ef_query': 100, 'metric': 'euclidean'}` |        11.052 |    0.903 |
| Hnsw   | `{'max_connection': 48, 'ef_construction': 200, 'ef_query': 100, 'metric': 'euclidean'}` |        11.095 |    0.868 |
| Rii    | `{'subspaces': 120, 'codewords': 128, 'cluster_center': 5000, 'candidates': 10000}`      |        11.211 |    0.530 |
| Hnsw   | `{'max_connection': 64, 'ef_construction': 400, 'ef_query': 50, 'metric': 'euclidean'}`  |        11.280 |    0.910 |
| Hnsw   | `{'max_connection': 64, 'ef_construction': 200, 'ef_query': 50, 'metric': 'euclidean'}`  |        11.297 |    0.874 |
| Rii    | `{'subspaces': 120, 'codewords': 256, 'cluster_center': 1000, 'candidates': 10000}`      |        11.306 |    0.518 |
| Hnsw   | `{'max_connection': 64, 'ef_construction': 400, 'ef_query': 100, 'metric': 'euclidean'}` |        11.306 |    0.910 |
| Rii    | `{'subspaces': 96, 'codewords': 128, 'cluster_center': 1000, 'candidates': 10000}`       |        11.320 |    0.452 |
| Hnsw   | `{'max_connection': 48, 'ef_construction': 400, 'ef_query': 50, 'metric': 'euclidean'}`  |        11.523 |    0.903 |
| Rii    | `{'subspaces': 192, 'codewords': 256, 'cluster_center': 1000, 'candidates': 10000}`      |        11.656 |    0.601 |
| Rii    | `{'subspaces': 192, 'codewords': 128, 'cluster_center': 1000, 'candidates': 10000}`      |        11.891 |    0.569 |
| Rii    | `{'subspaces': 192, 'codewords': 128, 'cluster_center': 5000, 'candidates': 10000}`      |        12.490 |    0.641 |
| Rii    | `{'subspaces': 64, 'codewords': 128, 'cluster_center': 1000, 'candidates': 50000}`       |        13.155 |    0.455 |
| Rii    | `{'subspaces': 192, 'codewords': 256, 'cluster_center': 5000, 'candidates': 10000}`      |        13.702 |    0.681 |
| Faiss  | `{'index_key': 'IVF128,PQ32', 'nprobe': 8, 'metric': 'euclidean'}`                       |        14.883 |    0.408 |
| Rii    | `{'subspaces': 96, 'codewords': 256, 'cluster_center': 1000, 'candidates': 50000}`       |        15.369 |    0.608 |
| Rii    | `{'subspaces': 120, 'codewords': 128, 'cluster_center': 5000, 'candidates': 50000}`      |        15.470 |    0.596 |
| Faiss  | `{'index_key': 'IVF128,PQ64', 'nprobe': 8, 'metric': 'euclidean'}`                       |        15.670 |    0.500 |
| Rii    | `{'subspaces': 96, 'codewords': 256, 'cluster_center': 5000, 'candidates': 50000}`       |        15.958 |    0.608 |
| Rii    | `{'subspaces': 120, 'codewords': 256, 'cluster_center': 1000, 'candidates': 50000}`      |        15.966 |    0.654 |
| Rii    | `{'subspaces': 64, 'codewords': 128, 'cluster_center': 5000, 'candidates': 50000}`       |        16.701 |    0.455 |
| Faiss  | `{'index_key': 'IVF128,PQ32', 'nprobe': 16, 'metric': 'euclidean'}`                      |        16.733 |    0.415 |
| Rii    | `{'subspaces': 64, 'codewords': 256, 'cluster_center': 5000, 'candidates': 50000}`       |        16.917 |    0.508 |
| Rii    | `{'subspaces': 64, 'codewords': 256, 'cluster_center': 1000, 'candidates': 50000}`       |        17.995 |    0.508 |
| Rii    | `{'subspaces': 96, 'codewords': 128, 'cluster_center': 5000, 'candidates': 50000}`       |        18.159 |    0.554 |
| Rii    | `{'subspaces': 96, 'codewords': 128, 'cluster_center': 1000, 'candidates': 50000}`       |        18.497 |    0.554 |
| Faiss  | `{'index_key': 'IVF128,PQ64', 'nprobe': 16, 'metric': 'euclidean'}`                      |        18.524 |    0.512 |
| Rii    | `{'subspaces': 192, 'codewords': 128, 'cluster_center': 5000, 'candidates': 50000}`      |        19.309 |    0.736 |
| Rii    | `{'subspaces': 120, 'codewords': 256, 'cluster_center': 5000, 'candidates': 50000}`      |        19.466 |    0.654 |
| Rii    | `{'subspaces': 192, 'codewords': 256, 'cluster_center': 5000, 'candidates': 50000}`      |        20.501 |    0.786 |
| Faiss  | `{'index_key': 'IVF1024,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                      |        22.263 |    0.589 |
| Rii    | `{'subspaces': 192, 'codewords': 128, 'cluster_center': 1000, 'candidates': 50000}`      |        22.674 |    0.736 |
| Rii    | `{'subspaces': 192, 'codewords': 256, 'cluster_center': 1000, 'candidates': 50000}`      |        24.885 |    0.786 |
| Faiss  | `{'index_key': 'IVF512,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                       |        27.338 |    0.676 |
| Faiss  | `{'index_key': 'IVF1024,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                     |        27.682 |    0.741 |
| Faiss  | `{'index_key': 'IVF256,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                       |        39.996 |    0.779 |
| Faiss  | `{'index_key': 'IVF512,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                      |        42.739 |    0.828 |
| Faiss  | `{'index_key': 'IVF128,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                       |        61.930 |    0.856 |
| Faiss  | `{'index_key': 'IVF256,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                      |        65.994 |    0.910 |
| Faiss  | `{'index_key': 'IVF128,SQ8', 'nprobe': 8, 'metric': 'euclidean'}`                        |        86.940 |    0.854 |
| Faiss  | `{'index_key': 'IVF64,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                        |       106.795 |    0.926 |
| Faiss  | `{'index_key': 'IVF128,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                      |       108.918 |    0.956 |
| Faiss  | `{'index_key': 'IVF128,SQ4', 'nprobe': 8, 'metric': 'euclidean'}`                        |       116.630 |    0.778 |
| Faiss  | `{'index_key': 'IVF128,SQ8', 'nprobe': 16, 'metric': 'euclidean'}`                       |       169.056 |    0.952 |
| Faiss  | `{'index_key': 'IVF32,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                        |       193.191 |    0.974 |
| Faiss  | `{'index_key': 'IVF64,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                       |       205.614 |    0.989 |
| Faiss  | `{'index_key': 'IVF128,SQ4', 'nprobe': 16, 'metric': 'euclidean'}`                       |       218.027 |    0.836 |
| Faiss  | `{'index_key': 'IVF32,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                       |       337.916 |    0.999 |
| Faiss  | `{'index_key': 'Flat', 'metric': 'euclidean'}`                                           |       578.059 |    1.000 |
</details>

<iframe width="600" height="400" style="border: 0" src="..\..\..\_static\indexers_benchmark_plots\gist-1m.html"></iframe>

<details>
<summary>Table</summary>
    
| name   | config                                                                                   |   time_search |    recall |
|:-------|:-----------------------------------------------------------------------------------------|--------------:|----------:|
| Rii    | `{'subspaces': 96, 'codewords': 128, 'cluster_center': 1000, 'candidates': 10000}`       |        10.266 |     0.324 |
| Rii    | `{'subspaces': 120, 'codewords': 128, 'cluster_center': 1000, 'candidates': 10000}`      |        10.451 |     0.353 |
| Hnsw   | `{'max_connection': 16, 'ef_construction': 400, 'ef_query': 100, 'metric': 'euclidean'}` |        10.454 |     0.726 |
| Rii    | `{'subspaces': 64, 'codewords': 128, 'cluster_center': 1000, 'candidates': 10000}`       |        10.475 |     0.271 |
| Rii    | `{'subspaces': 120, 'codewords': 256, 'cluster_center': 1000, 'candidates': 10000}`      |        10.650 |     0.388 |
| Rii    | `{'subspaces': 64, 'codewords': 256, 'cluster_center': 1000, 'candidates': 10000}`       |        10.681 |     0.303 |
| Hnsw   | `{'max_connection': 16, 'ef_construction': 200, 'ef_query': 100, 'metric': 'euclidean'}` |        10.695 |     0.706 |
| Rii    | `{'subspaces': 96, 'codewords': 128, 'cluster_center': 5000, 'candidates': 10000}`       |        10.870 |     0.375 |
| Rii    | `{'subspaces': 64, 'codewords': 128, 'cluster_center': 5000, 'candidates': 10000}`       |        10.886 |     0.304 |
| Rii    | `{'subspaces': 96, 'codewords': 256, 'cluster_center': 1000, 'candidates': 10000}`       |        10.905 |     0.361 |
| Rii    | `{'subspaces': 96, 'codewords': 256, 'cluster_center': 5000, 'candidates': 10000}`       |        11.049 |     0.415 |
| Hnsw   | `{'max_connection': 48, 'ef_construction': 200, 'ef_query': 100, 'metric': 'euclidean'}` |        11.055 |     0.812 |
| Hnsw   | `{'max_connection': 64, 'ef_construction': 200, 'ef_query': 50, 'metric': 'euclidean'}`  |        11.072 |     0.821 |
| Hnsw   | `{'max_connection': 16, 'ef_construction': 400, 'ef_query': 50, 'metric': 'euclidean'}`  |        11.098 |     0.725 |
| Hnsw   | `{'max_connection': 48, 'ef_construction': 200, 'ef_query': 50, 'metric': 'euclidean'}`  |        11.309 |     0.813 |
| Rii    | `{'subspaces': 64, 'codewords': 256, 'cluster_center': 5000, 'candidates': 10000}`       |        11.314 |     0.344 |
| Hnsw   | `{'max_connection': 16, 'ef_construction': 200, 'ef_query': 50, 'metric': 'euclidean'}`  |        11.323 |     0.707 |
| Rii    | `{'subspaces': 120, 'codewords': 128, 'cluster_center': 5000, 'candidates': 10000}`      |        11.465 |     0.409 |
| Hnsw   | `{'max_connection': 64, 'ef_construction': 400, 'ef_query': 100, 'metric': 'euclidean'}` |        11.468 |     0.864 |
| Hnsw   | `{'max_connection': 48, 'ef_construction': 400, 'ef_query': 100, 'metric': 'euclidean'}` |        11.473 |     0.853 |
| Hnsw   | `{'max_connection': 64, 'ef_construction': 200, 'ef_query': 100, 'metric': 'euclidean'}` |        11.494 |     0.821 |
| Rii    | `{'subspaces': 120, 'codewords': 256, 'cluster_center': 5000, 'candidates': 10000}`      |        11.510 |     0.450 |
| Rii    | `{'subspaces': 192, 'codewords': 128, 'cluster_center': 1000, 'candidates': 10000}`      |        11.643 |     0.424 |
| Hnsw   | `{'max_connection': 48, 'ef_construction': 400, 'ef_query': 50, 'metric': 'euclidean'}`  |        11.933 |     0.853 |
| Hnsw   | `{'max_connection': 64, 'ef_construction': 400, 'ef_query': 50, 'metric': 'euclidean'}`  |        12.096 |     0.864 |
| Rii    | `{'subspaces': 192, 'codewords': 256, 'cluster_center': 1000, 'candidates': 10000}`      |        12.266 |     0.458 |
| Rii    | `{'subspaces': 192, 'codewords': 128, 'cluster_center': 5000, 'candidates': 10000}`      |        13.087 |     0.511 |
| Rii    | `{'subspaces': 192, 'codewords': 256, 'cluster_center': 5000, 'candidates': 10000}`      |        13.294 |     0.545 |
| Rii    | `{'subspaces': 64, 'codewords': 128, 'cluster_center': 5000, 'candidates': 50000}`       |        16.971 |     0.367 |
| Rii    | `{'subspaces': 96, 'codewords': 128, 'cluster_center': 5000, 'candidates': 50000}`       |        20.023 |     0.464 |
| Faiss  | `{'index_key': 'IVF128,PQ32', 'nprobe': 8, 'metric': 'euclidean'}`                       |        20.409 |     0.337 |
| Rii    | `{'subspaces': 96, 'codewords': 128, 'cluster_center': 1000, 'candidates': 50000}`       |        20.663 |     0.464 |
| Rii    | `{'subspaces': 64, 'codewords': 128, 'cluster_center': 1000, 'candidates': 50000}`       |        20.772 |     0.367 |
| Rii    | `{'subspaces': 96, 'codewords': 256, 'cluster_center': 5000, 'candidates': 50000}`       |        20.828 |     0.522 |
| Rii    | `{'subspaces': 64, 'codewords': 256, 'cluster_center': 5000, 'candidates': 50000}`       |        21.248 |     0.417 |
| Rii    | `{'subspaces': 120, 'codewords': 128, 'cluster_center': 1000, 'candidates': 50000}`      |        21.335 |     0.508 |
| Rii    | `{'subspaces': 64, 'codewords': 256, 'cluster_center': 1000, 'candidates': 50000}`       |        21.450 |     0.417 |
| Faiss  | `{'index_key': 'IVF128,PQ64', 'nprobe': 8, 'metric': 'euclidean'}`                       |        22.162 |     0.429 |
| Faiss  | `{'index_key': 'IVF128,PQ32', 'nprobe': 16, 'metric': 'euclidean'}`                      |        22.224 |     0.342 |
| Rii    | `{'subspaces': 120, 'codewords': 256, 'cluster_center': 5000, 'candidates': 50000}`      |        22.509 |     0.572 |
| Rii    | `{'subspaces': 96, 'codewords': 256, 'cluster_center': 1000, 'candidates': 50000}`       |        24.615 |     0.522 |
| Rii    | `{'subspaces': 120, 'codewords': 128, 'cluster_center': 5000, 'candidates': 50000}`      |        25.297 |     0.508 |
| Faiss  | `{'index_key': 'IVF128,PQ64', 'nprobe': 16, 'metric': 'euclidean'}`                      |        26.422 |     0.438 |
| Rii    | `{'subspaces': 120, 'codewords': 256, 'cluster_center': 1000, 'candidates': 50000}`      |        26.527 |     0.572 |
| Rii    | `{'subspaces': 192, 'codewords': 128, 'cluster_center': 1000, 'candidates': 50000}`      |        29.036 |     0.671 |
| Rii    | `{'subspaces': 192, 'codewords': 256, 'cluster_center': 5000, 'candidates': 50000}`      |        31.064 |     0.727 |
| Faiss  | `{'index_key': 'IVF1024,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                      |        32.628 |     0.573 |
| Rii    | `{'subspaces': 192, 'codewords': 128, 'cluster_center': 5000, 'candidates': 50000}`      |        33.497 |     0.671 |
| Rii    | `{'subspaces': 192, 'codewords': 256, 'cluster_center': 1000, 'candidates': 50000}`      |        36.443 |     0.727 |
| Faiss  | `{'index_key': 'IVF512,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                       |        44.005 |     0.675 |
| Faiss  | `{'index_key': 'IVF1024,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                     |        46.694 |     0.730 |
| Faiss  | `{'index_key': 'IVF256,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                       |        68.386 |     0.772 |
| Faiss  | `{'index_key': 'IVF512,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                      |        70.265 |     0.828 |
| Faiss  | `{'index_key': 'IVF128,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                       |       108.011 |     0.847 |
| Faiss  | `{'index_key': 'IVF256,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                      |       123.070 |     0.901 |
| Faiss  | `{'index_key': 'IVF128,SQ8', 'nprobe': 8, 'metric': 'euclidean'}`                        |       156.673 |     0.845 |
| Faiss  | `{'index_key': 'IVF128,SQ4', 'nprobe': 8, 'metric': 'euclidean'}`                        |       201.969 |     0.745 |
| Faiss  | `{'index_key': 'IVF128,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                      |       207.494 |     0.950 |
| Faiss  | `{'index_key': 'IVF64,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                        |       207.639 |     0.927 |
| Faiss  | `{'index_key': 'IVF128,SQ8', 'nprobe': 16, 'metric': 'euclidean'}`                       |       306.423 |     0.945 |
| Faiss  | `{'index_key': 'IVF64,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                       |       366.850 |     0.988 |
| Faiss  | `{'index_key': 'IVF32,Flat', 'nprobe': 8, 'metric': 'euclidean'}`                        |       372.286 |     0.977 |
| Faiss  | `{'index_key': 'IVF128,SQ4', 'nprobe': 16, 'metric': 'euclidean'}`                       |       400.682 |     0.801 |
| Faiss  | `{'index_key': 'IVF32,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                       |       723.329 |     0.999 |
| Faiss  | `{'index_key': 'Flat', 'metric': 'euclidean'}`                                           |      1087.499 |     1.000 |
</details>
