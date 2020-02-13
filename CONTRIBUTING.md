# Contributing Guidelines


❤️ First, thank you for your great initiative! 


We welcome all kinds of contributions from the open-source community, individual committers and institutional partners. Without your active involvement, Jina can't be successful.  

## Making Your First Commit 

The beginning is always the hardest part. But fear not, if you find any typo, missing docstring or incomplete unit test, simply correct them by making a commit to jina. Here are the steps:

1. Create a new branch, say `fix-jina-typo-1`
2. Fix/improve the codebase
3. Commit the changes. Note the **commit message must follow [the naming style](#commit-message-naming)**, say `fix(readme): improve the readability and move sections`
4. Make a pull request. It can simply be one of your commit messages, just copy paste it, e.g. `fix(readme): improve the readability and move sections`
5. Submit your pull request and wait for all checks passed:
    - Coding style
    - Commit and PR styles check
    - All unit tests
6. Request reviews from one of [the code owners](./CODEOWNERS)
7. Get a LGTM 👍 and PR gets merged.

Well done! Once a PR gets merged, here are the things happened next:
- all Docker images tagged with `-latest` will be automatically updated in an hour. You may check the [its building status at here](#install-jina-via-pip)
- on every Friday when a new release is published, PyPi packages and all Docker images tagged with `-stable` will be updated accordindly. 
- your contribution and commits will be included in [our weekly release note](./CHANGELOG.md). 🍻


## Naming Your Commit

To help everyone with understanding the commit history of jina, we employ [`commitlint`](https://commitlint.js.org/#/) in the CI pipeline to enforce the commit styles. Specifically, our convention is:

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

`subject` explains the commit.

As an example, a commit that fix a bug in the executor module should be phrased as:
```text
fix(executor): fix the bad naming in init function
``` 

We do not enforce the naming of PR and branch, but we highly recommend you to follow the same style. For example, if your commit message is the above, then a good branch name could be `fix-executor-1`

