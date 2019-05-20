from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install
from xml.dom.minidom import parse
import shutil
import stat
import os


this_directory = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


def post_install():
    path = '/usr/local/bin/woeusbgui'  # I give up, I have no clue how to get bin path that is used by pip
    shutil.copy2(this_directory + '/WoeUSB/woeusbgui', path)  # I'll just hard code it until someone finds better way

    dom = parse(this_directory + '/miscellaneous/com.github.woeusb.woeusb-ng.policy')
    for action in dom.getElementsByTagName('action'):
        if action.getAttribute('id') == "com.github.slacka.woeusb.run-gui-using-pkexec":
            for annotate in action.getElementsByTagName('annotate'):
                if annotate.getAttribute('key') == "org.freedesktop.policykit.exec.path":
                    annotate.childNodes[0].nodeValue = path

    with open(this_directory + '/miscellaneous/com.github.woeusb.woeusb-ng.policy', "w") as file:
        dom.writexml(file)

    shutil.copy2(this_directory + '/miscellaneous/com.github.woeusb.woeusb-ng.policy', "/usr/share/polkit-1/actions")

    try:
        os.makedirs('/usr/share/icons/WoeUSB-ng')
    except FileExistsError:
        pass

    shutil.copy2(this_directory + '/WoeUSB/data/icon.ico', '/usr/share/icons/WoeUSB-ng/icon.ico')

    with open(this_directory + '/miscellaneous/WoeUSB-ng.desktop', "w") as file:
        file.write(
            """#!/usr/bin/env xdg-open
            [Desktop Entry]
            Name=WoeUSB-ng
            Exec=""" + path + """
            Icon=/usr/share/icons/WoeUSB-ng/icon.ico
            Terminal=false
            Type=Application
            """
        )

    shutil.copy2(this_directory + '/miscellaneous/WoeUSB-ng.desktop', '/usr/share/applications')
    os.chmod('/usr/share/applications/WoeUSB-ng.desktop', stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)  # 644


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
    version='0.1.11',
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
