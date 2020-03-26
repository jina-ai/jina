# Contributing Guideline

❤️ First, thank you for your great initiative! 

We welcome all kinds of contributions from the open-source community, individuals and  partners. Without your active involvement, Jina can't be successful.  

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [Commit Style](#commit-style)
  - [Branch Name](#branch-name)
  - [Commit Message](#commit-message)
  - [Pull Request Name](#pull-request-name)
- [Make Your First Submission](#make-your-first-submission)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

Typos and grammatical errors can go straight to a pull-request.

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
fix-exectutor-loader-113
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


## Make Your First Submission 

As a summary, here are the steps for contributing Jina.

1. Create a new branch, say `fix-jina-typo-1`.
2. Fix/improve the codebase.
3. Commit the changes with the correct commit style.
4. Make a pull request. 
5. Submit your pull request and wait for all checks passed.
6. Request reviews from one of [the code owners](CODEOWNERS).
7. Get a LGTM 👍 and PR gets merged.

Well done! Once a PR gets merged, here are the things happened next:

- Jina Docker images tagged with `master-debian` and `dev-debian` will be automatically updated in an hour.
- On every Friday when a new release is published, PyPi packages and all Docker images tagged with `-latest` will be updated accordindly. 
- Your contribution and commits will be included in [our weekly release note](CHANGELOG.md). 🍻

