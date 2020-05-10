# Contributing Guideline

❤️ First, thank you for your great initiative! 

We welcome all kinds of contributions from the open-source community, individuals and  partners. Without your active involvement, Jina can't be successful.  

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [Steps to Make Your First Submission](#steps-to-make-your-first-submission)
- [Commit Style](#commit-style)
- [Test Jina Locally and on CI](#test-jina-locally-and-on-ci)
- [Build Documentation Locally](#build-documentation-locally)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

**Typos and grammatical errors can go straight to a pull-request.**


## Steps to Make Your First Submission 

Here are the steps for contributing Jina.

1. Create a [new branch](#branch-name), say `fix-jina-typo-1`.
2. Work on this branch and do the fix/improve.
3. Commit the changes with the [correct commit style](#commit-message).
4. Make a pull request. 
5. Submit your pull request and wait for all checks passed.
6. Request reviews from one of [the code owners](CODEOWNERS).
7. Get a LGTM 👍 and PR gets merged.

What happens after the merge? [Understand the developement stage and release cylces here.](RELEASE.md)

## Commit Style

### Branch Name

The branch name should follow the style described below:

```text
type-scope(-issue_id)
```

where `type` is one of the following:

- build
- ci
- chore
- docs
- feat
- fix
- perf
- refactor
- revert
- style
- test

`scope` is optional, represents the module your commit working on.

`issue_id` is [the Github issues](https://github.com/jina-ai/jina/issues) number. Having the correct issue number will automatically link the Pull Request on this branch to that issue. 

> Good examples:
> 
```text
fix-executor-loader-113
chore-update-version
docs-add-cloud-section-33
```

> Bad examples:
>
```text
FIXAWESOME123
NEW-test-1
mybranch-1
``` 


### Commit Message

Good commit message helps us to track the development of Jina. A Pull Request with bad commit message will be *rejected* automatically in the CI pipeline.

Specifically, the commit message should follow the style ([`commitlint`](https://commitlint.js.org/#/)) described below:

```text
type(scope?): subject
```

where `type` is one of the following:

- build
- ci
- chore
- docs
- feat
- fix
- perf
- refactor
- revert
- style
- test

`scope` is optional, represents the module your commit working on.

`subject` explains the commit, without an ending period `.`

As an example, a commit that fix a bug in the executor module should be phrased as:
```text
fix(executor): fix the bad naming in init function
``` 

> Good examples:
> 
```text
fix(indexer): fix wrong sharding number in indexer
feat: add remote api
```

> Bad examples:
>
```text
fix indexer: something wrong and i fix it
test-123 is broken and i fix it
doc: it should be plural `docs`
```

### Pull Request Name

We do not enforce the naming of PR and branch, but we highly recommend you to follow the same style. It can simply be one of your commit messages, just copy paste it, e.g. `fix(readme): improve the readability and move sections`.

## Test Jina Locally and on CI

Locally you can do unittest via:

```bash
pip install ".[match-py-ver]"
cd tests && python -m unittest *.py -v
```

When you add an executor or a driver, you may introduce new dependencies to Jina. You can verify the dependencies via:

```bash
jina check
```
, and via Docker container:
```bash
docker run jinaai/jina:my-local-version check
```

It prints a list of components the current Jina supported and exits. Make sure yours is not in red.

Once you submit the PR, your code will be tested in the environment of Python 3.7 and 3.8 with [full exta dependencies](extra-requirements.txt) (`pip install .[all]`) installed.

## Build Documentation Locally

To build the documentation locally, you need to have Docker installed. Clone this repository and run the following command: 

```bash
bash ./make-doc.sh serve 8080
```

The documentation is then available via browser at `http://0.0.0.0:8080/`.

