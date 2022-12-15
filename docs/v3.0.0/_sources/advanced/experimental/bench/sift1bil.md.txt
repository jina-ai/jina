#### sift 1 billion

This has only been run with sub-samples, not with the full dataset.

<iframe width="600" height="400" style="border: 0" src="..\..\..\_static\indexers_benchmark_plots\sift50m-10.html"></iframe>

<details>
<summary>Table</summary>
    
| name   | config                                                                                   |   time_search |   recall |
|:-------|:-----------------------------------------------------------------------------------------|--------------:|---------:|
| Hnsw   | `{'max_connection': 16, 'ef_construction': 200, 'ef_query': 50, 'metric': 'euclidean'}`  |        95.291 |    0.971 |
| Hnsw   | `{'max_connection': 16, 'ef_construction': 400, 'ef_query': 50, 'metric': 'euclidean'}`  |        97.240 |    0.972 |
| Hnsw   | `{'max_connection': 16, 'ef_construction': 400, 'ef_query': 100, 'metric': 'euclidean'}` |        97.672 |    0.972 |
| Hnsw   | `{'max_connection': 48, 'ef_construction': 200, 'ef_query': 50, 'metric': 'euclidean'}`  |       100.603 |    0.992 |
| Hnsw   | `{'max_connection': 64, 'ef_construction': 400, 'ef_query': 100, 'metric': 'euclidean'}` |       105.235 |    0.995 |
| Faiss  | `{'index_key': 'IVF512,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                      |      1156.892 |    0.966 |
| Faiss  | `{'index_key': 'IVF128,PQ64', 'nprobe': 16, 'metric': 'euclidean'}`                      |      1359.404 |    0.936 |
| Faiss  | `{'index_key': 'IVF256,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                      |      1638.537 |    0.983 |
| Faiss  | `{'index_key': 'IVF128,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                      |      2323.912 |    0.994 |
| Faiss  | `{'index_key': 'IVF128,SQ8', 'nprobe': 16, 'metric': 'euclidean'}`                       |      3543.806 |    0.990 |
| Faiss  | `{'index_key': 'IVF64,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                       |      3866.858 |    0.998 |
| Faiss  | `{'index_key': 'IVF32,Flat', 'nprobe': 16, 'metric': 'euclidean'}`                       |      6918.610 |    1.000 |
</details>

<iframe width="600" height="400" style="border: 0" src="..\..\..\_static\indexers_benchmark_plots\sift50m-20.html"></iframe>

<details>
<summary>Table</summary>
    
| name   | config                                                                                  |   time_search |   recall |
|:-------|:----------------------------------------------------------------------------------------|--------------:|---------:|
| Hnsw   | `{'max_connection': 16, 'ef_construction': 200, 'ef_query': 50, 'metric': 'euclidean'}` |        95.436 |    0.927 |
| Hnsw   | `{'max_connection': 48, 'ef_construction': 200, 'ef_query': 50, 'metric': 'euclidean'}` |        99.769 |    0.976 |
| Faiss  | `{'index_key': 'IVF128,PQ64', 'nprobe': 16, 'metric': 'euclidean'}`                     |      2745.310 |    0.908 |
| Faiss  | `{'index_key': 'IVF128,SQ8', 'nprobe': 16, 'metric': 'euclidean'}`                      |      6902.018 |    0.988 |
</details>
