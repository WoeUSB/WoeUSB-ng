# WoeUSB-ng
![brand](https://raw.githubusercontent.com/WoeUSB/WoeUSB-ng/master/WoeUSB/data/woeusb-logo.png)

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

#### Install WoeUSB-ng's Build Dependencies

##### Ubuntu
```shell
sudo apt install git p7zip-full python3-pip python3-wxgtk4.0 
```
##### Arch
```shell
sudo pacman -Suy p7zip python-pip python-wxpython
```

#### Install WoeUSB-ng
```shell
sudo pip3 install WoeUSB-ng
```

#### Installation from source code
```shell
git clone https://github.com/WoeUSB/WoeUSB-ng.git
cd WoeUSB-ng
sudo pip3 install .
```

## License
WoeUSB-ng is distributed under the [GPL license](https://github.com/WoeUSB/WoeUSB-ng/blob/master/COPYING).
