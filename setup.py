import os
import shutil
import stat

from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install

this_directory = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


def post_install():
    path = '/usr/local/bin/woeusbgui'  # I give up, I have no clue how to get bin path that is used by pip
    shutil.copy2(this_directory + '/WoeUSB/woeusbgui', path)  # I'll just hard code it until someone finds better way

    shutil.copy2(this_directory + '/miscellaneous/com.github.woeusb.woeusb-ng.policy', "/usr/share/polkit-1/actions")

    try:
        os.makedirs('/usr/share/icons/WoeUSB-ng')
    except FileExistsError:
        pass

    shutil.copy2(this_directory + '/WoeUSB/data/icon.ico', '/usr/share/icons/WoeUSB-ng/icon.ico')
    shutil.copy2(this_directory + '/miscellaneous/WoeUSB-ng.desktop', "/usr/share/applications/WoeUSB-ng.desktop")

    os.chmod('/usr/share/applications/WoeUSB-ng.desktop',
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
    version='0.2.8',
    description='WoeUSB-ng is a simple tool that enable you to create your own usb stick windows installer from an iso image or a real DVD. This is a rewrite of original WoeUSB. ',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='http://github.com/WoeUSB/WoeUSB-ng',
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
