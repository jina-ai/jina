<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [Release Cycle](#release-cycle)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Release Cycle

We follow the [semantic versioning](https://semver.org/).

Say current master version is at `x.y.z`,

Every successful merge into the master triggers a development release. It will: 

- update the Docker image with tag `devel`;
- update [jina-ai/docs](https://github.com/jina-ai/docs) tag `devel`

On release, it will:

- tag the master as `vx.y.z` and push to the repo;
- create a new tag `vx.y.z` in [jina-ai/docs](https://github.com/jina-ai/docs);
- publish `x.y.z` docker image, with tag `latest`, `x.y.z`;
- upload `x.y.z` package on PyPI;
- bump the master to `x.y.(z+1)` and commit a `chore(version)` push.