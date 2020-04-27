# Autocomplete commands on Bash, Zsh and Fish

After installing Jina via `pip`, you should be able to use autocomplete feature while using Jina CLI. For example,

```bash

➜  _jina git:(master) ✗ jina 

--help          --version       --version-full  check           client          flow            gateway         hello-world     log             pea             ping            pod
```

The autocomplete is context-aware. It also works when you type a second-level argument:

```bash

➜  _jina git:(master) ✗ jina pod --name --lo

--log-profile  --log-remote   --log-sse
```


Currently, the feature is enabled automatically on Bash, Zsh and Fish. It requires your ".bashrc" path to be standard.

| Shell | ".bashrc" Path |
| --- | --- |
| Bash | `~/.bashrc` |
| Zsh | `~/.zshrc` |
| Fish | `~/.config/fish/config.fish` |

