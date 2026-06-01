# WoeUSB-ng AppImage Packaging

This directory contains the tooling used to build a portable x86_64 AppImage
from the current WoeUSB-ng source checkout.

The AppImage bundles:

- WoeUSB-ng
- Python 3 and the Python standard library
- wxPython and the GTK3 runtime needed by the GUI
- Runtime tools used by WoeUSB-ng: parted, GRUB tools, ntfs-3g, dosfstools,
  and p7zip

Host utilities such as `mount`, `umount`, `lsblk`, `wipefs`, `blockdev`, and
`df` are still expected from the host system because they operate on live block
devices.

## Build Requirements

The build script is intended to run on Fedora or in a Fedora container. It uses
`dnf download` to collect runtime RPMs before assembling the AppDir.

Install the build dependencies on Fedora:

```shell
sudo dnf install -y --setopt=install_weak_deps=False --disablerepo=fedora-cisco-openh264 \
    git wget python3 python3-pip python3-wxpython4 \
    patchelf rpm-build cpio file findutils binutils dnf-plugins-core
```

Then build from the repository root:

```shell
packaging/appimage/build-appimage.sh
```

The AppImage will be written to:

```text
build/appimage/WoeUSB-ng-<version>-x86_64.AppImage
```

## Container Build

From any Linux distribution with Docker:

```shell
docker run --rm -v "$PWD":/work -w /work fedora:latest bash -lc \
  'dnf install -y --setopt=install_weak_deps=False --disablerepo=fedora-cisco-openh264 git wget python3 python3-pip python3-wxpython4 patchelf rpm-build cpio file findutils binutils dnf-plugins-core && packaging/appimage/build-appimage.sh'
```

With Podman:

```shell
podman run --rm -v "$PWD":/work:Z -w /work fedora:latest bash -lc \
  'dnf install -y --setopt=install_weak_deps=False --disablerepo=fedora-cisco-openh264 git wget python3 python3-pip python3-wxpython4 patchelf rpm-build cpio file findutils binutils dnf-plugins-core && packaging/appimage/build-appimage.sh'
```

## Smoke Test

After building:

```shell
APPIMAGE_EXTRACT_AND_RUN=1 build/appimage/WoeUSB-ng-*-x86_64.AppImage --version
APPIMAGE_EXTRACT_AND_RUN=1 build/appimage/WoeUSB-ng-*-x86_64.AppImage --help
```
