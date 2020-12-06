# Code Review Guidelines  

## PyGuide  

- [Google guide](https://google.github.io/styleguide/pyguide.html)
- [Antipatterns](https://docs.quantifiedcode.com/python-anti-patterns/index.html)
- [Zen of python](https://zen-of-python.info/)
- [Code review for humans](https://phauer.com/2018/code-review-guidelines/)
- [Code review culture](https://www.giladpeleg.com/blog/better-code-review/)

## General PR process  

- The scope of PR should be simple, unique and well-defined. PR should not contain unrelated changes
- Approve PR only if you are sure about the scope
- Be respectful and reply asap
- Avoid spending too much time on trivial changes
- Avoid premature optimisation
- For community PR, check CLA by typing `recheckcla`
- Ask for jina env if needed by `jina -vf`
- Suggest changes and check back ASAP. Get PR merged soon
- Suggest adding appropriate documentation for new features
- Don't forget to praise when PR is ready with something like LGTM

## TLDR for pyguide  

- Variables names need to be informative. No k, v or x.
- Use standard import [order](https://stackoverflow.com/questions/20762662/whats-the-correct-way-to-sort-python-import-x-and-from-x-import-y-statement)
- Define global variables in CAPS
- Use appropriate underscore for variable naming (leading, lagging, single, double)
- Add docstrings
- Add type hints
- Use codetags like [#TODO](https://www.python.org/dev/peps/pep-0350/#mnemonics) in code wherever needed
- Raise appropriate exceptions
- Don't rename functions & arguments exposed to the user unless necessary. Have appropriate depreciation strategy

## Jina specific  

- Use this to create random ports for servers

    `from jina.helper import random_port`

- You can keep function specific imports inside functions
- Jina ENV variables should start with **JINA_**
- For type hints which require import, you can do it like this

```python
if False:
    from PIL import Image

def func(arr: 'Image'):
    from PIL import Image
    ...
```

## Adding tests  

- Add new unit & integration test if you add a new feature
- Use pytest tmpdir fixture for temporary directories
- Check test locally before pushing
- If a `Flow()` needs to be built in the test and is not a test of the Flow module, the test should go under `/tests/integration`

## Core  

**Single Responsibility Principle**  

Do not place more than one responsibility into a single class or function. Instead, refactor into separate classes and functions.

**Open Closed Principle**  

While adding new functionality, existing code should not be modified. New functionality should be written in new classes and functions.

**Liskov substitutability principle**  

The child class should not change the behavior (meaning) of the parent class. The child class can be used as a substitute for a base class.

**Interface segregation**  

Do not create lengthy interfaces. Instead, split them into smaller interfaces based on the functionality. The interface should not contain any dependencies (parameters) which are not required for the expected functionality.

**Dependency Injection**  

Inject dependencies instead of hard-coding them.