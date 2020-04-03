# Contributing Guideline

❤️ First, thank you for your great initiative! 

We welcome all kinds of contributions from the open-source community, individuals and  partners. Without your active involvement, Jina can't be successful.  

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [Make Your First Submission](#make-your-first-submission)
- [Commit Style](#commit-style)
- [Test Jina Locally and on CI](#test-jina-locally-and-on-ci)
- [Sign Your Contribution](#sign-your-contribution)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

Typos and grammatical errors can go straight to a pull-request.


## Make Your First Submission 

Here are the steps for contributing Jina.

1. Create a [new branch](#branch-name), say `fix-jina-typo-1`.
2. Fix/improve the codebase.
3. Commit the changes with the [correct commit style](#commit-message). Remember to [sign-off your work](#sign-your-contribution).
4. Make a pull request. 
5. Submit your pull request and wait for all checks passed.
6. Request reviews from one of [the code owners](CODEOWNERS).
7. Get a LGTM 👍 and PR gets merged.

Well done! Once a PR gets merged, here are the things happened next:

- Jina Docker images tagged with `master-debian` and `dev-debian` will be automatically updated in an hour.
- On every Friday when a new release is published, PyPi packages and all Docker images tagged with `-latest` will be updated accordindly. 
- Your contribution and commits will be included in [our weekly release note](CHANGELOG.md). 🍻


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

## Sign Your Contribution

The sign-off is a simple line at the end of the explanation for the patch, which certifies that you wrote it or otherwise have the right to pass it on as an open-source patch. The rules are pretty simple: if you can certify the below (from developercertificate.org):

```text
Developer Certificate of Origin
Version 1.1

Copyright (C) 2004, 2006 The Linux Foundation and its contributors.
660 York Street, Suite 102,
San Francisco, CA 94110 USA

Everyone is permitted to copy and distribute verbatim copies of this
license document, but changing it is not allowed.


Developer's Certificate of Origin 1.1

By making a contribution to this project, I certify that:

(a) The contribution was created in whole or in part by me and I
    have the right to submit it under the open source license
    indicated in the file; or

(b) The contribution is based upon previous work that, to the best
    of my knowledge, is covered under an appropriate open source
    license and I have the right under that license to submit that
    work with modifications, whether created in whole or in part
    by me, under the same open source license (unless I am
    permitted to submit under a different license), as indicated
    in the file; or

(c) The contribution was provided directly to me by some other
    person who certified (a), (b) or (c) and I have not modified
    it.

(d) I understand and agree that this project and the contribution
    are public and that a record of the contribution (including all
    personal information I submit with it, including my sign-off) is
    maintained indefinitely and may be redistributed consistent with
    this project or the open source license(s) involved.
```

then you just add a line to every git commit message:

```text
Signed-off-by: Joe Smith <joe@gmail.com>
```

using your real name (sorry, no pseudonyms or anonymous contributions.)

You can add the sign off when creating the git commit via `git commit -s`.

Most of the IDE support sign-off with one checkbox, e.g. PyCharm 

![](.github/.CONTRIBUTING_images/82e3f6e1.png)


