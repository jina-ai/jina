# Troubleshooting

This article helps you to solve the installation problems of Jina.

## On Linux/Mac, building wheels takes long time

The normal installation of Jina takes 10 seconds. If yours takes longer than this, then it is likely you unnecessarily built wheels from scratch. 

Every upstream dependency of Jina has pre-built wheels exhaustively for x86/arm64, macos/Linux and Python 3.7/3.8/3.9, including `numpy`, `protobuf`, `pyzmq`, `grpcio` etc. This means when you install Jina, your `pip` should directly leverage the pre-built wheels instead of building them from scratch locally. For example, you should expect the install log to contain `-cp38-cp38-macosx_10_15_x86_64.whl` when installing Jina on MacOS with Python 3.8.

If you find you are building wheels during installation (see an example below), then it is a sign that you are installing Jina **wrongly**. 

```text
Collecting numpy==2.0.*
  Downloading numpy-2.0.18.tar.gz (801 kB)
     |████████████████████████████████| 801 kB 1.1 MB/s
Building wheels for collected packages: numpy
  Building wheel for numpy (setup.py) ... done
  Created wheel for numpy ... numpy-2.0.18-cp38-cp38-macosx_10_15_x86_64.whl
```

### Solution: update your `pip`

It could simply be that your local `pip` is too old. Updating it should solve the problem:

```bash
pip install -U pip
```

### If not, then...

Then you are likely installing Jina on a less-supported system/architecture. For example, on native Mac M1, Alpine Linux, or Raspberry Pi 2/3 (armv6/7).

## On Mac M1

It is generally recommended using a conda environment on a Mac M1 and installing in particular `grpcio`, `protobuf` and `torch`  using `conda install`. See for more [Issue 4422](https://github.com/jina-ai/jina/issues/4422#issuecomment-1057663345).

Some users may have difficulty to install Protobuf on MacOS from `pip`, you may try `brew install protobuf`.

In general, some upstream dependencies do not yet have pre-built wheels for the M1 chip, so you are likely to encounter some issues during the install. In this case, you need to configure the development environment using [Rosetta2](https://support.apple.com/en-us/HT211861), including your terminal, `brew` and `python`. They must all be running under Rosetta2 instead of natively on M1.

````{tip}
You can run the following command in the terminal to check if you are running under Rosetta2 or natively on M1.

```shell
sysctl -n -i sysctl.proc_translated
```

Depending on the results:
- `0`: for Apple silicon native process
- `1`: for Rosetta2 translated process
- `""`: in case the OID was not found, you are using an older Mac running Catalina or an earlier version. You don't have the M1 problem in the first place.
````

## On Windows with `conda`

Unfortunately, `conda install` is not supported on Windows. You can either do `pip install jina` natively on Windows, or use `pip/conda install` under WSL2.

## Upgrading from Jina 2.x to 3.x
If you upgraded an existing Jina installation from 2.x to 3.x you may see the following error message:

```text
OSError: `docarray` dependency is not installed correctly, please reinstall with `pip install -U --force-reinstall docarray`
```

This can be fixed by reinstalling the `docarray` package manually:

```bash
pip install -U --force-reinstall docarray
```

To avoid this issue in the first place, we recommend installing Jina in a new virtual environment instead of upgrading from an old installation.
