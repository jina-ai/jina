# Autocomplete commands on Bash, Zsh and Fish

After installing Jina via `pip`, you should be able to use your shell's autocomplete feature while using Jina's CLI. For example, typing `jina` then hitting your Tab key will provide the following suggestions:

```bash

➜  _jina git:(master) ✗ jina 

--help          --version       --version-full  check           client          flow            gateway         hello-world     log             pea             ping            pod
```

The autocomplete is context-aware. It also works when you type a second-level argument:

```bash

➜  _jina git:(master) ✗ jina pod --name --lo

--log-profile  --log-remote   --log-sse
```


Currently, the feature is enabled automatically on Bash, Zsh and Fish. It requires you to have a standard shell path as follows:

| Shell | Configuration file path      |
| ---   | ---                          |
| Bash  | `~/.bashrc`                  |
| Zsh   | `~/.zshrc`                   |
| Fish  | `~/.config/fish/config.fish` |

