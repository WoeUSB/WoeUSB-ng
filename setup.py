import os
import shutil
import stat
import sys
import sysconfig

from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install

this_directory = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


def get_bin_path() -> str:
    return sysconfig.get_path('scripts')

def get_datarootdir() -> str:
    # Getting datarootdir directly will ignore venv
    return os.path.join(sys.prefix, 'share')

def post_install():
    bin_path = get_bin_path()
    shutil.copy2(this_directory + '/WoeUSB/woeusbgui', os.path.join(bin_path, 'woeusbgui'))

    datarootdir_path = get_datarootdir()

    actions_path = os.path.join(datarootdir_path, "polkit-1/actions")
    os.makedirs(actions_path, exist_ok=True)
    shutil.copy2(this_directory + '/miscellaneous/com.github.woeusb.woeusb-ng.policy', actions_path)

    icons_path = os.path.join(datarootdir_path, 'icons/WoeUSB-ng')
    os.makedirs(icons_path, exist_ok=True)

    icon_path = os.path.join(icons_path, 'icon.ico')
    shutil.copy2(this_directory + '/WoeUSB/data/icon.ico', icon_path)

    applications_path = os.path.join(datarootdir_path, 'applications')
    os.makedirs(applications_path, exist_ok=True)

    desktopfile_path = os.path.join(applications_path, 'WoeUSB-ng.desktop')
    shutil.copy2(this_directory + '/miscellaneous/WoeUSB-ng.desktop', desktopfile_path)

    os.chmod(desktopfile_path,
             stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH | stat.S_IEXEC)  # 755


class PostDevelopCommand(develop):
    """Post-installation for development mode."""

    def run(self):
        # TODO
        develop.run(self)


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self):
        post_install()
        install.run(self)


setup(
    name='WoeUSB-ng',
    version='0.2.12',
    description='WoeUSB-ng is a simple tool that enable you to create your own usb stick windows installer from an iso image or a real DVD. This is a rewrite of original WoeUSB. ',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/WoeUSB/WoeUSB-ng',
    author='Jakub Szymański',
    author_email='jakubmateusz@poczta.onet.pl',
    license='GPL-3',
    zip_safe=False,
    packages=['WoeUSB'],
    include_package_data=True,
    scripts=[
        'WoeUSB/woeusb',
    ],
    install_requires=[
        'termcolor',
        'wxPython',
    ],
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand
    }
)
