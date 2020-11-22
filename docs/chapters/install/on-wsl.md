# Install Jina on Windows Subsystem for Linux (WSL)

On WSL 2 with Python >= 3.7 installed, you can install Jina via:

```bash
pip install jina
```

You can run the hello-world demo for verify the installation

```bash
jina hello-world
```

Due to the lack of GUI in WSL, you might not be able to see the results. 
Run the following lines at `/where/your/run/jina-helloworld` and check the results in your browser at `localhost:8000`.

```bash
cd /where/your/run/jina-helloworld/
python -m http.server
```

## Reference

The WSL allows you to run a Linux system directly in Windows. You can find the official installation Guide at [here](https://docs.microsoft.com/en-us/windows/wsl/install-win10)