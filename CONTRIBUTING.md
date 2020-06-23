# Contributing to Jina

Thanks for your interest in contributing to Jina. We're grateful for your initiative! ❤️

I'm Alex C-G, Open Source Evangelist for Jina. I'm all about getting our new contributors up-to-speed, and that's what we'll do below. If you have any feedback or questions, ping me on [Twitter](http://www.twitter.com/alexcg) or get in touch on [Slack](https://jina-ai.slack.com/).

In this guide we're going to go through how the steps for each kind of contribution, and good and bad examples of what to do. We look forward to your contributions!

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [Steps to Make Your First Submission](#steps-to-make-your-first-submission)
- [Commit Style](#commit-style)
- [Test Jina Locally and on CI](#test-jina-locally-and-on-ci)
- [Build Documentation Locally](#build-documentation-locally)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Bugs and Issues

### Submitting Issues

We love to get issue reports. But we love it even more if they're in the right format. For any bugs you encounter, we need you to:

* **Describe your problem**: What exactly is the bug. Be as clear and concise as possible
* **Why do you think it's happening?** If you have any insight, here's where to share it

There are also a couple of nice to haves:

* **Environment:** You can find this with `jina --version-full`
* **Screenshots:** If they're relevant

### Fixing and Discussing Issues

Right now we're working on a list of things we want help with and easy-to-fix bugs suitable for first-time contributors. Stay tuned to:

* [Good first issues](https://github.com/jina-ai/jina/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22)
* [Help wanted](https://github.com/jina-ai/jina/issues?q=is%3Aopen+is%3Aissue+label%3A%22help+wanted%22)
* [Discussion required](https://github.com/jina-ai/jina/issues?q=is%3Aopen+is%3Aissue+label%3A%22discussion+required%22)

## Making Your First Submission 

1. Fork the Jina repo and clone onto your computer.
2. Create a [new branch](#naming-your-branch), for example `fix-jina-typo-1`.
3. Work on this branch to do the fix/improvement.
4. Commit the changes with the [correct commit style](#commit-message).
5. Make a pull request. 
6. Submit your pull request and wait for all checks to pass.
7. Request reviews from one of [the code owners](CODEOWNERS).
8. Get a LGTM 👍 and PR gets merged.

**Note:** If you're just fixing a typo or grammatical issue, you can go straight to a pull request.

What happens after the merge? [Understand the developement stage and release cycles here.](RELEASE.md)

## Naming Conventions

For branches, commits, and PRs we follow some basic naming conventions:

* Be descriptive
* Use all lower-case
* Limit punctuation
* Include one of our specified types
* In general, follow the [Conventional Commit](https://www.conventionalcommits.org/en/v1.0.0/#summary) guidelines

### Types

For each branch, commit, or PR, we need you to specify the type to help us keep things organized:
 
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

### Naming your Branch

Your branch name should follow the format `type-scope(-issue_id)`:

* `type` is one of the [types above](#types)
* `scope` is optional, and represents the module your branch is working on.
* `issue_id` is [the GitHub issue](https://github.com/jina-ai/jina/issues) number. Having the correct issue number will automatically link the Pull Request on this branch to that issue. 

> Good examples:
> 
```text
fix-executor-loader-113
chore-update-version
docs-add-cloud-section-33
```

> Bad examples:
>

| Branch name     | Feedback                                              |
| ---             | ---                                                   |
| `FIXAWESOME123` | Not descriptive enough, all caps, doesn't follow spec |
| `NEW-test-1`    | Should be lower case, not descriptive                 |
| `mybranch-1`    | No type, not descriptive                              |

### Writing your Commit Message

A good commit message helps us track Jina's development. A Pull Request with a bad commit message will be *rejected* automatically in the CI pipeline.

A good commit message should:

* Stick to our naming format (outlined below)
* Be short
* Be all lower-case
* Not use too much punctuation

Specifically, your commit message should follow the [Conventional Commits format]: `type(scope?): subject`:

* `type` is one of the [types above](#types).
* `scope` is optional, and represents the module your commit is working on.
* `subject` explains the commit, without an ending period `.`

For example, a commit that fixes a bug in the executor module should be phrased as: `fix(executor): fix the bad naming in init function`

> Good examples:
> 
```text
fix(indexer): fix wrong sharding number in indexer
feat: add remote api
```

> Bad examples:
>

| Commit message                                                                                | Feedback                           |
| ---                                                                                           | ---                                |
| `doc(101): improved 101 document`                                                             | Should be `docs(101)`              |
| `tests(flow): add unit test for flow exception`                                               | Should be `test(flow)`             |
| `DOC(101): Improved 101 Documentation`                                                        | All letters should be in lowercase |
| `fix(pea): i fix this pea and this looks really awesome and everything should be working now` | Too long                           |
| `fix(pea):fix network receive of the pea`                                                     | Missing space after `:`            |
| `hello: add hello-world`                                                                      | Type `hello` is not allowed          |

#### What if I Mess Up?

We all make mistakes. GitHub has a guide on [rewriting commit messages](https://help.github.com/en/github/committing-changes-to-your-project/changing-a-commit-message) to they can adhere to our standards.

You can also install [commitlint](https://commitlint.js.org/#/) onto your own machine and check your commit message by running:

```bash
echo "<commit message>" | commitlint
```

### Naming your Pull Request

We don't enforce naming of PRs and branches, but we recommend you follow the same style. It can simply be one of your commit messages, just copy/paste it, e.g. `fix(readme): improve the readability and move sections`.

## Testing Jina Locally and on CI

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

It prints a list of components the current version of Jina supports, and then exits. Make sure yours are not in red.

Once you submit the PR, your code will be tested in the environment of Python 3.7 and 3.8 with [full exta dependencies](extra-requirements.txt) (`pip install .[all]`) installed.

## Building Documentation Locally

To build documentation locally, you need Docker installed. Clone this repository and run the following command: 

```bash
bash ./make-doc.sh serve 8080
```

The documentation is then available in your browser at [`http://0.0.0.0:8080/`](http://0.0.0.0:8080/).

## Getting Support

We're always happy to lend a hand, answer questions, or listen to feedback. You find us here:

* [Documentation](http://docs.jina.ai)
* [Slack](https://jina-ai.slack.com/)

We're also looking at starting online developer hangouts, so you can catch up with us over chat and video, and get to meet your fellow Jina contributors.

And you can find me, Jina's Open Source Evangelist on [Twitter](http://twitter.com/alexcg). Feel free to @ me if there's anything you want to know!

## Thank You

Once again, thanks so much for your interest in contributing to Jina. We're excited to have you on board!
