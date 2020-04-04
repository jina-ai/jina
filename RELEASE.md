# Release Cycle

We follow the [semantic versioning](https://semver.org/). Say current master version is at `x.y.z`,

## Version Explained

- `devel`: the development version corresponds to the latest master.
- `devel-x.y.z`: alias of `devel`, often `x.y.z` is one minor version forward comparing to the last Friday release.
- `x.y.z`: Friday release.
- `latest`: the last Friday release. 

## Release Triggered Events 

Every successful merge into the master triggers a development release. It will: 

- update the Docker image with tag `devel`;
- update [jina-ai/docs](https://github.com/jina-ai/docs) tag `devel`

On Friday release, it will:

- tag the master as `vx.y.z` and push to the repo;
- create a new tag `vx.y.z` in [jina-ai/docs](https://github.com/jina-ai/docs);
- publish `x.y.z` docker image, with tag `latest`, `x.y.z`;
- upload `x.y.z` package on PyPI;
- bump the master to `x.y.(z+1)` and commit a `chore(version)` push.

