import json
import os
import shutil
import sys
import time
import timeit
from pathlib import Path
from typing import Dict

# this line is needed here for measuring import time accurately for 1M imports
import_time = timeit.timeit(stmt='import jina', number=1000000)

from jina import Document, Flow, __version__
from jina.helloworld.fashion.helper import (
    download_data,
    index_generator,
    query_generator,
)
from jina.logging.logger import JinaLogger
from jina.parsers.helloworld import set_hw_parser
from jina import DocumentArrayMemmap
from packaging import version
from pkg_resources import resource_filename

try:
    from jina.helloworld.fashion.executors import MyEncoder, MyIndexer
except:
    from jina.helloworld.fashion.my_executors import MyEncoder, MyIndexer


# declare base logger
log = JinaLogger(__name__, 'custom_logger')


def __doc_generator():
    # Document generator
    for i in range(1000):
        yield Document(
            text=f'This is the document number: {i}',
        )


def _benchmark_import_time() -> Dict[str, float]:
    """Benchmark Jina Core import time for 1M imports.

    Returns:
        A dict mapping of import time in seconds as float number.

    TODO: Figure out How we can measure the import time within a function.
    """
    return {'import_time': float(import_time)}


def _benchmark_avg_flow_time() -> Dict[str, float]:
    """Benchmark on a simple flow operation.

    Reurns:
        A dict mapping of import time in seconds as float number.
    """
    fs = [
        Flow().add(),
        Flow().add().add(),
        Flow().add().add().add(),
        Flow().add().add().add(needs='gateway'),
    ]
    log.info('Benchmarking average flow time')
    st = time.perf_counter()
    for f in fs:
        with f:
            f.post(on='/', inputs=__doc_generator, request_size=10)
    flow_time = time.perf_counter() - st
    avg_flow_time = flow_time / len(fs)
    log.info('Average flow time: %f seconds', avg_flow_time)

    return {'avg_flow_time': avg_flow_time}


def _benchmark_dam_extend_qps() -> Dict[str, float]:
    """Benchmark on adding 1M documents to DocumentArrayMemmap.

    Returns:
        A dict mapping of dam extend time in seconds as float number.
    """
    dlist = []
    dam_size = 1000000
    dam = DocumentArrayMemmap(os.path.join(os.getcwd(), 'MyMemMap'))

    for i in range(dam_size):
        dlist.append(
            Document(
                text=f'This is the document number: {i}',
            )
        )

    log.info('Benchmarking DAM extend')
    st = time.perf_counter()
    dam.extend(dlist)
    dam_extend_time = time.perf_counter() - st
    log.info('%d qps within %d seconds', dam_size / dam_extend_time, dam_extend_time)

    return {
        'dam_extend_time': dam_extend_time,
        'dam_extend_qps': dam_size / dam_extend_time,
    }


def _benchmark_qps() -> Dict[str, float]:
    """Benchmark Jina Core Indexing and Query.

    Returns:
        A dict mapping keys
    """
    args = set_hw_parser().parse_args()
    args.workdir = os.path.join(os.getcwd(), 'original')
    args.num_query = 4096

    targets = {
        'index-labels': {
            'url': args.index_labels_url,
            'filename': os.path.join(args.workdir, 'index-labels'),
        },
        'query-labels': {
            'url': args.query_labels_url,
            'filename': os.path.join(args.workdir, 'query-labels'),
        },
        'index': {
            'url': args.index_data_url,
            'filename': os.path.join(args.workdir, 'index-original'),
        },
        'query': {
            'url': args.query_data_url,
            'filename': os.path.join(args.workdir, 'query-original'),
        },
    }

    # download the data
    Path(args.workdir).mkdir(parents=True, exist_ok=True)
    download_data(targets, args.download_proxy)

    try:
        f = Flow().add(uses=MyEncoder).add(uses=MyIndexer)

        with f:
            # do index
            log.info('Benchmarking index')
            st = time.perf_counter()
            f.index(
                index_generator(
                    num_docs=targets['index']['data'].shape[0], target=targets
                ),
                show_progress=True,
            )
            index_time = time.perf_counter() - st
            log.info(
                'Indexed %d docs within %d seconds',
                targets['index']['data'].shape[0],
                index_time,
            )

            # do query
            log.info('Benchmarking query')
            st = time.perf_counter()
            f.search(
                query_generator(num_docs=args.num_query, target=targets),
                shuffle=True,
                parameters={'top_k': args.top_k},
                show_progress=True,
            )
            query_time = time.perf_counter() - st
            log.info('%d query within %d seconds', args.num_query, query_time)

    except Exception as e:
        log.error(e)
        sys.exit(1)

    return {
        'index_time': index_time,
        'query_time': query_time,
        'index_qps': targets['index']['data'].shape[0] / index_time,
        'query_qps': args.num_query / query_time,
    }


def benchmark() -> Dict[str, str]:
    """Merge all benchmark results and return final stats.

    Returns:
        A dict mapping keys.
    """
    stats = {'version': __version__}
    stats.update(_benchmark_import_time())
    stats.update(_benchmark_dam_extend_qps())
    stats.update(_benchmark_qps())
    stats.update(_benchmark_avg_flow_time())

    return stats


def write_stats(stats: Dict[str, str], path: str = 'output/stats.json') -> None:
    """Write stats to a JSON file.

    Args:
        stats: This is the summary result of all benchmarks.
    """
    his = []
    path_dir = os.path.join(os.getcwd(), os.path.split(path)[0])
    path = os.path.join(os.getcwd(), path)
    Path(path_dir).mkdir(parents=True, exist_ok=True)

    try:
        with open(path) as fp:
            his = json.load(fp)
    except Exception as e:
        log.warning('Existing file not found at: %s', path)

    try:
        with open(path, 'w+') as fp:
            his.append(stats)
            cleaned = {}

            for dd in his:
                # some versions may completely broken therefore they give unreasonably speed
                # but the truth is they are not indexing/querying accurately
                if 5000 > dd['index_qps'] > 0 and 1000 > dd['query_qps'] > 0:
                    cleaned[dd['version']] = dd
                else:
                    log.warning(f'{dd} is broken')
            result = list(cleaned.values())
            result.sort(key=lambda x: version.Version(x['version']))
            json.dump(result, fp, indent=2)
            log.info('Stats: %s', result)

        if os.path.exists(path):
            log.info('Stats written successful at: %s', path)

    except Exception as e:
        log.error(e)
        sys.exit(1)


def cleanup() -> None:
    # Do the cleanup at the end of this script.
    cwd = os.getcwd()
    my_indexer_dir = os.path.join(cwd, 'MyIndexer')
    my_mem_map = os.path.join(cwd, 'MyMemMap')

    if os.path.exists(my_indexer_dir):
        shutil.rmtree(my_indexer_dir)

    if os.path.exists(my_mem_map):
        shutil.rmtree(my_mem_map)


def main() -> None:
    os.environ['PATH'] += os.pathsep + resource_filename('jina', 'resources')
    os.environ['PATH'] += (
        os.pathsep + resource_filename('jina', 'resources') + '/fashion/'
    )

    for k, v in {
        'RESOURCE_DIR': resource_filename('jina', 'resources'),
        'SHARDS': 4,
        'PARALLEL': 4,
        'REPLICAS': 4,
        'HW_WORKDIR': 'workdir',
        'WITH_LOGSERVER': False,
    }.items():
        os.environ[k] = str(v)

    output_path = 'output/{}.json'.format(__version__)
    write_stats(benchmark(), output_path)
    cleanup()


if __name__ == '__main__':
    main()
