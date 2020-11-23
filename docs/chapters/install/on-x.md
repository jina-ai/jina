# Can I Run Jina On ....?

Linux distributions (not to mention notebooks and other Python environments) are like a box of chocolates. They're all different, and you never know what you're going to get.

While installing Jina on Ubuntu is pretty straightforward, other distributions may have their quirks, either with Jina directly or with some of the tools around Jina (like Docker for example). This document aims to be a one-stop resource for any issues you may encounter on different distros, operating systems, or running in notebooks.

## Fedora

While Jina hasn't shown any quirks on Fedora, getting Docker up and running to test Jina examples can be troublesome. Two main errors commonly pop up on a fresh install:

### Error: OCI runtime create failed: this version of runc doesn't work on cgroups v2

To fix this:

Switch to root user and enter `/etc/grub.d`:

```
sudo su
cd /boot
```

Open `grubenv` in your text editor

Find the line starting with `kernelopts`, and add `systemd.unified_cgroup_hierarchy=0` to the end of the line, ensuring there is a space before it. After that, reboot.

[Source](https://github.com/jitsi/docker-jitsi-meet/issues/618)

### PermissionError: [Errno 13] Permission denied

You'll need to temporarily disable SELinux:

```
sudo setenforce 0
```

[Source](https://stackoverflow.com/questions/61527193/docker-and-permissionerror-errno-13-permission-denied-output-svg)

## Other

If you've got Jina running on other systems, we'd love to hear from you, and especially the steps you had to go through to make it work properly!

## Google Colab

Jina requires Python 3.7 or 3.8. At the time of writing Google Colab runs Python 3.6.7 so Jina can't be installed via `pip`
