# WoeUSB-ng
![brand](.github/woeusb-logo.png)

_A Linux program to create a Windows USB stick installer from a real Windows DVD or image._

This package contains two programs:

* woeusb: A command-line utility that enables you to create your own bootable Windows installation USB storage device from an existing Windows Installation disc or disk image
* woeusbgui: Graphic version of woeusb

Supported images:

Windows Vista, Windows 7, Window 8.x, Windows 10. All languages and any version (home, pro...) and Windows PE are supported.

Supported bootmodes:

* Legacy/MBR-style/IBM PC compatible bootmode
* Native UEFI booting is supported for Windows 7 and later images (limited to the FAT filesystem as the target)

This project rewrite of original [WoeUSB](https://github.com/slacka/WoeUSB) 

## Installation

### Arch
```shell
yay woeusb-ng
```

### For other distributions
### Install WoeUSB-ng's Dependencies
#### Ubuntu

```shell
sudo apt install git p7zip-full python3-pip python3-wxgtk4.0 grub2-common grub-pc-bin
```

#### Fedora (tested on: Fedora Workstation 33)
```shell
sudo dnf install git p7zip p7zip-plugins python3-pip python3-wxpython4
```

#### Install WoeUSB-ng
```shell
sudo pip3 install WoeUSB-ng
```

## Installation from source code

### Install WoeUSB-ng's Build Dependencies
#### Ubuntu
```shell
sudo apt install git p7zip-full python3-pip python3-wxgtk4.0 grub2-common grub-pc-bin
```
#### Arch
```shell
sudo pacman -Suy p7zip python-pip python-wxpython
```
#### Fedora (tested on: Fedora Workstation 33) 
```shell
sudo dnf install git p7zip p7zip-plugins python3-pip python3-wxpython4
```
### Install WoeUSB-ng
```shell
git clone https://github.com/WoeUSB/WoeUSB-ng.git
cd WoeUSB-ng
sudo pip3 install .
```

### Installation from source code locally or in virtual environment 
```shell
git clone https://github.com/WoeUSB/WoeUSB-ng.git
cd WoeUSB-ng
git apply development.patch
sudo pip3 install -e .
```
Please note that this will not create menu shortcut and you may need to run gui twice as it may want to adjust policy. 

### Uninstalling

To remove WoeUSB-ng completely run (needed only when using installation from source code):
```shell
sudo pip3 uninstall WoeUSB-ng
sudo rm /usr/share/icons/WoeUSB-ng/icon.ico \
    /usr/share/applications/WoeUSB-ng.desktop \
    /usr/local/bin/woeusbgui
sudo rmdir /usr/share/icons/WoeUSB-ng/
```

## License
WoeUSB-ng is distributed under the [GPL license](https://github.com/WoeUSB/WoeUSB-ng/blob/master/COPYING).
