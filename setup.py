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
    path = '/usr/local/bin/woeusbgui'  # Assuming default installation path
    shutil.copy2(os.path.join(this_directory, 'WoeUSB/woeusbgui'), path)

    shutil.copy2(os.path.join(this_directory, 'miscellaneous/com.github.woeusb.woeusb-ng.policy'),
                 "/usr/share/polkit-1/actions")

    icons_directory = '/usr/share/icons/WoeUSB-ng'
    os.makedirs(icons_directory, exist_ok=True)
    shutil.copy2(os.path.join(this_directory, 'WoeUSB/data/icon.ico'), os.path.join(icons_directory, 'icon.ico'))

    shutil.copy2(os.path.join(this_directory, 'miscellaneous/WoeUSB-ng.desktop'),
                 "/usr/share/applications/WoeUSB-ng.desktop")

    # Setting permissions
    os.chmod('/usr/share/applications/WoeUSB-ng.desktop',
             stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH | stat.S_IEXEC)  # 755


class PostDevelopCommand(develop):
    """Post-installation for development mode."""

    def run(self):
        post_install()
        develop.run(self)


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self):
        post_install()
        install.run(self)


setup(
    name='WoeUSB-ng',
    version='0.2.12',
    description='WoeUSB-ng is a simple tool that enables you to create your own USB stick Windows installer from an ISO image or a real DVD. This is a rewrite of the original WoeUSB.',
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
