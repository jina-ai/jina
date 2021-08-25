# Latency Tracking

Latency Tracking repository works in accordance with [scripts/latency-tracking](https://github.com/jina-ai/jina/blob/master/scripts/latency-tracking) from [Jina Core](https://github.com/jina-ai/jina). It benchmarks the following items over the history of releases:

- `import jina` time
- Index Speed
- Query Speed
- Average Flow Time
- `DocumentArrayMemmap` Extend Time

<img src=".github/container-env.png?raw=true" alt="Jina banner" width="50%">

Blog post: [Benchmark a Decentralized Search System on 79 Past Releases](https://hanxiao.io/2020/11/10/Optimizing-the-Overhead-of-a-Decentralized-Search-System/)

## Track Latency

### Prepare Environment

This repo can't produce benchmark results independently as it works in accordance with [scripts/latency-tracking](https://github.com/jina-ai/jina/blob/master/scripts/latency-tracking) from [Jina Core](https://github.com/jina-ai/jina). So, let's prepare the envrionment at first.

```bash
git clone git@github.com:jina-ai/jina.git
cd jina
git clone https://github.com/jina-ai/latency-tracking latency
```

### Run single version

```bash
# give the version to benchmark
JINA_VER=master

# benchmark it!
rm -f .dockerignore
docker build --build-arg JINA_VER=$JINA_VER -f latency/Dockerfile -t latency-tracking .
docker run -v $(pwd)/output:/app/output -v $(pwd)/latency/original:/app/original latency-tracking
```

### Run last `n` versions

Require `jq` to be installed.

```bash
bash latency/batch.sh 5
```

This will run the last 5 versions in reverse order, i.e. last release first.